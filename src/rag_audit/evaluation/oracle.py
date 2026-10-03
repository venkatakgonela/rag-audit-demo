import json
from datetime import date
from decimal import Decimal


def expected_rule(operation: str, claim: dict, policy: dict) -> str:
    if operation == "status":
        return claim["status"]
    if operation == "payout":
        remaining = int(Decimal(claim["loss"]) * 100) - int(
            Decimal(policy["excess"]) * 100
        )
        pennies = max(0, min(remaining, int(Decimal(policy["limit"]) * 100)))
        return f"{pennies // 100}.{pennies % 100:02d}"
    elapsed = (
        date.fromisoformat(claim["notified"]) - date.fromisoformat(claim["incident"])
    ).days
    return (
        "eligible"
        if claim["peril"] in policy["covered"] and 0 <= elapsed <= policy["window"]
        else "ineligible"
    )


def rule_failures(
    case, response: dict, trace: dict, calls: int, manifest: dict
) -> list[str]:
    label = case.expected_rule
    if label is None:
        return []
    claim = next(record for record in manifest["claims"] if record["id"] == case.scope)
    policy = next(
        record for record in manifest["policies"] if record["id"] == claim["policy_id"]
    )
    result = response.get("rule") or {}
    expected = expected_rule(label.operation, claim, policy)
    wrong = (
        calls != 0
        or response["decision"] != "answered"
        or result.get("name") != label.operation
        or result.get("value") != expected
        or expected != label.value
        or json.dumps(trace.get("rule"), sort_keys=True)
        != json.dumps(result, sort_keys=True)
    )
    if label.operation in ("status", "payout"):
        wrong = (
            wrong
            or result.get("inputs", {}).get("status") != claim["status"]
            or (label.operation == "payout" and label.status != claim["status"])
        )
    return ["rule_oracle"] if wrong else []
