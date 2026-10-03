import asyncio
import copy
import json
import socket
from pathlib import Path

import httpx
import pytest

from rag_audit.evaluation.model_integrity import verify
from rag_audit.evaluation.replay import (
    MODEL,
    ReplayTransport,
    fixture_entries,
    no_network,
    request_hash,
)

ROOT = Path(__file__).resolve().parents[1]


def test_replay_duplicate_miss_and_extra_fail_loudly():
    entries = fixture_entries(ROOT / "datasets/evaluation/replay")
    with pytest.raises(ValueError, match="duplicate"):
        ReplayTransport(entries + entries[:1])
    transport = ReplayTransport(entries)
    request = httpx.Request("POST", "https://replay.invalid", json={"model": MODEL})
    with pytest.raises(ValueError, match="replay_miss"):
        asyncio.run(transport.handle_async_request(request))
    assert transport.failures[0]["request_hash"] == request_hash(
        json.dumps({"model": MODEL}).encode()
    )
    with pytest.raises(ValueError, match="staleness"):
        transport.complete()


def test_replay_roundtrip_and_duplicate_consumption():
    from rag_audit.evaluation_data import digest

    body = json.dumps({"model": MODEL}).encode()
    entry = dict(
        request_hash=request_hash(body), http_status=200, response={"model": MODEL}
    )
    transport = ReplayTransport([entry])
    request = httpx.Request("POST", "https://replay.invalid", content=body)
    response = asyncio.run(transport.handle_async_request(request))
    assert digest(response.json()) == digest(entry["response"])
    transport.complete()
    with pytest.raises(ValueError, match="replay_duplicate"):
        asyncio.run(transport.handle_async_request(request))


def test_fixture_digest_tamper(tmp_path):
    directory = ROOT / "datasets/evaluation/replay"
    (tmp_path / "manifest.json").write_bytes((directory / "manifest.json").read_bytes())
    (tmp_path / "responses.json").write_bytes(
        (directory / "responses.json").read_bytes() + b" "
    )
    with pytest.raises(ValueError, match="fixture_digest"):
        fixture_entries(tmp_path)


def test_network_attempt_remains_failure_if_caught():
    with pytest.raises(ValueError, match="network_attempt"):
        with no_network():
            try:
                socket.getaddrinfo("replay.invalid", 443)
            except ValueError:
                pass


def test_model_integrity_does_not_trust_cache_metadata(tmp_path):
    import hashlib

    content = b"synthetic original"
    expected = hashlib.sha256(content).hexdigest()
    manifest = dict(
        model="synthetic",
        revision="fixed",
        files={"model": dict(bytes=len(content), sha256=expected)},
    )
    (tmp_path / "model").write_bytes(content)
    metadata: dict = dict(
        model="synthetic", revision="fixed", hashes={"model": expected}
    )
    (tmp_path / "identity.json").write_text(json.dumps(metadata))
    verify(tmp_path, manifest)
    (tmp_path / "model").write_bytes(b"poisoned")
    changed = copy.deepcopy(metadata)
    changed["hashes"]["model"] = hashlib.sha256(b"poisoned").hexdigest()
    (tmp_path / "identity.json").write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="model_digest"):
        verify(tmp_path, manifest)
