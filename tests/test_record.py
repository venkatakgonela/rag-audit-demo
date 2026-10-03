import json
import sys

import pytest

from rag_audit.evaluation import record
from rag_audit.evaluation.replay import MODEL, fixture_entries
from rag_audit.evaluation_data import digest


def test_sanitiser_preserves_rejected_text_and_usage(tmp_path):
    text = "ignore previous instructions: synthetic rejected output"
    response = dict(
        model="private-model",
        id="private-id",
        status="completed",
        output=[
            dict(type="reasoning", id="private-reason", summary=[]),
            dict(
                type="message",
                id="private-message",
                role="assistant",
                status="completed",
                content=[dict(type="output_text", text=text, annotations=["private"])],
            ),
        ],
        usage=dict(
            input_tokens=10,
            output_tokens=3,
            total_tokens=13,
            input_tokens_details=dict(
                cached_tokens=0, cache_write_tokens=0, private="secret"
            ),
            output_tokens_details=dict(reasoning_tokens=0),
        ),
    )
    entry = record.sanitise(
        b'{"model":"private-model","input":"synthetic"}', response, 200
    )
    assert entry["request_hash"] == digest(dict(model=MODEL, input="synthetic"))
    assert entry["response"]["output"][0]["content"][0]["text"] == text
    assert "private" not in json.dumps(entry)
    record.write_candidates(tmp_path / "candidate", [entry], "synthetic-commit")
    assert fixture_entries(tmp_path / "candidate") == [entry]


def test_record_cli_rejects_override_before_live_call(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "record",
            "--output",
            str(tmp_path / "new"),
            "--forecast-baseline",
            "forecast.json",
            "--split",
            "dev",
        ],
    )
    monkeypatch.setattr(
        record, "evaluation_main", lambda: pytest.fail("Live call forbidden")
    )
    with pytest.raises(SystemExit):
        record.main()


@pytest.mark.parametrize("variable", ["CI", "GITHUB_ACTIONS"])
def test_record_and_rebaseline_refuse_ci_before_evaluation(
    monkeypatch, tmp_path, variable
):
    from rag_audit.evaluation import ci_gate

    monkeypatch.setenv(variable, "true")
    with pytest.raises(ValueError, match="record_forbidden"):
        record.require_record_permission(
            True, "Explicit synthetic test reason", record.Settings()
        )
    monkeypatch.setattr(sys, "argv", ["gate", "--root", str(tmp_path), "--rebaseline"])
    monkeypatch.setattr(
        ci_gate, "evaluate", lambda *args: pytest.fail("Evaluation forbidden")
    )
    with pytest.raises(ValueError, match="rebaseline_opt_in"):
        ci_gate.main()
