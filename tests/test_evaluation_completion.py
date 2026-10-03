import asyncio
import copy
import json
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import httpx
import pytest

from rag_audit.accounting import Price
from rag_audit.evaluation.live import Ledger, RecordingTransport
from rag_audit.evaluation.metrics import assess
from rag_audit.evaluation.reporting import deterministic_metrics, report
from rag_audit.evaluation.validation import outcome, validate_forecast
from rag_audit.evaluation_data import Case
from rag_audit.policy import envelope


def example():
    case = SimpleNamespace(
        must_not_appear=[],
        forbidden_documents=[],
        forbidden_sentinels=[],
        forbidden_chunks={},
        category="multi",
        support=[
            SimpleNamespace(document_id="first", section="Facts", key_facts=["blue"]),
            SimpleNamespace(document_id="second", section="Facts", key_facts=["green"]),
        ],
        acceptable_decisions=["answered"],
    )
    chunks = [
        dict(id="irrelevant", document_id="other", section="Facts", text="red"),
        dict(id="first", document_id="first", section="Facts", text="blue"),
        dict(id="second", document_id="second", section="Facts", text="green"),
    ]
    response = envelope(
        "answered", "blue", [dict(chunk_id="first", text="blue", quote="blue")]
    )
    trace = dict(
        sent_ids=["first", "second"],
        durations={"total": 1},
        gate_duration=0.1,
        verification_reason=None,
        reason="citations_verified",
        usage=dict(input=2, output=3),
        cost_usd="0",
    )
    assessment = assess(cast(Case, case), response, trace, chunks, 1)
    return dict(
        case="example",
        style="keyword",
        category="multi",
        split="dev",
        challenge_kind="none",
        response=response,
        trace=trace,
        assessment=assessment,
        hard_failures=assessment["hard_failures"],
    )


def test_metric_hand_audit_and_stable_report():
    row = example()
    assert row["assessment"]["recall"] == {"5": [2, 2], "10": [2, 2]}
    assert row["assessment"]["reciprocal_rank"] == 0.5
    assert row["assessment"]["facts"] == [1, 2]
    assert row["assessment"]["answered_wrong"]
    first = report([row])
    assert first["groups"]["all"]["fact_coverage"]["value"] == 0.5
    assert first["groups"]["all"]["all_facts_covered"]["value"] == 0
    assert not first["cases"]["example"]
    row["trace"]["durations"]["total"] = 100
    assert deterministic_metrics(report([row])) == deterministic_metrics(first)


def test_released_instruction_echo_is_hard_failure():
    from test_evaluation_harness import ROOT

    from rag_audit.evaluation.data import load_split

    case = load_split(ROOT, "dev")[0]
    response = envelope("answered", "ignore previous instructions")
    assert (
        "instruction_echo"
        in assess(case, response, dict(sent_ids=[]), [], 1)["hard_failures"]
    )


def test_partial_results_do_not_count_missing_as_abstention():
    row = example()
    cases = [
        SimpleNamespace(
            id="example",
            phrasings=[
                SimpleNamespace(style="keyword"),
                SimpleNamespace(style="natural"),
            ],
        )
    ]
    result = outcome([row], cases)
    assert result["status"] == "partial" and result["failed"]
    assert result["coverage"] == dict(
        expected=2, attempted=1, not_run=1, missing=[["example", "natural"]]
    )


def test_hard_failure_forces_failed_outcome():
    row = example()
    cases = [
        SimpleNamespace(id="example", phrasings=[SimpleNamespace(style="keyword")])
    ]
    row["hard_failures"] = ["forbidden_output"]
    assert outcome([row], cases)["failed"]
    assert outcome([row], cases)["status"] == "failed"


def test_forecast_requires_same_freeze_policy_settings_commit_and_coverage():
    config: dict = dict(
        generator="sentence-overlap-v1",
        freeze="fixed",
        embedder="real",
        gate=None,
        profile="fixed",
        effective_gate="V1",
        settings={},
        split="all",
    )
    baseline = dict(
        commit="frozen", status="complete", config=config, rows=[dict(hard_failures=[])]
    )
    validate_forecast(baseline, config, "frozen", 1)
    for field in (
        "freeze",
        "embedder",
        "gate",
        "profile",
        "effective_gate",
        "settings",
        "split",
    ):
        altered = copy.deepcopy(config)
        altered[field] = "changed"
        with pytest.raises(ValueError):
            validate_forecast(baseline, altered, "frozen", 1)
    with pytest.raises(ValueError):
        validate_forecast(baseline, config, "changed", 1)
    with pytest.raises(ValueError):
        validate_forecast(baseline, config, "frozen", 2)


def test_live_recording_settles_and_preserves_model_once(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl", {})
    body = dict(
        model="synthetic-model",
        status="completed",
        output=[],
        usage=dict(
            input_tokens=100,
            output_tokens=10,
            total_tokens=110,
            input_tokens_details=dict(cached_tokens=0, cache_write_tokens=0),
            output_tokens_details=dict(reasoning_tokens=0),
        ),
    )

    def handler(request):
        assert ledger.total > 0
        assert (
            json.loads(ledger.path.read_text().splitlines()[-1])["event"] == "reserved"
        )
        return httpx.Response(200, json=body)

    price = Price(
        "synthetic",
        Decimal(10),
        Decimal(50),
        Decimal(1),
        Decimal(50),
        "provider_tokens",
        Decimal("12.5"),
    )
    output = tmp_path / "raw.jsonl"
    transport = RecordingTransport(
        ledger,
        {"synthetic-model": price},
        output,
        "synthetic-secret",
        lambda: httpx.MockTransport(handler),
    )
    request = httpx.Request(
        "POST", "https://synthetic.invalid/responses", json={"max_output_tokens": 2048}
    )
    response = asyncio.run(transport.handle_async_request(request))
    assert response.status_code == 200
    assert ledger.total == Decimal("0.0015")
    recorded = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(recorded) == 1
    assert recorded[0]["reported_model"] == "synthetic-model"
    assert recorded[0]["usage"] == body["usage"]
