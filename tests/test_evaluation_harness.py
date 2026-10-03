import asyncio
from pathlib import Path

import pytest

from rag_audit.evaluation.baseline import BaselineGenerator
from rag_audit.evaluation.calibration import choose, grid, summarize
from rag_audit.evaluation.data import load_split
from rag_audit.evaluation.metrics import percentile, rate
from rag_audit.gate import Gate, lexical_coverage
from rag_audit.generation import Evidence, GenerationRequest

ROOT = Path(__file__).resolve().parents[1]


def test_grid_is_predeclared():
    variants = grid()
    assert len(variants) == 114
    assert len(set(variants)) == 114
    assert [
        sum(gate.variant == name for gate in variants)
        for name in ("V0", "V1", "V2", "V3")
    ] == [1, 18, 72, 23]


def test_metrics_hand_computed():
    assert rate(0, 0)["value"] is None
    assert rate(1, 1)["interval"] == pytest.approx([0.20654931437723745, 1])
    assert rate(5, 10)["value"] == 0.5
    assert percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert percentile([1, 2, 3, 4, 5], 0.95) == 5
    with pytest.raises(ValueError):
        rate(2, 1)


def test_gate_signal_local_and_boundaries():
    chunk = dict(
        section="Receipts",
        text="Keep the blue receipt.",
        cosine_similarity=0.5,
        keyword_score=0,
        keyword_rank=None,
    )
    assert lexical_coverage("the blue receipt", chunk) == 1
    assert not Gate().accepts(chunk, "blue receipt")
    assert Gate("V1", 0.5).accepts(chunk, "blue receipt")
    assert Gate("V2", 0.5, 1).accepts(chunk, "blue receipt")
    assert Gate("V3", 0.75).accepts(chunk, "blue receipt")
    assert not Gate("V3", 0.8).accepts(chunk, "blue receipt")
    assert lexical_coverage("the and", chunk) == 0


def test_baseline_is_label_blind_exact_and_deterministic():
    provider = BaselineGenerator()
    request = GenerationRequest(
        "blue receipt",
        (Evidence("chunk", "First sentence. Keep the blue receipt. Last sentence."),),
        512,
        10,
        "test",
    )
    first = asyncio.run(provider.generate(request))
    second = asyncio.run(provider.generate(request))
    assert first == second
    assert "Keep the blue receipt." in first.payload
    assert provider.calls == 2


def test_calibration_never_opens_test_labels(monkeypatch):
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path.name in ("test.json", "golden.json"):
            raise AssertionError("Test labels read during calibration")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    cases = load_split(ROOT, "dev")
    assert len(cases) == 42
    assert all(case.split == "dev" for case in cases)


def test_calibration_rejects_test_case():
    cases = load_split(ROOT, "test")
    with pytest.raises(ValueError, match="dev"):
        summarize(Gate(), cases, [])


def test_calibration_selection_band_and_fallback():
    def row(variant, count, natural, eligible=True):
        return dict(
            gate=dict(variant=variant, threshold=0.55, fraction=0),
            counts=dict(near_miss=count),
            sufficient=dict(natural=natural, keyword=10),
            eligible=eligible,
        )

    rows = [row("V0", 0, 4), row("V1", 1, 9), row("V2", 2, 12)]
    assert choose(rows)["gate"]["variant"] == "V1"
    for item in rows:
        item["eligible"] = False
    assert choose(rows)["gate"]["variant"] == "V0"


def test_runtime_cannot_import_evaluation():
    import ast

    runtime = ROOT / "src/rag_audit"
    for path in runtime.rglob("*.py"):
        if "evaluation" in path.parts or path.name == "evaluation_data.py":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("rag_audit.evaluation")
            if isinstance(node, ast.Import):
                assert all(
                    not alias.name.startswith("rag_audit.evaluation")
                    for alias in node.names
                )
        assert "datasets/evaluation" not in path.read_text()
