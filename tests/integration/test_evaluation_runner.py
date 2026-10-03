import asyncio

import pytest
from test_answer_database import database as database
from test_evaluation_harness import ROOT
from test_reranking import FixedReranker

from rag_audit.embeddings import FakeEmbedder
from rag_audit.evaluation import runner
from rag_audit.evaluation.data import load_split
from rag_audit.evaluation.metrics import assess
from rag_audit.evaluation.oracle import rule_failures
from rag_audit.evaluation.runner import run_cases, run_phrasing
from rag_audit.evaluation_data import read_json
from rag_audit.gate import Gate

pytestmark = pytest.mark.integration


def test_counterfactual_detects_changed_bytes_and_global_signal(database, monkeypatch):
    connection, _ = database
    case = next(
        case for case in load_split(ROOT, "dev") if case.challenge_kind == "free_text"
    )
    original = runner.run_phrasing
    calls = 0

    async def changed(*args, **kwargs):
        nonlocal calls
        calls += 1
        row = await original(*args, **kwargs)
        if calls % 2 == 0:
            row["response_bytes"] += " "
            row["chunks"][0]["synthetic_global_count"] = 1
        return row

    monkeypatch.setattr(runner, "run_phrasing", changed)
    rows = run_cases(connection, FakeEmbedder(), [case], None)
    for row in rows:
        assert "counterfactual_bytes" in row["hard_failures"]
        assert "counterfactual_signals" in row["hard_failures"]


def test_reranker_hidden_removal_invariance(database):
    connection, _ = database
    cases = [
        case for case in load_split(ROOT, "dev") if case.challenge_kind == "free_text"
    ]
    rows = run_cases(
        connection, FakeEmbedder(), cases, Gate("V4a", 0.5), reranker=FixedReranker()
    )
    assert len(rows) == 10
    for row in rows:
        assert row["trace"]["reranker_scores"]
        assert (
            row["trace"]["reranker_scores"]
            == row["counterfactual"]["trace"]["reranker_scores"]
        )
        assert not row["hard_failures"]


def test_real_pipeline_dev_and_counterfactual(database):
    connection, _ = database
    cases = load_split(ROOT, "dev")
    cases = [
        case
        for case in cases
        if case.id in ("case-001", "case-039", "case-050", "case-061")
    ]
    rows = run_cases(connection, FakeEmbedder(), cases, Gate("V1", 0.15))
    assert len(rows) == 8
    manifest = read_json(ROOT / "datasets/corpus-v3/manifest.json")
    for row in rows:
        case = next(case for case in cases if case.id == row["case"])
        assert not row["hard_failures"]
        assert not rule_failures(
            case, row["response"], row["trace"], row["assessment"]["calls"], manifest
        )
    assert any(row["attack_retrieved"] for row in rows)
    assert len(connection.execute("SELECT payload FROM demo_traces").fetchall()) == 10


def test_metric_detects_planted_leak_and_citation(database):
    connection, _ = database
    case = next(case for case in load_split(ROOT, "dev") if case.id == "case-039")
    row = asyncio.run(
        run_phrasing(
            connection, FakeEmbedder(), case, "keyword", case.phrasings[0].text, Gate()
        )
    )
    response = dict(row["response"], text=case.must_not_appear[0])
    assert (
        "forbidden_output"
        in assess(case, response, row["trace"], row["chunks"], 0)["hard_failures"]
    )
    response = dict(
        row["response"],
        decision="answered",
        statements=[dict(chunk_id="invented", text="quote", quote="quote")],
    )
    assert (
        "invalid_citation"
        in assess(case, response, row["trace"], row["chunks"], 0)["hard_failures"]
    )
