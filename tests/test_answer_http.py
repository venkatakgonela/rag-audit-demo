import base64
import hashlib
import hmac
import json
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from test_answering import MemoryStore

from rag_audit.api import main
from rag_audit.auth import encode, issue_token, verify_token

KEY = "synthetic-disposable-signing-key-000000"


@pytest.fixture
def client(monkeypatch):
    store = MemoryStore([])

    @contextmanager
    def context(settings):
        yield store

    monkeypatch.setattr(main, "store_context", context)
    monkeypatch.setenv("STUB_SIGNING_KEY", KEY)
    return TestClient(main.app), store


def headers(subject="synthetic-customer-a"):
    return {"Authorization": "Bearer " + issue_token(subject, KEY)}


def test_signed_subject_only_roundtrip():
    token = issue_token("synthetic-customer-a", KEY)
    assert verify_token(token, KEY) == "synthetic-customer-a"
    payload = token.split(".")[1]
    assert json.loads(
        base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    ) == {"sub": "synthetic-customer-a"}


@pytest.mark.parametrize(
    "token",
    [
        "",
        "v2.a.b",
        "v1.a.b",
        "x" * 1025,
        issue_token("synthetic-customer-a", KEY) + "=",
        issue_token("synthetic-customer-a", KEY + "wrong"),
    ],
)
def test_invalid_tokens_rejected(token):
    with pytest.raises(ValueError):
        verify_token(token, KEY)


def test_signed_extra_claims_and_noncanonical_encoding_rejected():
    for body in (
        {"sub": "synthetic-customer-a", "role": "admin"},
        {"sub": "synthetic-customer-a"},
    ):
        payload = encode(json.dumps(body).encode())
        message = f"v1.{payload}"
        token = (
            message
            + "."
            + encode(hmac.digest(KEY.encode(), message.encode(), hashlib.sha256))
        )
        with pytest.raises(ValueError):
            verify_token(token, KEY)


def test_body_privilege_claims_cannot_override_identity(client):
    http, store = client
    response = http.post(
        "/ask",
        headers=headers(),
        json={"question": "status synthetic-claim-1", "role": "admin"},
    )
    assert response.status_code == 400
    assert response.json()["decision"] == "error"
    assert store.traces[0][1]["role"] is None
    assert "admin" not in str(store.traces)


def test_missing_and_forged_auth_is_sanitized_and_traced(client):
    http, store = client
    for auth in ({}, {"Authorization": "Bearer synthetic-secret-forgery"}):
        response = http.post("/ask", headers=auth, json={"question": "secret"})
        assert response.status_code == 401
        assert "secret" not in response.text
    assert len(store.traces) == 2
    assert "secret" not in str(store.traces)


def test_valid_request_and_body_limits(client, monkeypatch):
    http, store = client
    response = http.post(
        "/ask", headers=headers(), json={"question": "repair receipts"}
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "no_answer"
    for raw in (b"not json", b'{"question":null}', b'{"question":"a","question":"b"}'):
        assert http.post("/ask", headers=headers(), content=raw).status_code == 400
    monkeypatch.setenv("HTTP_BODY_BYTES", "10")
    assert http.post("/ask", headers=headers(), content=b"x" * 11).status_code == 413
    store.fail_trace = True
    assert http.post("/ask", headers=headers(), content=b"x").status_code == 503


def test_missing_key_and_unknown_subject_fail_closed(client, monkeypatch):
    http, _ = client
    assert (
        http.post(
            "/ask", headers=headers("synthetic-unknown"), json={"question": "repair"}
        ).status_code
        == 503
    )
    monkeypatch.delenv("STUB_SIGNING_KEY")
    assert (
        http.post("/ask", headers=headers(), json={"question": "repair"}).status_code
        == 503
    )
