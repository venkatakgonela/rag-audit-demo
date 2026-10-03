import asyncio
import copy
import json
from decimal import Decimal

import httpx
import pytest

from rag_audit.evaluation.trial import (
    CANDIDATES,
    RequestRegistry,
    TrialLedger,
    choose_candidate,
)


def request(text="synthetic", output=20):
    return httpx.Request(
        "POST",
        "https://synthetic.invalid",
        json=dict(model="synthetic", input=text, max_output_tokens=output),
    )


def test_trial_registry_reuses_identical_bytes_and_preserves_different_requests(
    tmp_path,
):
    registry = RequestRegistry(tmp_path)
    registry.bind("case", "natural", "primary")
    first = asyncio.run(registry.handle_async_request(request()))
    registry.bind("case", "natural", "paired")
    second = asyncio.run(registry.handle_async_request(request()))
    assert first.content == second.content
    assert registry.calls == 2 and len(registry.responses) == 1
    assert registry.consumers[1]["reused"]
    registry.bind("case", "keyword", "paired")
    asyncio.run(registry.handle_async_request(request("hidden-dependent")))
    assert (
        registry.consumers[0]["request_hash"] != registry.consumers[2]["request_hash"]
    )
    assert len(registry.responses) == 2


def test_forecast_miss_stops_before_dispatch(tmp_path):
    registry = RequestRegistry(tmp_path)
    registry.expected = set()
    with pytest.raises(ValueError, match="unforecast"):
        asyncio.run(registry.handle_async_request(request()))
    assert registry.ledger.stopped and registry.calls == 0


def test_shared_ledger_phase_limits_unknown_usage_and_one_settlement(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl", {})
    hold = ledger.reserve(100, 10, "first")
    ledger.settle(hold, Decimal("0.0001"), "first")
    assert ledger.total == ledger.spent["dev"] == Decimal("0.0001")
    ledger.final_phase()
    hold = ledger.reserve(100, 10, "second")
    ledger.settle(hold, None, "second")
    assert ledger.stopped and ledger.total == Decimal("0.0001") + hold
    with pytest.raises(ValueError, match="settlement"):
        ledger.settle(hold, None, "second")
    with pytest.raises(ValueError):
        ledger.reserve(100, 10, "third")
    with pytest.raises(ValueError):
        TrialLedger(tmp_path / "ledger.jsonl", {})


@pytest.mark.parametrize("phase,limit", [("dev", "3.50"), ("final", "1.50")])
def test_phase_cap_binds_before_total_cap(tmp_path, phase, limit):
    ledger = TrialLedger(tmp_path / "ledger.jsonl", {})
    ledger.phase = phase
    ledger.spent[phase] = Decimal(limit)
    with pytest.raises(ValueError, match="phase limit"):
        ledger.reserve(1, 1, "request")
    assert not any(
        json.loads(line)["event"] == "reserved"
        for line in ledger.path.read_text().splitlines()
    )


def test_resume_keeps_spend_and_refuses_unknown_or_pending(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = TrialLedger(path, {})
    hold = ledger.reserve(100, 10, "first")
    with pytest.raises(ValueError, match="unresolved"):
        TrialLedger.resume(path)
    ledger.settle(hold, Decimal("0.0001"), "first")
    resumed = TrialLedger.resume(path)
    assert resumed.total == resumed.spent["dev"] == Decimal("0.0001")
    resumed.final_phase()
    hold = resumed.reserve(100, 10, "second")
    resumed.settle(hold, Decimal("0.0002"), "second")
    again = TrialLedger.resume(path)
    assert again.total == Decimal("0.0003")
    assert again.spent["final"] == Decimal("0.0002")
    assert again.phase == "final"
    text = path.read_text()
    path.write_text(text.replace('"actual": "0.0002"', '"actual": null'))
    with pytest.raises(ValueError, match="unknown"):
        TrialLedger.resume(path)


def table():
    return [
        dict(
            threshold=value,
            complete=True,
            errors=0,
            hard=0,
            eligible=True,
            correct=dict(natural=8, keyword=10),
            false_answers=dict(near_miss=1),
        )
        for value in CANDIDATES
    ]


def test_selection_ties_and_adoption_boundaries():
    candidates = table()
    assert choose_candidate(candidates)["selected"] == 0.75
    candidates[1]["correct"]["keyword"] = 11
    assert choose_candidate(candidates)["selected"] == 0.70
    candidates[2]["correct"]["natural"] = 9
    assert choose_candidate(candidates)["selected"] == 0.65
    candidates[2]["false_answers"]["near_miss"] = 2
    assert not choose_candidate(candidates)["adopt"]
    candidates = table()
    for row in candidates:
        row["correct"]["natural"] = 7
    assert not choose_candidate(candidates)["adopt"]
    for row in candidates:
        row["eligible"] = False
    assert choose_candidate(candidates)["selected"] is None
    broken = copy.deepcopy(candidates)
    broken[0]["complete"] = False
    with pytest.raises(ValueError, match="complete declared grid"):
        choose_candidate(broken)
