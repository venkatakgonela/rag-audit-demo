import asyncio
import json
from decimal import Decimal

import httpx
import pytest

from rag_audit.evaluation.rate_limit import (
    PacedAttempts,
    delay_after_429,
    resume_rejected_ledger,
)
from rag_audit.evaluation.trial import TrialLedger


def test_delay_honours_header_backoff_and_minimum():
    assert [delay_after_429(None, index) for index in range(3)] == [60, 60, 120]
    assert delay_after_429("180", 0) == 180
    assert delay_after_429("2", 0) == 60


def test_resume_429_retains_hold_and_preserves_original(tmp_path):
    old = tmp_path / "old.jsonl"
    ledger = TrialLedger(old, {})
    hold = ledger.reserve(100, 10, "failed")
    ledger.settle(hold, None, "failed")
    content = old.read_bytes()
    raw = tmp_path / "raw.jsonl"
    raw.write_text(json.dumps(dict(request_hash="failed", http_status=429)) + "\n")
    resumed, counts = resume_rejected_ledger(old, raw, tmp_path / "new.jsonl")
    assert resumed.total == resumed.spent["dev"] == hold
    assert counts["failed"] == 1 and not resumed.stopped
    assert old.read_bytes() == content
    raw.write_text(json.dumps(dict(request_hash="failed", http_status=500)) + "\n")
    with pytest.raises(ValueError, match="only confirmed 429"):
        resume_rejected_ledger(old, raw, tmp_path / "bad.jsonl")


def test_pacing_and_429_only_attempt_limits(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl", {})
    now = [0.0]
    waits = []

    async def sleep(seconds):
        waits.append(seconds)
        now[0] += seconds

    statuses = [429, 200, 500]
    pacing = PacedAttempts(
        ledger,
        tmp_path / "attempts.jsonl",
        factory=lambda: httpx.MockTransport(
            lambda request: httpx.Response(
                statuses.pop(0), headers={"Retry-After": "90"}
            )
        ),
        clock=lambda: now[0],
        sleep=sleep,
    )

    async def run():
        request = httpx.Request("POST", "https://synthetic.invalid", content=b"same")
        await pacing.before()
        transport = pacing.transport()
        assert (await transport.handle_async_request(request)).status_code == 429
        assert pacing.retry()
        await pacing.before()
        assert waits[-1] == 90
        assert (await transport.handle_async_request(request)).status_code == 200
        assert not pacing.retry()
        await pacing.before()
        assert waits[-1] == 5
        assert (await transport.handle_async_request(request)).status_code == 500
        assert not pacing.retry()
        assert pacing.last is not None
        identity = pacing.last[0]
        pacing.last = (identity, 429)
        pacing.attempts[identity] = 4
        assert not pacing.retry()
        pacing.attempts[identity] = 1
        hold = ledger.reserve(50000, 0, "hold")
        assert hold > Decimal("0.60")
        ledger.settle(hold, None, "hold")
        assert not pacing.retry()

    asyncio.run(run())
