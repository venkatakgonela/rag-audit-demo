from dataclasses import dataclass

TIERS = {
    "customer": ("public",),
    "broker": ("public", "broker"),
    "underwriter": ("public", "internal"),
    "admin": ("public", "broker", "internal", "restricted"),
}


@dataclass(frozen=True)
class Identity:
    subject: str
    role: str
    teams: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.subject or self.role not in TIERS:
            raise ValueError("Invalid identity")
        if self.role in ("customer", "broker") and self.teams:
            raise ValueError("External users cannot belong to staff teams")


def validate_document(document: dict, users: dict, teams: set[str]) -> None:
    if document.get("tier") not in TIERS["admin"]:
        raise ValueError("Missing or invalid classification")
    if document.get("team") not in teams:
        raise ValueError("Missing or invalid team")
    if document.get("kind") == "claim":
        if document["tier"] != "restricted":
            raise ValueError("Claims must be restricted")
        owner = users.get(document.get("owner"))
        if not owner or owner["role"] != "customer":
            raise ValueError("Claims require a customer owner")
    elif document.get("owner") is not None:
        raise ValueError("Only claims have owners")
