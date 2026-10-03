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


def test_resume_rejected_then_successful_same_request(tmp_path):
    old = tmp_path / "old.jsonl"
    ledger = TrialLedger(old, {})
    hold = ledger.reserve(100, 10, "same")
    ledger.settle(hold, None, "same")
    ledger.stopped = False
    second = ledger.reserve(100, 10, "same")
    ledger.settle(second, Decimal("0.0001"), "same")
    raw = tmp_path / "raw.jsonl"
    raw.write_text(
        "".join(
            json.dumps(dict(request_hash="same", http_status=status)) + "\n"
            for status in (429, 200)
        )
    )
    resumed, attempts = resume_rejected_ledger(old, raw, tmp_path / "new.jsonl")
    assert attempts["same"] == 2
    assert resumed.total == hold + Decimal("0.0001")
    resumed.final_phase()
    assert resumed.spent["final"] == 0
    assert resumed.spent["dev"] == resumed.total
    raw.write_text(
        raw.read_text() + json.dumps(dict(request_hash="extra", http_status=200)) + "\n"
    )
    with pytest.raises(ValueError, match="extra response"):
        resume_rejected_ledger(old, raw, tmp_path / "bad.jsonl")
    assert not (tmp_path / "bad.jsonl").exists()


@pytest.mark.parametrize("status", [200, 429, 500])
def test_runner_retries_only_rejected_attempts(tmp_path, monkeypatch, status):
    from types import SimpleNamespace

    from rag_audit.evaluation import runner

    ledger = TrialLedger(tmp_path / "ledger.jsonl", {})
    now = [0.0]

    async def sleep(seconds):
        now[0] += seconds

    pacing = PacedAttempts(
        ledger, tmp_path / "attempts.jsonl", clock=lambda: now[0], sleep=sleep
    )
    calls = []

    async def phrasing(*args, **kwargs):
        calls.append(now[0])
        pacing.attempts["same"] += 1
        pacing.last = ("same", status)
        pacing.ready = now[0] + 60
        held = ledger.reserve(100, 10, "same")
        ledger.settle(held, None, "same")
        return {"response": {"decision": "error"}}

    monkeypatch.setattr(runner, "_run_phrasing", phrasing)
    asyncio.run(
        runner.run_phrasing(
            live=(None, None, SimpleNamespace(ledger=ledger, pacing=pacing))
        )
    )
    assert len(calls) == (4 if status == 429 else 1)
    assert ledger.stopped
    if status == 429:
        assert calls == [0, 60, 120, 180]


@pytest.mark.parametrize("status", [429, 500])
def test_rejected_response_never_settles_even_with_usage(tmp_path, status):
    from rag_audit.evaluation.live import RecordingTransport

    ledger = TrialLedger(tmp_path / "ledger.jsonl", {})
    recorder = RecordingTransport(
        ledger,
        {},
        tmp_path / "raw.jsonl",
        "synthetic-secret",
        transport_factory=lambda: httpx.MockTransport(
            lambda request: httpx.Response(
                status, json={"usage": {"input_tokens": 1, "output_tokens": 1}}
            )
        ),
    )
    request = httpx.Request(
        "POST", "https://synthetic.invalid", json={"max_output_tokens": 10}
    )
    with pytest.raises(ValueError, match="rejected request"):
        asyncio.run(recorder.handle_async_request(request))
    assert ledger.stopped and ledger.total > 0
    assert json.loads(ledger.path.read_text().splitlines()[-1])["actual"] is None
