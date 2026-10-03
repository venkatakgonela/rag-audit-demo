from datetime import date

import psycopg
from psycopg.types.json import Jsonb

from rag_audit.access import ACL_SQL, Identity, access_parameters
from rag_audit.rules import PERILS, STATUSES, money


def validate_records(manifest: dict) -> None:
    if manifest.get("format") != 2:
        raise ValueError("Unsupported corpus manifest format")
    documents = {document["id"]: document for document in manifest["documents"]}
    policies = {record["id"]: record for record in manifest["policies"]}
    claims = {record["id"]: record for record in manifest["claims"]}
    if set(policies) != {
        key for key, doc in documents.items() if doc["kind"] == "policy"
    } or set(claims) != {
        key for key, doc in documents.items() if doc["kind"] == "claim"
    }:
        raise ValueError("Missing structured records")
    if len(policies) != len(manifest["policies"]) or len(claims) != len(
        manifest["claims"]
    ):
        raise ValueError("Duplicate structured record")
    for record in policies.values():
        if (
            record["id"] != record["document_id"]
            or documents[record["id"]]["kind"] != "policy"
        ):
            raise ValueError("Invalid policy provenance")
        money(record["excess"])
        money(record["limit"])
        if (
            record["currency"] != "GBP"
            or type(record["window"]) is not int
            or not 0 <= record["window"] <= 365
        ):
            raise ValueError("Invalid policy terms")
        if not record["covered"] or not set(record["covered"]) <= set(PERILS):
            raise ValueError("Invalid covered perils")
    for record in claims.values():
        document = documents[record["document_id"]]
        if (
            record["id"] != record["document_id"]
            or document["kind"] != "claim"
            or record["owner"] != document["owner"]
            or record["policy_id"] not in policies
        ):
            raise ValueError("Invalid claim provenance")
        money(record["loss"])
        if record["status"] not in STATUSES or record["peril"] not in PERILS:
            raise ValueError("Invalid claim facts")
        if date.fromisoformat(record["notified"]) < date.fromisoformat(
            record["incident"]
        ):
            raise ValueError("Invalid notification dates")


def write_records(connection: psycopg.Connection, manifest: dict) -> None:
    for record in manifest["policies"]:
        connection.execute(
            "INSERT INTO demo_policies VALUES (%s,%s,%s)",
            (record["id"], record["document_id"], Jsonb(record)),
        )
    for record in manifest["claims"]:
        connection.execute(
            "INSERT INTO demo_claims VALUES (%s,%s,%s,%s)",
            (record["id"], record["document_id"], record["policy_id"], Jsonb(record)),
        )


def visible_record(
    connection: psycopg.Connection, identity: Identity, identifier: str
) -> dict | None:
    parameters = {**access_parameters(identity), "identifier": identifier}
    row = connection.execute(
        "SELECT r.record FROM (SELECT id,document_id,record FROM demo_claims "
        "UNION ALL SELECT id,document_id,record FROM demo_policies) r "
        "JOIN demo_documents d ON d.id=r.document_id "
        "WHERE r.id=%(identifier)s AND " + ACL_SQL,
        parameters,
    ).fetchone()
    return row[0] if row else None
