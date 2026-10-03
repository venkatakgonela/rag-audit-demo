import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import httpx

from rag_audit.evaluation.data import append_event
from rag_audit.evaluation.live import Ledger, live_provider
from rag_audit.evaluation.record import sanitise
from rag_audit.evaluation_data import digest

CANDIDATES = (0.75, 0.70, 0.65, 0.60)
HISTORICAL_AVERAGE = Decimal("0.28712") / 35


class TrialLedger(Ledger):
    def __init__(self, path, forecast):
        super().__init__(path, {"trial_forecast": forecast}, Decimal("5.00"))
        self.phase = "dev"
        self.spent = {"dev": Decimal(0), "final": Decimal(0)}
        self.limits = {"dev": Decimal("3.50"), "final": Decimal("1.50")}
        self.inflight = None

    @classmethod
    def resume(cls, path: Path):
        events = [json.loads(line) for line in path.read_text().splitlines()]
        if not events or events[0].get("cap") != "5.00":
            raise ValueError("trial_resume: incompatible ledger")
        ledger = cls.__new__(cls)
        ledger.path = path
        ledger.cap = Decimal("5.00")
        ledger.total = Decimal(0)
        ledger.stopped = False
        ledger.phase = "dev"
        ledger.spent = {"dev": Decimal(0), "final": Decimal(0)}
        ledger.limits = {"dev": Decimal("3.50"), "final": Decimal("1.50")}
        ledger.inflight = None
        reservation = Decimal(0)
        seen = set()
        for event in events[1:]:
            if event["event"] == "reserved":
                identity = event["request_hash"]
                if ledger.inflight is not None or identity in seen:
                    raise ValueError(
                        "trial_resume: duplicate or overlapping reservation"
                    )
                seen.add(identity)
                ledger.inflight = identity
                reservation = Decimal(event["amount"])
                ledger.total += reservation
                ledger.spent[ledger.phase] += reservation
            elif event["event"] == "settled":
                if ledger.inflight != event["request_hash"] or event["actual"] is None:
                    raise ValueError("trial_resume: unknown or unmatched settlement")
                actual = Decimal(event["actual"])
                if not 0 <= actual <= reservation:
                    raise ValueError("trial_resume: reservation exceeded")
                ledger.total += actual - reservation
                ledger.spent[ledger.phase] += actual - reservation
                ledger.inflight = None
            elif event["event"] == "phase":
                if (
                    ledger.inflight
                    or ledger.phase != "dev"
                    or event["phase"] != "final"
                ):
                    raise ValueError("trial_resume: invalid phase")
                ledger.phase = "final"
            else:
                raise ValueError("trial_resume: stopped or unknown ledger event")
            if "retained" in event and Decimal(event["retained"]) != ledger.total:
                raise ValueError("trial_resume: retained amount mismatch")
            if (
                ledger.total > ledger.cap
                or ledger.spent[ledger.phase] > ledger.limits[ledger.phase]
            ):
                raise ValueError("trial_resume: cap exceeded")
        if ledger.inflight:
            raise ValueError("trial_resume: unresolved request; no retry")
        return ledger

    def reserve(self, bound, output, request_hash):
        amount = (Decimal(bound) * Decimal("12.5") + Decimal(output) * 50) / 1000000
        if (
            self.inflight is not None
            or self.spent[self.phase] + amount > self.limits[self.phase]
        ):
            self.stopped = True
            append_event(
                self.path,
                dict(event="phase_cap_stop", phase=self.phase, reservation=str(amount)),
            )
            raise ValueError("trial_cap: phase limit prevents dispatch")
        reserved = super().reserve(bound, output, request_hash)
        self.spent[self.phase] += reserved
        self.inflight = request_hash
        return reserved

    def settle(self, reserved, actual, request_hash):
        if self.inflight != request_hash:
            raise ValueError("trial_ledger: mismatched settlement")
        super().settle(reserved, actual, request_hash)
        if actual is not None:
            self.spent[self.phase] += actual - reserved
        else:
            self.stopped = True
        self.inflight = None

    def final_phase(self):
        if self.stopped or self.inflight is not None or self.phase != "dev":
            raise ValueError("trial_ledger: invalid phase transition")
        self.phase = "final"
        append_event(
            self.path, dict(event="phase", phase="final", settled=str(self.total))
        )


class RequestRegistry(httpx.AsyncBaseTransport):
    def __init__(self, output: Path, ledger=None, recorder=None, reported_model=None):
        self.output = output
        self.ledger = ledger or SimpleNamespace(stopped=False)
        self.recorder = recorder
        self.reported_model = reported_model
        self.bodies: dict[str, bytes] = {}
        self.responses: dict[str, tuple[int, dict]] = {}
        self.calls = 0
        self.context = "unbound"
        self.consumers: list[dict] = []
        self.expected: set[str] | None = None
        self.failures: list[str] = []

    def restore_cache(self, path: Path, body_builder=None):
        if self.bodies or self.responses:
            raise ValueError("cache_restore: fresh registry required")
        for line in path.read_text().splitlines():
            entry = json.loads(line)
            body = json.dumps(
                entry["body"], ensure_ascii=False, separators=(",", ":")
            ).encode()
            if body_builder is not None:
                body = body_builder(entry["body"])
                if json.loads(body) != entry["body"]:
                    raise ValueError("cache_restore: reconstructed request differs")
            identity = hashlib.sha256(body).hexdigest()
            if identity != entry["request_hash"] or identity in self.bodies:
                raise ValueError("cache_restore: identity mismatch or duplicate")
            self.bodies[identity] = body
            self.responses[identity] = (entry["status"], entry["response"])

    def bind(self, case, style, side):
        self.context = f"{case}/{style}/{side}"

    async def handle_async_request(self, request):
        body = await request.aread()
        identity = hashlib.sha256(body).hexdigest()
        if identity in self.bodies and self.bodies[identity] != body:
            raise ValueError("request_identity: body collision")
        if self.expected is not None and identity not in self.expected:
            self.ledger.stopped = True
            self.failures.append("unforecast_request")
            raise ValueError("request_identity: unforecast request")
        self.calls += 1
        self.bodies[identity] = body
        reused = identity in self.responses
        self.consumers.append(
            dict(context=self.context, request_hash=identity, reused=reused)
        )
        if not reused:
            if self.recorder is None:
                payload = dict(
                    model=self.reported_model or json.loads(body)["model"],
                    status="completed",
                    output=[
                        dict(
                            type="message",
                            role="assistant",
                            status="completed",
                            content=[
                                dict(
                                    type="output_text",
                                    text='{"outcome":"insufficient_evidence","statements":[]}',
                                )
                            ],
                        )
                    ],
                    usage=dict(
                        input_tokens=10,
                        output_tokens=10,
                        total_tokens=20,
                        input_tokens_details=dict(
                            cached_tokens=0, cache_write_tokens=0
                        ),
                        output_tokens_details=dict(reasoning_tokens=0),
                    ),
                )
                response = httpx.Response(200, json=payload)
            else:
                try:
                    response = await self.recorder.handle_async_request(request)
                except Exception:
                    self.ledger.stopped = True
                    raise
            self.responses[identity] = (response.status_code, response.json())
            if self.recorder is not None:
                append_event(
                    self.output / "cache.jsonl",
                    dict(
                        request_hash=identity,
                        body=json.loads(body),
                        status=response.status_code,
                        response=response.json(),
                    ),
                )
        status, payload = self.responses[identity]
        return httpx.Response(status, json=payload)

    def forecast(self):
        reservations = {
            identity: str(
                (
                    Decimal(len(body) + 1024) * Decimal("12.5")
                    + Decimal(json.loads(body)["max_output_tokens"]) * 50
                )
                / 1000000
            )
            for identity, body in self.bodies.items()
        }
        return dict(
            unique=len(reservations),
            logical=self.calls,
            conservative_total=str(
                sum(map(Decimal, reservations.values()), Decimal(0))
            ),
            expected_historical_average=str(HISTORICAL_AVERAGE * len(reservations)),
            reservations=reservations,
        )

    def fixture_candidates(self, consumers):
        entries = []
        for identity in dict.fromkeys(row["request_hash"] for row in consumers):
            status, payload = self.responses[identity]
            entry = sanitise(self.bodies[identity], payload, status)
            entry["consumers"] = [
                row["context"] for row in consumers if row["request_hash"] == identity
            ]
            if len(entry["consumers"]) != len(set(entry["consumers"])):
                raise ValueError("fixture_consumer: duplicate consumer")
            entry["expected_consumptions"] = len(entry["consumers"])
            entries.append(entry)
        return entries


def cached_live(settings, ledger, directory):
    adapter, prices, recorder = live_provider(
        settings, ledger, directory / "raw-output.jsonl"
    )
    registry = RequestRegistry(directory, ledger, recorder)
    return replace(adapter, transport=registry), prices, registry


def candidate_summary(threshold, rows):
    if any(row["split"] != "dev" for row in rows):
        raise ValueError("selection: dev only")
    complete = (
        len(rows) == 84 and len({(row["case"], row["style"]) for row in rows}) == 84
    )
    hard = sum(len(row["hard_failures"]) for row in rows)
    errors = sum(row["response"]["decision"] == "error" for row in rows)
    false = {
        kind: sum(
            row["assessment"]["false_answer"]
            for row in rows
            if row["challenge_kind"] == kind
        )
        for kind in ("off_domain", "id_lookup", "free_text", "near_miss")
    }
    correct = {
        style: sum(
            row["assessment"]["correct"]
            for row in rows
            if row["style"] == style and row["category"] in ("single", "multi")
        )
        for style in ("keyword", "natural")
    }
    return dict(
        threshold=threshold,
        complete=complete,
        hard=hard,
        errors=errors,
        false_answers=false,
        correct=correct,
        eligible=complete
        and not hard
        and not errors
        and not any(false[kind] for kind in ("off_domain", "id_lookup", "free_text")),
    )


def choose_candidate(table):
    if tuple(row["threshold"] for row in table) != CANDIDATES or not all(
        row["complete"] and not row["errors"] for row in table
    ):
        raise ValueError("selection: complete declared grid required")
    eligible = [row for row in table if row["eligible"]]
    if not eligible:
        return dict(selected=None, adopt=False)
    selected = max(
        eligible,
        key=lambda row: (
            row["correct"]["natural"],
            row["correct"]["keyword"],
            -row["false_answers"]["near_miss"],
            row["threshold"],
        ),
    )
    return dict(
        selected=selected["threshold"],
        adopt=selected["correct"]["natural"] >= 8
        and selected["false_answers"]["near_miss"] <= 1,
        table_digest=digest(table),
    )
