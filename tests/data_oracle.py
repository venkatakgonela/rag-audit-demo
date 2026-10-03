from datetime import date
from decimal import Decimal


def expected_rule(operation: str, claim: dict, policy: dict) -> str:
    if operation == "status":
        return claim["status"]
    if operation == "payout":
        remaining = int(Decimal(claim["loss"]) * 100) - int(
            Decimal(policy["excess"]) * 100
        )
        ceiling = int(Decimal(policy["limit"]) * 100)
        pennies = 0 if remaining < 0 else ceiling if remaining > ceiling else remaining
        return f"{pennies // 100}.{pennies % 100:02d}"
    elapsed = (
        date.fromisoformat(claim["notified"]) - date.fromisoformat(claim["incident"])
    ).days
    covered = claim["peril"] in policy["covered"]
    return "eligible" if covered and 0 <= elapsed <= policy["window"] else "ineligible"
