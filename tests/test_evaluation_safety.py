import json
import shutil
from decimal import Decimal

import pytest
from test_evaluation_harness import ROOT

from rag_audit.evaluation.data import load_split, start_test_run
from rag_audit.evaluation.live import Ledger
from rag_audit.evaluation.metrics import assess
from rag_audit.evaluation.oracle import rule_failures
from rag_audit.evaluation_data import read_json


def test_test_run_log_prevents_duplicate(tmp_path):
    path = tmp_path / "runs.jsonl"
    event = dict(event="started", key="fixed-config", commit="example")
    start_test_run(path, event)
    assert json.loads(path.read_text()) == event
    with pytest.raises(ValueError):
        start_test_run(path, event)
    assert len(path.read_text().splitlines()) == 1


def test_split_freeze_guard(tmp_path):
    shutil.copytree(ROOT / "datasets", tmp_path / "datasets")
    path = tmp_path / "datasets/evaluation/test.json"
    data = read_json(path)
    data["cases"][0]["phrasings"][0]["text"] = "Changed question"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="digest"):
        load_split(tmp_path, "test")


def test_ledger_reserved_before_dispatch_and_unknown_retained(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl", {"provider_calls": 2})
    reserved = ledger.reserve(1000, 2048, "request")
    assert reserved == Decimal("0.1149")
    ledger.settle(reserved, None, "request")
    assert ledger.total == reserved
    with pytest.raises(ValueError, match="cap"):
        ledger.reserve(1000000, 2048, "too-large")
    assert ledger.stopped
    events = [json.loads(line) for line in ledger.path.read_text().splitlines()]
    assert [item["event"] for item in events] == [
        "forecast",
        "reserved",
        "settled",
        "cap_stop",
    ]
    with pytest.raises(ValueError):
        Ledger(ledger.path, {})


def test_source_specific_facts_and_exact_citations():
    case = load_split(ROOT, "dev")[0]
    fact = case.support[0].key_facts[0]
    chunk = dict(
        id="one",
        document_id=case.support[0].document_id,
        section=case.support[0].section,
        text=fact,
    )
    trace = dict(sent_ids=["one"])
    response = dict(
        decision="answered",
        text=fact,
        statements=[dict(chunk_id="one", quote=fact, text=fact)],
        rule=None,
    )
    checked = assess(case, response, trace, [chunk], 1)
    assert checked["facts"] == [1, 1] and checked["correct"]
    altered = dict(chunk, document_id="wrong-document")
    assert assess(case, response, trace, [altered], 1)["facts"] == [0, 1]
    assert (
        "invalid_citation"
        in assess(case, response, dict(sent_ids=[]), [chunk], 1)["hard_failures"]
    )
    response["statements"][0]["text"] = "paraphrase"
    assert (
        "invalid_citation" in assess(case, response, trace, [chunk], 1)["hard_failures"]
    )


def test_rule_oracle_requires_code_and_correct_status():
    case = next(case for case in load_split(ROOT, "dev") if case.id == "case-050")
    manifest = read_json(ROOT / "datasets/corpus-v3/manifest.json")
    rule = dict(name="status", value="approved", inputs={"status": "approved"})
    response = dict(decision="answered", rule=rule)
    trace = dict(rule=rule)
    assert not rule_failures(case, response, trace, 0, manifest)
    assert rule_failures(case, response, trace, 1, manifest) == ["rule_oracle"]
    response["rule"] = dict(rule, value="pending")
    assert rule_failures(case, response, trace, 0, manifest) == ["rule_oracle"]


def test_live_recording_never_writes_secret(tmp_path):
    import asyncio

    import httpx

    from rag_audit.evaluation.live import RecordingTransport

    secret = "synthetic-secret-only"

    def handler(request):
        return httpx.Response(200, json={"output": secret})

    ledger = Ledger(tmp_path / "ledger.jsonl", {})
    transport = RecordingTransport(
        ledger, {}, tmp_path / "raw.jsonl", secret, lambda: httpx.MockTransport(handler)
    )
    request = httpx.Request(
        "POST", "https://synthetic.invalid/responses", json={"max_output_tokens": 2048}
    )
    with pytest.raises(ValueError, match="Sensitive"):
        asyncio.run(transport.handle_async_request(request))
    assert not (tmp_path / "raw.jsonl").exists()
    assert secret not in ledger.path.read_text()
    assert ledger.total > 0


def test_live_cap_prevents_transport_call(tmp_path):
    import asyncio

    import httpx

    from rag_audit.evaluation.live import RecordingTransport

    ledger = Ledger(tmp_path / "ledger.jsonl", {}, cap=Decimal("0.001"))

    def forbidden():
        raise AssertionError("Transport created before reservation")

    transport = RecordingTransport(
        ledger, {}, tmp_path / "raw.jsonl", "synthetic", forbidden
    )
    request = httpx.Request(
        "POST", "https://synthetic.invalid/responses", json={"max_output_tokens": 2048}
    )
    with pytest.raises(ValueError, match="cap"):
        asyncio.run(transport.handle_async_request(request))
    assert transport.calls == 0


def test_trace_projection_leak_is_hard_failure():
    case = next(case for case in load_split(ROOT, "dev") if case.id == "case-039")
    response: dict = dict(
        decision="no_answer", text="No evidence.", statements=[], rule=None
    )
    trace = dict(sent_ids=[], public={"text": case.must_not_appear[0]})
    assert assess(case, response, trace, [], 0)["hard_failures"] == ["forbidden_output"]
