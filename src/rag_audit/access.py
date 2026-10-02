from dataclasses import dataclass

import psycopg

ACL_SQL = """(
 d.tier = ANY(%(tiers)s) OR d.team = ANY(%(teams)s)
 OR (d.kind='claim' AND d.owner=%(subject)s)
 OR (d.kind='claim' AND %(role)s='broker' AND EXISTS (
 SELECT 1 FROM demo_brokers b WHERE b.broker=%(subject)s AND b.customer=d.owner)))"""

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


def load_identity(connection: psycopg.Connection, subject: str) -> Identity:
    row = connection.execute(
        "SELECT subject,role,teams FROM demo_users WHERE subject=%s", (subject,)
    ).fetchone()
    if row is None:
        raise ValueError("Unknown fixture identity")
    return Identity(row[0], row[1], tuple(row[2]))


def access_parameters(identity: Identity) -> dict:
    return {
        "subject": identity.subject,
        "role": identity.role,
        "teams": list(identity.teams),
        "tiers": list(TIERS[identity.role]),
    }


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
