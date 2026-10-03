import copy
import json
from pathlib import Path

import pytest

from rag_audit.evaluation import ci_gate
from rag_audit.evaluation_data import read_json

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "fault", ["changelog", "chain", "reason", "baseline", "config"]
)
def test_baseline_history_and_changelog_have_passing_control(
    tmp_path, monkeypatch, fault
):
    directory = tmp_path / "datasets/evaluation"
    directory.mkdir(parents=True)
    log = ROOT / "datasets/evaluation/gate-baseline-log.jsonl"
    (directory / log.name).write_bytes(log.read_bytes())
    (tmp_path / "CHANGELOG.md").write_bytes((ROOT / "CHANGELOG.md").read_bytes())
    baseline = copy.deepcopy(
        read_json(ROOT / "datasets/evaluation/baselines/ci-v1.json")
    )
    ci_gate_config = copy.deepcopy(baseline["config"])
    monkeypatch.setattr(ci_gate, "configuration", lambda root: ci_gate_config)
    ci_gate.integrity(tmp_path, baseline)
    if fault == "changelog":
        (tmp_path / "CHANGELOG.md").write_text("No markers")
    elif fault in ("chain", "reason"):
        events = [json.loads(line) for line in log.read_text().splitlines()]
        events[-1]["previous_digest" if fault == "chain" else "reason"] = ""
        (directory / log.name).write_text(
            "\n".join(json.dumps(event) for event in events)
        )
    elif fault == "baseline":
        baseline["measures"]["dev/natural/evidence_sufficient"] += 1
    else:
        baseline["config_digest"] = "altered"
    with pytest.raises(ValueError, match="baseline_"):
        ci_gate.integrity(tmp_path, baseline)
