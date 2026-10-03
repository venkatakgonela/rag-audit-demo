import copy
import json
import os
from pathlib import Path

import pytest

from rag_audit.evaluation.ci_gate import expected_rows, integrity, protected
from rag_audit.evaluation.data import load_split
from rag_audit.evaluation.gate_checks import check_rows
from rag_audit.evaluation.metrics import assess
from rag_audit.evaluation.oracle import rule_failures
from rag_audit.evaluation.regression import active_live_baseline, evaluate
from rag_audit.evaluation.replay import fixture_entries
from rag_audit.evaluation.reporting import deterministic_metrics
from rag_audit.evaluation_data import read_json

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def replay_result():
    directory = os.environ.get("SYNTHETIC_MODEL_DIRECTORY")
    if not directory:
        pytest.skip("Full replay self-test requires explicit cached model directory")
    before = protected(ROOT)
    result = evaluate(ROOT, Path(directory))
    assert protected(ROOT) == before
    baseline = read_json(ROOT / "datasets/evaluation/baselines/ci-v1.json")
    policy = read_json(ROOT / "datasets/evaluation/gate-policy.json")
    return result, baseline, policy


def checks_for(rows, fixture, failures=None):
    _, baseline, policy = fixture
    return check_rows(rows, baseline, policy, expected_rows(ROOT), failures or [])


def control(fixture):
    result, baseline, _ = fixture
    integrity(ROOT, baseline)
    assert all(check["passed"] for check in checks_for(result["rows"], fixture))


def test_current_pipeline_exact_replay_identity_and_live_equality(replay_result):
    control(replay_result)
    result = replay_result[0]
    entries = fixture_entries(ROOT / "datasets/evaluation/replay")
    assert sorted(result["consumed"]) == sorted(
        entry["request_hash"]
        for entry in entries
        for _ in range(entry.get("expected_consumptions", 1))
    )
    assert not result["replay_failures"]
    live = active_live_baseline(ROOT)
    assert deterministic_metrics(result["metrics"]) == deterministic_metrics(
        live["metrics"]
    )


@pytest.mark.parametrize(
    "fault", ["leak", "citation", "quote", "rule", "bytes", "echo", "incomplete"]
)
def test_gate_faults_have_passing_controls(replay_result, fault):
    control(replay_result)
    rows = copy.deepcopy(replay_result[0]["rows"])
    cases = {
        case.id: case for split in ("dev", "test") for case in load_split(ROOT, split)
    }
    if fault == "incomplete":
        rows.pop()
        expected = "complete"
    elif fault == "rule":
        row = next(row for row in rows if row["category"] == "rules")
        row["response"]["rule"]["value"] = "999999"
        row["hard_failures"].extend(
            rule_failures(
                cases[row["case"]],
                row["response"],
                row["trace"],
                0,
                read_json(ROOT / "datasets/corpus-v3/manifest.json"),
            )
        )
        expected = "hard:rule_oracle"
    elif fault == "bytes":
        row = next(row for row in rows if "counterfactual" in row)
        row["response_bytes"] += "changed"
        if row["response_bytes"] != row["counterfactual"]["response_bytes"]:
            row["hard_failures"].append("counterfactual_bytes")
        expected = "hard:counterfactual_bytes"
    else:
        row = next(
            row
            for row in rows
            if (
                row["category"] == "unauthorised"
                if fault == "leak"
                else bool(row["response"]["statements"])
            )
        )
        if fault == "leak":
            row["response"]["text"] = cases[row["case"]].must_not_appear[0]
            expected = "hard:forbidden_output"
        elif fault == "echo":
            row["response"]["text"] = "ignore previous instructions"
            expected = "hard:instruction_echo"
        elif fault == "citation":
            row["response"]["statements"][0]["chunk_id"] = "outside-sent"
            expected = "hard:invalid_citation"
        else:
            row["response"]["statements"][0]["quote"] = "not in source"
            expected = "hard:invalid_citation"
        row["hard_failures"] = assess(
            cases[row["case"]],
            row["response"],
            row["trace"],
            row["chunks"],
            row["assessment"]["calls"],
        )["hard_failures"]
    failed = {
        check["check"]
        for check in checks_for(rows, replay_result)
        if not check["passed"]
    }
    assert expected in failed


def test_gate_lowered_threshold_measured_false_evidence(replay_result):
    control(replay_result)
    from rag_audit.embeddings import OnnxEmbedder
    from rag_audit.gate import Gate
    from rag_audit.policy import select_evidence
    from rag_audit.settings import Settings

    rows = copy.deepcopy(replay_result[0]["rows"])
    for row in rows:
        if row["category"] != "rules":
            selected, _ = select_evidence(
                row["chunks"],
                OnnxEmbedder.identity,
                Settings(),
                gate=Gate("V1", 0.55),
                question=row["trace"]["question"],
            )
            row["trace"]["sent_ids"] = [chunk["id"] for chunk in selected]
    failed = {
        check["check"]
        for check in checks_for(rows, replay_result)
        if not check["passed"]
    }
    assert any("false_evidence" in name for name in failed)


def test_gate_integrity_controls(replay_result, tmp_path):
    control(replay_result)
    baseline = copy.deepcopy(replay_result[1])
    baseline["measures"]["dev/natural/evidence_sufficient"] += 1
    with pytest.raises(ValueError, match="baseline_log"):
        integrity(ROOT, baseline)
    baseline = copy.deepcopy(replay_result[1])
    baseline["config_digest"] = "tampered"
    with pytest.raises(ValueError, match="baseline_config"):
        integrity(ROOT, baseline)
    directory = ROOT / "datasets/evaluation/replay"
    (tmp_path / "manifest.json").write_bytes((directory / "manifest.json").read_bytes())
    entries = json.loads((directory / "responses.json").read_text())
    for changed in (entries[:-1], [dict(entries[0], response={}), *entries[1:]]):
        (tmp_path / "responses.json").write_text(json.dumps(changed))
        with pytest.raises(ValueError, match="fixture_digest"):
            fixture_entries(tmp_path)


def test_gate_soft_regression_and_infinite_tolerance(replay_result):
    control(replay_result)
    rows = copy.deepcopy(replay_result[0]["rows"])
    for row in rows:
        row["trace"]["sent_ids"] = []
        row["assessment"]["correct"] = False
    assert any(
        not check["passed"] and "evidence_sufficient" in check["check"]
        for check in checks_for(rows, replay_result)
    )
    policy = dict(replay_result[2], count_tolerance=float("inf"))
    with pytest.raises(ValueError, match="gate_policy"):
        check_rows(rows, replay_result[1], policy, expected_rows(ROOT), [])


def test_gate_actual_fake_embedder_swap(replay_result, monkeypatch):
    from rag_audit.embeddings import FakeEmbedder
    from rag_audit.evaluation import regression

    control(replay_result)
    monkeypatch.setattr(regression, "OnnxEmbedder", lambda directory: FakeEmbedder())
    result = regression.evaluate(ROOT, Path(os.environ["SYNTHETIC_MODEL_DIRECTORY"]))
    failed = {
        check["check"]
        for check in checks_for(
            result["rows"], replay_result, result["replay_failures"]
        )
        if not check["passed"]
    }
    assert "dev/natural/evidence_sufficient" in failed
    assert "dev/recall_hits" in failed or "dev/mrr_sum" in failed


def test_gate_actual_acl_widening(replay_result, monkeypatch):
    from rag_audit.access import TIERS

    control(replay_result)
    monkeypatch.setitem(TIERS, "customer", ("public", "restricted"))
    result = evaluate(ROOT, Path(os.environ["SYNTHETIC_MODEL_DIRECTORY"]))
    failed = {
        check["check"]
        for check in checks_for(
            result["rows"], replay_result, result["replay_failures"]
        )
        if not check["passed"]
    }
    assert "hard:forbidden_output" in failed
