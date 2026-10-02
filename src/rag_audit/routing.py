import re
from dataclasses import dataclass

ENTITY = re.compile(r"\bsynthetic-(?:claim|policy)-[\w-]+\b", re.IGNORECASE)
OPERATIONS = {
    "status": r"\bstatus\b",
    "payout": r"\b(?:payout|payable)\b",
    "eligibility": r"\b(?:eligibility|eligible)\b",
}


@dataclass(frozen=True)
class Route:
    operation: str | None
    entities: tuple[str, ...]
    valid: bool


def route(question: str) -> Route:
    entities = tuple(
        sorted(
            {
                identifier.removesuffix("-canary")
                for identifier in ENTITY.findall(question.lower())
            }
        )
    )
    operations = [
        name
        for name, pattern in OPERATIONS.items()
        if re.search(pattern, question, re.IGNORECASE)
    ]
    claims = [entity for entity in entities if entity.startswith("synthetic-claim-")]
    policies = [entity for entity in entities if entity.startswith("synthetic-policy-")]
    valid = len(claims) <= 1 and len(policies) <= 1 and len(operations) <= 1
    if operations and len(claims) != 1:
        valid = False
    return Route(operations[0] if len(operations) == 1 else None, entities, valid)
