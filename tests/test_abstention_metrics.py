import copy

import pytest
from test_evaluation_completion import example

from rag_audit.evaluation.reporting import summarize_rows
from rag_audit.evaluation.trial import candidate_summary
from rag_audit.policy import envelope


def test_abstention_sources_and_answer_outcomes_remain_distinct():
    answer = example()
    rows = [answer]
    for reason, selected in (
        ("no_evidence", False),
        ("model_abstained", True),
        ("verification_failed", True),
    ):
        row = copy.deepcopy(answer)
        row["response"] = envelope()
        row["trace"]["reason"] = reason
        row["trace"]["verification_reason"] = (
            "schema" if reason == "verification_failed" else None
        )
        row["trace"]["sent_ids"] = ["first"] if selected else []
        row["assessment"].update(
            correct=False, allowed=False, missed_answer=True, answered_wrong=False
        )
        rows.append(row)
    negative = copy.deepcopy(rows[2])
    negative["category"] = "unanswerable"
    negative["assessment"].update(allowed=True, missed_answer=False)
    rows.append(negative)
    result = summarize_rows(rows)
    assert result["answers"]["hits"] == 1
    assert result["gate_abstention"]["hits"] == 1
    assert result["model_abstention"]["hits"] == 2
    assert result["verification_rejection"]["hits"] == 1
    assert result["missed_answer"]["hits"] == 3
    assert result["correct_abstention"]["hits"] == 1
    assert result["false_evidence"]["hits"] == 1
    assert result["false_answer"]["hits"] == 0
    assert result["model_abstention"]["total"] == 5
    assert result["model_abstention"]["interval"] is not None


@pytest.mark.parametrize(
    "fault",
    ["hard", "off_domain", "id_lookup", "free_text", "incomplete", "error", "test"],
)
def test_trial_eligibility_rejects_each_invalid_condition(fault):
    rows = []
    for index in range(84):
        row = copy.deepcopy(example())
        row["case"] = f"synthetic-{index}"
        row["hard_failures"] = []
        row["assessment"].update(correct=True, false_answer=False)
        rows.append(row)
    assert candidate_summary(0.75, rows)["eligible"]
    if fault == "test":
        rows[0]["split"] = "test"
        with pytest.raises(ValueError, match="dev only"):
            candidate_summary(0.75, rows)
        return
    if fault == "hard":
        rows[0]["hard_failures"] = ["synthetic-failure"]
    elif fault == "error":
        rows[0]["response"]["decision"] = "error"
    elif fault == "incomplete":
        rows.pop()
    else:
        rows[0]["challenge_kind"] = fault
        rows[0]["assessment"]["false_answer"] = True
    assert not candidate_summary(0.75, rows)["eligible"]
