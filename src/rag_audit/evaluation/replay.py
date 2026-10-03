import hashlib
import json
import socket
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from pydantic import SecretStr

from rag_audit.accounting import Price
from rag_audit.evaluation_data import digest
from rag_audit.responses import ResponsesProvider

MODEL = "local-provider-1"


def request_hash(body: bytes) -> str:
    data = json.loads(body)
    if data.get("model") != MODEL:
        raise ValueError("Replay requires neutral model identity")
    return digest(data)


def fixture_entries(directory: Path) -> list[dict]:
    manifest = json.loads((directory / "manifest.json").read_text())
    content = (directory / "responses.json").read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest["sha256"]:
        raise ValueError("fixture_digest: response file changed")
    entries = json.loads(content)
    identities = [entry["request_hash"] for entry in entries]
    if len(identities) != len(set(identities)):
        raise ValueError("replay_duplicate: duplicate fixture identity")
    if len(entries) != manifest["count"] or identities != manifest["request_hashes"]:
        raise ValueError("fixture_manifest: count or identity mismatch")
    for entry in entries:
        if digest(entry["response"]) != entry["response_digest"]:
            raise ValueError("fixture_digest: entry changed")
        if entry["response"].get("model") != MODEL:
            raise ValueError("fixture_identity: expected neutral model")
        if "consumers" in entry:
            consumers = entry["consumers"]
            if (
                type(consumers) is not list
                or not consumers
                or any(type(value) is not str for value in consumers)
                or len(consumers) != len(set(consumers))
                or entry.get("expected_consumptions") != len(consumers)
            ):
                raise ValueError("fixture_consumers: invalid expected consumption")
    if manifest.get("version") == "neutral-http-v2":
        expected = {
            entry["request_hash"]: entry["expected_consumptions"] for entry in entries
        }
        if manifest.get("expected_consumptions") != expected:
            raise ValueError("fixture_consumers: manifest mismatch")
    return entries


class ReplayTransport(httpx.AsyncBaseTransport):
    def __init__(self, entries: list[dict]):
        self.entries = {entry["request_hash"]: entry for entry in entries}
        if len(self.entries) != len(entries):
            raise ValueError("replay_duplicate: duplicate fixture identity")
        self.used: list[str] = []
        self.failures: list[dict] = []
        self.calls = 0
        self.ledger = SimpleNamespace(stopped=False)
        self.context = "unbound"
        self.consumers: list[dict] = []

    def bind(self, case, style, side):
        self.context = f"{case}/{style}/{side}"

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        identity = request_hash(await request.aread())
        self.calls += 1
        entry = self.entries.get(identity)
        allowed = entry.get("consumers") if entry else None
        duplicate = (
            identity in self.used
            if allowed is None
            else any(row["context"] == self.context for row in self.consumers)
        )
        invalid_context = allowed is not None and self.context not in allowed
        check = (
            "replay_duplicate"
            if duplicate
            else "replay_context"
            if invalid_context
            else "replay_miss"
        )
        if duplicate or invalid_context or entry is None:
            self.failures.append(
                dict(check=check, request_hash=identity, context=self.context)
            )
            raise ValueError(
                f"{check}: {identity}; use the explicit local record protocol"
            )
        self.used.append(identity)
        self.consumers.append(dict(context=self.context, request_hash=identity))
        return httpx.Response(entry["http_status"], json=entry["response"])

    def complete(self) -> None:
        missing = sorted(
            identity
            for identity, entry in self.entries.items()
            if self.used.count(identity) != entry.get("expected_consumptions", 1)
        )
        if missing:
            self.failures.append(dict(check="replay_extra", count=len(missing)))
        if self.failures:
            raise ValueError(
                "replay_staleness: request set changed; "
                "inspect diagnostics and re-record explicitly"
            )


def provider(transport: ReplayTransport):
    adapter = ResponsesProvider(
        "https://replay.invalid",
        MODEL,
        MODEL,
        SecretStr("synthetic-replay-credential"),
        transport=transport,
    )
    price = Price(
        "operator-list-replay-v1",
        Decimal(10),
        Decimal(50),
        Decimal(1),
        Decimal(50),
        "provider_tokens",
        Decimal("12.5"),
        "Operator list estimates, not billing; replay spends nothing.",
    )
    return adapter, {MODEL: price}, transport


@contextmanager
def no_network():
    violations: list[str] = []

    def blocked(*args, **kwargs):
        violations.append("network_attempt")
        raise ValueError("network_attempt: replay forbids external access")

    with (
        patch.object(socket.socket, "connect", blocked),
        patch.object(socket.socket, "connect_ex", blocked),
        patch.object(socket, "getaddrinfo", blocked),
        patch.object(httpx, "AsyncHTTPTransport", blocked),
    ):
        yield violations
    if violations:
        raise ValueError("network_attempt: attempted network use during replay")
