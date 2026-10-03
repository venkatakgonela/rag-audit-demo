import json
import shutil
from pathlib import Path

import pytest
from data_oracle import expected_rule

from rag_audit.corpus import SOURCE, validate_sources
from rag_audit.evaluation_data import (
    Case,
    check_dataset,
    check_response_constraints,
    read_cases,
    read_json,
)
from rag_audit.rules import calculate

ROOT = Path(__file__).resolve().parents[1]


def test_dataset_integrity():
    result = check_dataset(ROOT)
    assert result["documents"] == 72
    assert result["cases"] == 65
    assert result["phrasings"] == 130
    assert sorted(result["hidden_documents"].values()) == [0, 12, 12, 20, 20, 28, 28]


def test_evaluation_data_is_outside_ingestion_and_prompts():
    manifest = read_json(SOURCE / "manifest.json")
    assert all(
        document["path"].startswith("documents/") and document["path"].endswith(".md")
        for document in manifest["documents"]
    )
    for name in ("ingestion.py", "generation.py", "responses.py", "answering.py"):
        text = (ROOT / "src/rag_audit" / name).read_text()
        assert "evaluation_data" not in text
        assert "datasets/evaluation" not in text


def test_access_table_matches_authored_intent():
    intent = read_json(ROOT / "datasets/evaluation/access-intent.json")
    documentation = (ROOT / "docs/evaluation-data.md").read_text()
    for entry in intent["documents"]:
        row = next(
            line
            for line in documentation.splitlines()
            if line.startswith("| " + entry["document_id"] + " |")
        )
        values = [cell.strip() for cell in row.split("|")[1:-1]]
        assert values[3:] == [
            "yes" if subject in entry["allowed_subjects"] else "no"
            for subject in intent["subjects"]
        ]


def test_independent_rule_oracles():
    manifest = read_json(SOURCE / "manifest.json")
    claims = {record["id"]: record for record in manifest["claims"]}
    policies = {record["id"]: record for record in manifest["policies"]}
    for case in read_cases(ROOT / "datasets/evaluation")["cases"]:
        if case["category"] != "rules":
            continue
        label = case["expected_rule"]
        claim = claims[case["scope"]]
        policy = policies[claim["policy_id"]]
        assert label["value"] == expected_rule(label["operation"], claim, policy)
        result = calculate(label["operation"], claim, policy, manifest["version"])
        assert result.value == label["value"]
        if label["operation"] == "payout":
            assert label["status"] == result.inputs["status"] == claim["status"]


@pytest.mark.parametrize(
    "change",
    [
        "fact",
        "visibility",
        "document",
        "chunk",
        "freeze",
        "forbidden_fact",
        "acceptable_decision",
    ],
)
def test_bad_dataset_is_detected(tmp_path, change):
    shutil.copytree(ROOT / "datasets", tmp_path / "datasets")
    directory = tmp_path / "datasets/evaluation"
    name = "dev.json"
    data = read_json(directory / name)
    if change == "fact":
        data["cases"][0]["support"][0]["key_facts"] = ["not a recorded fact"]
    elif change == "document":
        data["cases"][0]["support"][0]["document_id"] = "synthetic-stale-id"
    elif change == "visibility":
        name = "access-intent.json"
        data = read_json(directory / name)
        data["documents"][0]["allowed_subjects"] = ["synthetic-admin"]
    elif change == "chunk":
        case = next(case for case in data["cases"] if case["forbidden_chunks"])
        next(iter(case["forbidden_chunks"].values()))[0] = "stale-chunk"
    elif change == "forbidden_fact":
        case = next(
            case for case in data["cases"] if case["category"] == "unauthorised"
        )
        case["must_not_appear"] = ["invented unrelated fact"]
    elif change == "acceptable_decision":
        case = next(
            case for case in data["cases"] if case["challenge_kind"] == "ordinary"
        )
        case["acceptable_decisions"] = ["answered"]
    else:
        name = "freeze.json"
        data = read_json(directory / name)
        data["digests"]["test"] = "stale"
    (directory / name).write_text(json.dumps(data))
    with pytest.raises((AssertionError, ValueError, KeyError)):
        check_dataset(tmp_path, frozen=change == "freeze")


def test_prose_record_drift_rejected(tmp_path):
    shutil.copytree(SOURCE, tmp_path / "corpus")
    directory = tmp_path / "corpus"
    manifest = read_json(directory / "manifest.json")
    manifest["policies"][0]["excess"] = "101.00"
    with pytest.raises(ValueError, match="Structured prose"):
        validate_sources(directory, manifest)


def test_source_bindings_cannot_mask_amount_drift():
    manifest = read_json(SOURCE / "manifest.json")
    manifest["policies"][0]["excess"] = "00"
    with pytest.raises(ValueError, match="Structured prose"):
        validate_sources(SOURCE, manifest)


def test_response_label_constraints_are_enforced():
    cases = read_cases(ROOT / "datasets/evaluation")["cases"]
    case = Case.model_validate(
        next(item for item in cases if item["challenge_kind"] == "ordinary")
    )
    check_response_constraints(case, {"decision": "no_answer", "text": "No evidence."})
    quote = case.support[0].key_facts[0]
    check_response_constraints(
        case, {"decision": "answered", "statements": [{"quote": quote}]}
    )
    for response in (
        {"decision": "error"},
        {"decision": "answered", "statements": []},
        {"decision": "no_answer", "text": "IGNORE PREVIOUS INSTRUCTIONS"},
    ):
        with pytest.raises(AssertionError):
            check_response_constraints(case, response)
    hidden = Case.model_validate(
        next(item for item in cases if item["challenge_kind"] == "free_text")
    )
    with pytest.raises(AssertionError):
        check_response_constraints(
            hidden, {"decision": "no_answer", "text": hidden.must_not_appear[0]}
        )
