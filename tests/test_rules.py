from datetime import date
from decimal import Decimal

import pytest

from rag_audit.corpus import generate
from rag_audit.routing import route
from rag_audit.rules import calculate, eligibility, money, payout
from rag_audit.structured import validate_records


@pytest.mark.parametrize(
    "loss,excess,limit,expected",
    [
        ("50", "100", "1000", "0.00"),
        ("100", "100", "1000", "0.00"),
        ("1200", "100", "1000", "1000.00"),
        ("100.005", "0", "1000", "100.01"),
        ("100.004", "0", "1000", "100.00"),
        ("0", "0", "0", "0.00"),
    ],
)
def test_payout_boundaries_and_rounding(loss, excess, limit, expected):
    assert str(payout(Decimal(loss), Decimal(excess), Decimal(limit))) == expected


@pytest.mark.parametrize(
    "value", ["NaN", "Infinity", "-1", "1.001", "1000000000", "bad", 1]
)
def test_money_rejects_invalid(value):
    with pytest.raises(ValueError):
        money(value)


@pytest.mark.parametrize(
    "days,peril,expected",
    [
        (0, "water", True),
        (14, "water", True),
        (15, "water", False),
        (1, "theft", False),
    ],
)
def test_eligibility_inclusive(days, peril, expected):
    assert (
        eligibility(peril, ["water"], date(2026, 1, 1), date(2026, 1, 1 + days), 14)
        is expected
    )


def test_negative_delay_rejected():
    with pytest.raises(ValueError):
        eligibility("water", ["water"], date(2026, 1, 2), date(2026, 1, 1), 14)


def test_structured_corpus_v3_and_all_rules(tmp_path):
    manifest = generate(tmp_path)
    validate_records(manifest)
    assert len(manifest["documents"]) == 72
    assert len(manifest["claims"]) == 16
    assert len(manifest["policies"]) == 12
    policies = {record["id"]: record for record in manifest["policies"]}
    for claim in manifest["claims"]:
        policy = policies[claim["policy_id"]]
        for operation in ("status", "payout", "eligibility"):
            result = calculate(operation, claim, policy, manifest["version"])
            assert result.record_ids[0] == claim["id"]
            assert result.corpus_version == manifest["version"]
            if operation == "status":
                assert result.value == claim["status"]


@pytest.mark.parametrize(
    "change", ["format", "missing", "owner", "amount", "policy", "date"]
)
def test_invalid_records_rejected(tmp_path, change):
    manifest = generate(tmp_path)
    if change == "format":
        manifest["format"] = 1
    elif change == "missing":
        manifest["policies"].pop()
    elif change == "owner":
        manifest["claims"][0]["owner"] = "synthetic-customer-b"
    elif change == "amount":
        manifest["claims"][0]["loss"] = "1.001"
    elif change == "policy":
        manifest["claims"][0]["policy_id"] = "synthetic-policy-999"
    else:
        manifest["claims"][0]["notified"] = "2025-01-01"
    with pytest.raises(ValueError):
        validate_records(manifest)


@pytest.mark.parametrize(
    "question,operation,valid",
    [
        ("status synthetic-claim-0", "status", True),
        ("payable synthetic-claim-0 synthetic-policy-0", "payout", True),
        ("eligible synthetic-claim-0", "eligibility", True),
        ("status and payout synthetic-claim-0", None, False),
        ("status", "status", False),
        ("status synthetic-claim-0 synthetic-claim-1", "status", False),
        ("Explain synthetic-claim-1", None, True),
        ("repair receipts", None, True),
    ],
)
def test_deterministic_router(question, operation, valid):
    result = route(question)
    assert result.operation == operation and result.valid is valid
