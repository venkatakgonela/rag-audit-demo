import hashlib
import json
import math
from pathlib import Path

import psycopg

from rag_audit.access import Identity, validate_document
from rag_audit.chunking import chunk_document
from rag_audit.embeddings import Embedder


def ingest(connection: psycopg.Connection, directory: Path, embedder: Embedder) -> int:
    manifest = json.loads((directory / "manifest.json").read_text())
    users = {user["subject"]: user for user in manifest["users"]}
    if len(users) != len(manifest["users"]):
        raise ValueError("Duplicate users")
    teams = set(manifest["teams"])
    for user in users.values():
        Identity(user["subject"], user["role"], tuple(user["teams"]))
        if not set(user["teams"]) <= teams:
            raise ValueError("Unknown identity team")
    for broker, customer in manifest["brokers"]:
        if users[broker]["role"] != "broker" or users[customer]["role"] != "customer":
            raise ValueError("Invalid broker assignment")
    records = []
    seen = set()
    for document in manifest["documents"]:
        validate_document(document, users, teams)
        if document["id"] in seen:
            raise ValueError("Duplicate document")
        seen.add(document["id"])
        path = (directory / document["path"]).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError("Source path escapes corpus")
        source = path.read_text(encoding="utf-8")
        if hashlib.sha256(source.encode()).hexdigest() != document["sha256"]:
            raise ValueError("Source hash mismatch")
        chunks = chunk_document(document["id"], source, embedder)
        vectors = embedder.encode(
            [chunk.section + "\n" + chunk.text for chunk in chunks]
        )
        if len(vectors) != len(chunks) or any(
            len(vector) != 384
            or not all(math.isfinite(value) for value in vector)
            or not any(vector)
            for vector in vectors
        ):
            raise ValueError("Invalid embedding vectors")
        records.append((document, source, chunks, vectors))
    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(482031)")
        connection.execute("DELETE FROM demo_chunks")
        connection.execute("DELETE FROM demo_documents")
        connection.execute("DELETE FROM demo_brokers")
        connection.execute("DELETE FROM demo_users")
        for user in users.values():
            connection.execute(
                "INSERT INTO demo_users VALUES (%s,%s,%s)",
                (user["subject"], user["role"], user["teams"]),
            )
        for assignment in manifest["brokers"]:
            connection.execute("INSERT INTO demo_brokers VALUES (%s,%s)", assignment)
        for document, source, chunks, vectors in records:
            connection.execute(
                "INSERT INTO demo_documents VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    document["id"],
                    source,
                    document["kind"],
                    document["tier"],
                    document["team"],
                    document["owner"],
                ),
            )
            for chunk, vector in zip(chunks, vectors, strict=True):
                connection.execute(
                    "INSERT INTO demo_chunks VALUES "
                    "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,"
                    "to_tsvector('english',%s),%s,%s)",
                    (
                        chunk.identifier,
                        document["id"],
                        chunk.text,
                        chunk.section,
                        chunk.ordinal,
                        chunk.start,
                        chunk.end,
                        document["tier"],
                        document["team"],
                        document["owner"],
                        str(vector),
                        chunk.section + "\n" + chunk.text,
                        manifest["version"],
                        embedder.identity,
                    ),
                )
        connection.execute(
            "INSERT INTO demo_configuration VALUES (true,%s,%s) "
            "ON CONFLICT(singleton) DO UPDATE SET "
            "model_identity=excluded.model_identity,"
            "corpus_version=excluded.corpus_version",
            (embedder.identity, manifest["version"]),
        )
    return sum(len(record[2]) for record in records)
