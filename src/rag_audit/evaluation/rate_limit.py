import asyncio
import hashlib
import json
import time
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime

import httpx

from rag_audit.evaluation.data import append_event
from rag_audit.evaluation.trial import TrialLedger


def delay_after_429(value, retry):
    delay: float = (30, 60, 120)[min(retry, 2)]
    if value:
        try:
            delay = max(0, float(value))
        except ValueError:
            delay = max(
                0, (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
            )
    return max(60, delay)


class PacedAttempts:
    def __init__(
        self,
        ledger,
        path,
        attempts=None,
        factory=None,
        clock=time.monotonic,
        sleep=asyncio.sleep,
    ):
        self.ledger = ledger
        self.path = path
        self.attempts = Counter(attempts or {})
        self.factory = factory or (lambda: httpx.AsyncHTTPTransport(retries=0))
        self.clock = clock
        self.sleep = sleep
        self.ready = clock() + (60 if attempts else 0)
        self.last = None

    async def before(self):
        await self.sleep(max(0, self.ready - self.clock()))
        self.last = None

    def transport(self):
        owner = self

        class Observed(httpx.AsyncBaseTransport):
            def __init__(self):
                self.inner = owner.factory()

            async def handle_async_request(self, request):
                identity = hashlib.sha256(await request.aread()).hexdigest()
                if owner.clock() < owner.ready or owner.attempts[identity] >= 4:
                    raise ValueError("retry_policy: pacing or attempt limit")
                owner.attempts[identity] += 1
                owner.ready = owner.clock() + 5
                append_event(
                    owner.path,
                    dict(
                        event="dispatch",
                        request_hash=identity,
                        attempt=owner.attempts[identity],
                    ),
                )
                response = await self.inner.handle_async_request(request)
                owner.last = (identity, response.status_code)
                append_event(
                    owner.path,
                    dict(
                        event="http_status",
                        request_hash=identity,
                        status=response.status_code,
                        retry_after=response.headers.get("Retry-After"),
                    ),
                )
                if response.status_code == 429:
                    owner.ready = owner.clock() + delay_after_429(
                        response.headers.get("Retry-After"),
                        owner.attempts[identity] - 1,
                    )
                return response

            async def aclose(self):
                await self.inner.aclose()

        return Observed()

    def retry(self):
        if self.last is None or self.last[1] != 429:
            return False
        identity = self.last[0]
        events = [
            json.loads(line) for line in self.ledger.path.read_text().splitlines()
        ]
        holds = Decimal(0)
        pending = None
        for event in events:
            if event["event"] == "reserved":
                pending = Decimal(event["amount"])
            elif event["event"] == "settled" and event["actual"] is None:
                if pending is None:
                    raise ValueError("retry_policy: unmatched hold")
                holds += pending
        if holds > Decimal("0.60") or self.attempts[identity] >= 4:
            return False
        self.ledger.stopped = False
        return True


def resume_rejected_ledger(old_path, raw_path, new_path):
    if new_path.exists():
        raise ValueError("retry_resume: preserve previous continuation")
    events = [json.loads(line) for line in old_path.read_text().splitlines()]
    responses = [json.loads(line) for line in raw_path.read_text().splitlines()]
    statuses = {}
    for row in responses:
        identity = row["request_hash"]
        if identity in statuses:
            raise ValueError("retry_resume: duplicate original request")
        statuses[identity] = row["http_status"]
    ledger = TrialLedger.__new__(TrialLedger)
    ledger.path = new_path
    ledger.cap = Decimal("5.00")
    ledger.total = Decimal(0)
    ledger.stopped = False
    ledger.phase = "dev"
    ledger.spent = {"dev": Decimal(0), "final": Decimal(0)}
    ledger.limits = {"dev": Decimal("3.50"), "final": Decimal("1.50")}
    ledger.inflight = None
    holds = Decimal(0)
    seen = set()
    if events[0].get("cap") != "5.00":
        raise ValueError("retry_resume: incompatible cap")
    for event in events[1:]:
        identity = event.get("request_hash")
        if event["event"] == "reserved":
            if ledger.inflight or identity in seen:
                raise ValueError("retry_resume: ambiguous reservation")
            seen.add(identity)
            ledger.inflight = identity
            reserved = Decimal(event["amount"])
            ledger.total += reserved
        elif event["event"] == "settled":
            if ledger.inflight != identity:
                raise ValueError("retry_resume: unmatched settlement")
            if event["actual"] is None:
                if statuses.get(identity) != 429:
                    raise ValueError("retry_resume: only confirmed 429 allowed")
                holds += reserved
            else:
                actual = Decimal(event["actual"])
                if statuses.get(identity) != 200 or not 0 <= actual <= reserved:
                    raise ValueError("retry_resume: invalid known settlement")
                ledger.total += actual - reserved
            ledger.inflight = None
        else:
            raise ValueError("retry_resume: unexpected event")
        if Decimal(event["retained"]) != ledger.total:
            raise ValueError("retry_resume: retained mismatch")
    if (
        ledger.inflight
        or holds > Decimal("0.60")
        or ledger.total > ledger.limits["dev"]
    ):
        raise ValueError("retry_resume: unresolved or over limit")
    ledger.spent["dev"] = ledger.total
    new_path.write_bytes(old_path.read_bytes())
    return ledger, Counter({identity: 1 for identity in seen})
