from pathlib import Path

import pytest
import yaml

from rag_audit.evaluation.record import require_record_permission
from rag_audit.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_ci_pins_and_unconditional_model_verification():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    assert set(workflow["jobs"]) == {"checks", "integration", "evaluation"}
    assert workflow["permissions"] == {"contents": "read"}
    for job in workflow["jobs"].values():
        assert job["runs-on"] == "ubuntu-24.04"
        checkout = next(
            step
            for step in job["steps"]
            if step.get("uses", "").startswith("actions/checkout")
        )
        assert checkout["with"]["persist-credentials"] is False
        assert checkout["uses"] == (
            "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
        )
    steps = workflow["jobs"]["evaluation"]["steps"]
    verify = next(step for step in steps if "eval-model" in step.get("run", ""))
    assert "if" not in verify
    cache = next(
        step for step in steps if step.get("uses", "").startswith("actions/cache")
    )
    assert "model-manifest.json" in cache["with"]["key"]
    assert "restore-keys" not in cache["with"]
    assert steps.index(cache) < steps.index(verify)
    assert not any(
        "eval-record" in step.get("run", "") or "eval-rebaseline" in step.get("run", "")
        for step in steps
    )
    assert "secrets." not in (ROOT / ".github/workflows/ci.yml").read_text()


def test_record_permission_guards_before_transport(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    settings = Settings(generation_key_env="SYNTHETIC_TEST_RECORD_KEY")
    with pytest.raises(ValueError, match="record_opt_in"):
        require_record_permission(
            False, "A meaningful test-only recording reason", settings
        )
    monkeypatch.delenv("SYNTHETIC_TEST_RECORD_KEY", raising=False)
    with pytest.raises(ValueError, match="record_key"):
        require_record_permission(
            True, "A meaningful test-only recording reason", settings
        )
    monkeypatch.setenv("SYNTHETIC_TEST_RECORD_KEY", "synthetic")
    require_record_permission(True, "A meaningful test-only recording reason", settings)
    monkeypatch.setenv("CI", "true")
    with pytest.raises(ValueError, match="record_forbidden"):
        require_record_permission(
            True, "A meaningful test-only recording reason", settings
        )
