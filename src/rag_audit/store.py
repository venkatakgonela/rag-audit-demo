import re
from dataclasses import dataclass
from typing import Protocol

import psycopg
from psycopg.pq import TransactionStatus
from psycopg.types.json import Jsonb

from rag_audit.access import ACL_SQL, Identity, access_parameters, load_identity
from rag_audit.embeddings import Embedder
from rag_audit.retrieval import retrieve
from rag_audit.routing import Route
from rag_audit.rules import RuleResult, calculate
from rag_audit.structured import visible_record


@dataclass(frozen=True)
class Snapshot:
    identity: Identity
    corpus_version: str
    model_identity: str
    chunks: list[dict]
    rule: RuleResult | None = None


class Store(Protocol):
    def snapshot(
        self, subject: str, question: str, route: Route, embedder: Embedder
    ) -> Snapshot: ...
    def trace(self, request_id: str, payload: dict) -> None: ...


class PostgresStore:
    def __init__(self, connection: psycopg.Connection):
        self.connection = connection

    def require_idle(self) -> None:
        if self.connection.info.transaction_status != TransactionStatus.IDLE:
            raise ValueError("Answering requires an idle dedicated connection")

    def snapshot(
        self, subject: str, question: str, route: Route, embedder: Embedder
    ) -> Snapshot:
        self.require_idle()
        with self.connection.transaction():
            self.connection.execute("SELECT pg_advisory_xact_lock_shared(482031)")
            self.connection.execute(
                "LOCK TABLE demo_users,demo_brokers,demo_documents,demo_chunks,"
                "demo_claims,demo_policies,demo_configuration IN SHARE MODE"
            )
            identity = load_identity(self.connection, subject)
            config = self.connection.execute(
                "SELECT corpus_version,model_identity FROM demo_configuration "
                "WHERE singleton"
            ).fetchone()
            if (
                config is None
                or config[1] != embedder.identity
                or not config[0].startswith("synthetic-v3-")
            ):
                raise ValueError("Ingest matching corpus v3 first")
            empty = Snapshot(identity, config[0], config[1], [])
            if not route.valid:
                return empty
            records = {}
            for identifier in route.entities:
                record = visible_record(self.connection, identity, identifier)
                if record is None:
                    return empty
                records[identifier] = record
            claim = next(
                (
                    record
                    for key, record in records.items()
                    if key.startswith("synthetic-claim-")
                ),
                None,
            )
            policy = next(
                (
                    record
                    for key, record in records.items()
                    if key.startswith("synthetic-policy-")
                ),
                None,
            )
            if claim and policy and claim["policy_id"] != policy["id"]:
                return empty
            if route.operation:
                if claim is None:
                    return empty
                if route.operation != "status":
                    policy = visible_record(
                        self.connection, identity, claim["policy_id"]
                    )
                    if policy is None:
                        return empty
                result = calculate(route.operation, claim, policy, config[0])
                return Snapshot(identity, config[0], config[1], [], result)
            scope = route.entities or None
            sentinels = re.findall(r"\b(synthetic-[\w-]+)-canary\b", question.lower())
            if sentinels:
                for identifier in sentinels:
                    parameters = {**access_parameters(identity), "id": identifier}
                    row = self.connection.execute(
                        "SELECT d.id FROM demo_documents d WHERE d.id=%(id)s AND "
                        + ACL_SQL,
                        parameters,
                    ).fetchone()
                    if row is None:
                        return empty
                scope = tuple(sentinels)
            chunks = retrieve(
                self.connection,
                subject,
                question,
                embedder,
                top_k=20,
                document_ids=scope,
            )["chunks"]
            return Snapshot(identity, config[0], config[1], chunks)

    def trace(self, request_id: str, payload: dict) -> None:
        self.require_idle()
        with self.connection.transaction():
            self.connection.execute(
                "INSERT INTO demo_traces(request_id,payload) VALUES (%s,%s)",
                (request_id, Jsonb(payload)),
            )
