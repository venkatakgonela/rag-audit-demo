from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

STATUSES = ("pending", "approved", "declined", "paid")
PERILS = ("water", "theft", "fire", "flood")


def money(value: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("Amounts require decimal strings")
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError("Invalid amount") from None
    if not result.is_finite() or result < 0 or result > Decimal("999999999.99"):
        raise ValueError("Invalid amount")
    exponent = result.as_tuple().exponent
    if not isinstance(exponent, int) or exponent < -2:
        raise ValueError("Fractional cent input")
    return result


def payout(loss: Decimal, excess: Decimal, limit: Decimal) -> Decimal:
    if any(not value.is_finite() or value < 0 for value in (loss, excess, limit)):
        raise ValueError("Invalid amount")
    with localcontext() as context:
        context.prec = 32
        return max(Decimal(0), min(loss - excess, limit)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


def eligibility(
    peril: str, covered: list[str], incident: date, notified: date, window: int
) -> bool:
    if peril not in PERILS or not set(covered) <= set(PERILS) or not 0 <= window <= 365:
        raise ValueError("Invalid eligibility input")
    days = (notified - incident).days
    if days < 0:
        raise ValueError("Notification precedes incident")
    return peril in covered and days <= window


@dataclass(frozen=True)
class RuleResult:
    name: str
    record_ids: tuple[str, ...]
    inputs: dict
    value: str
    corpus_version: str
    version: str = "synthetic-rules-v1"


def calculate(
    operation: str, claim: dict, policy: dict | None, version: str
) -> RuleResult:
    if operation == "status":
        if claim["status"] not in STATUSES:
            raise ValueError("Invalid status")
        return RuleResult(
            operation,
            (claim["id"],),
            {"status": claim["status"]},
            claim["status"],
            version,
        )
    if policy is None:
        raise ValueError("Policy required")
    inputs = {
        "loss": claim["loss"],
        "excess": policy["excess"],
        "limit": policy["limit"],
        "peril": claim["peril"],
        "covered": policy["covered"],
        "incident": claim["incident"],
        "notified": claim["notified"],
        "window": policy["window"],
    }
    if operation == "payout":
        value = str(
            payout(
                money(claim["loss"]), money(policy["excess"]), money(policy["limit"])
            )
        )
    elif operation == "eligibility":
        value = (
            "eligible"
            if eligibility(
                claim["peril"],
                policy["covered"],
                date.fromisoformat(claim["incident"]),
                date.fromisoformat(claim["notified"]),
                policy["window"],
            )
            else "ineligible"
        )
    else:
        raise ValueError("Unknown rule")
    return RuleResult(operation, (claim["id"], policy["id"]), inputs, value, version)


def templates(result: RuleResult) -> tuple[str, str]:
    label = {
        "status": "Claim status",
        "payout": "Payout in GBP",
        "eligibility": "Eligibility",
    }[result.name]
    return (f"{label}: {result.value}.", f"Synthetic result — {label}: {result.value}.")
