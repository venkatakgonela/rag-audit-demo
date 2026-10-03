import asyncio
import json

import httpx
import pytest

from rag_audit.evaluation.replay import MODEL, ReplayTransport, request_hash


def pair():
    body = json.dumps(dict(model=MODEL, input="synthetic evidence")).encode()
    entry = dict(
        request_hash=request_hash(body),
        http_status=200,
        response=dict(model=MODEL),
        consumers=["case/natural/primary", "case/natural/paired"],
        expected_consumptions=2,
    )
    return body, entry


def call(transport, body):
    return asyncio.run(
        transport.handle_async_request(
            httpx.Request("POST", "https://replay.invalid", content=body)
        )
    )


def test_pair_context_counts_are_exact():
    body, entry = pair()
    transport = ReplayTransport([entry])
    transport.bind("case", "natural", "primary")
    first = call(transport, body)
    transport.bind("case", "natural", "paired")
    assert call(transport, body).content == first.content
    transport.complete()
    with pytest.raises(ValueError, match="duplicate"):
        call(transport, body)


@pytest.mark.parametrize(
    "fault", ["unused", "missing-pair", "wrong-context", "hidden-dependent"]
)
def test_pair_faults_fail_with_passing_control(fault):
    body, entry = pair()
    control = ReplayTransport([entry])
    for side in ("primary", "paired"):
        control.bind("case", "natural", side)
        call(control, body)
    control.complete()
    broken = ReplayTransport([entry])
    if fault == "unused":
        with pytest.raises(ValueError, match="staleness"):
            broken.complete()
    else:
        broken.bind("case", "natural", "primary")
        call(broken, body)
        if fault == "missing-pair":
            with pytest.raises(ValueError, match="staleness"):
                broken.complete()
        else:
            broken.bind(
                "other" if fault == "wrong-context" else "case", "natural", "paired"
            )
            changed = (
                body
                if fault == "wrong-context"
                else json.dumps(dict(model=MODEL, input="hidden content")).encode()
            )
            with pytest.raises(ValueError, match="replay_"):
                call(broken, changed)


@pytest.mark.parametrize("missing", ["consumers", "expected_consumptions"])
def test_versioned_manifest_requires_context_metadata(tmp_path, missing):
    import hashlib

    from rag_audit.evaluation.record import write_candidates
    from rag_audit.evaluation.replay import fixture_entries
    from rag_audit.evaluation_data import digest

    _, entry = pair()
    entry["response_digest"] = digest(entry["response"])
    directory = tmp_path / "fixtures"
    write_candidates(directory, [entry], "synthetic")
    assert fixture_entries(directory) == [entry]
    del entry[missing]
    content = json.dumps([entry]).encode()
    (directory / "responses.json").write_bytes(content)
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["sha256"] = hashlib.sha256(content).hexdigest()
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="context metadata missing"):
        fixture_entries(directory)
