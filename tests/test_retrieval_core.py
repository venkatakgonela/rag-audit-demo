import hashlib
import json
from unittest.mock import Mock

import pytest

from rag_audit.access import Identity, validate_document
from rag_audit.chunking import chunk_document
from rag_audit.corpus import generate
from rag_audit.embeddings import FakeEmbedder


def test_generator_is_deterministic(tmp_path):
    first = generate(tmp_path / "first")
    second = generate(tmp_path / "second")
    assert first == second
    for document in first["documents"]:
        text = (tmp_path / "first" / document["path"]).read_text()
        assert "SYNTHETIC" in text
        assert hashlib.sha256(text.encode()).hexdigest() == document["sha256"]
        assert text == (tmp_path / "second" / document["path"]).read_text()


@pytest.mark.parametrize("role", ["customer", "broker"])
def test_external_membership_rejected(role):
    with pytest.raises(ValueError, match="staff teams"):
        Identity("synthetic-user", role, ("claims-a",))


def test_claim_tier_rejected():
    document = {
        "kind": "claim",
        "tier": "public",
        "team": "claims-a",
        "owner": "synthetic-owner",
    }
    with pytest.raises(ValueError, match="Claims must"):
        validate_document(
            document, {"synthetic-owner": {"role": "customer"}}, {"claims-a"}
        )


@pytest.mark.parametrize("missing", ["tier", "team"])
def test_classification_fails_closed(missing):
    document = {"kind": "policy", "tier": "public", "team": "claims-a"}
    document.pop(missing)
    with pytest.raises(ValueError):
        validate_document(document, {}, {"claims-a"})


def test_chunk_offsets_overlap_sections_and_determinism():
    text = (
        "# Synthetic café\n\n## Section one\n\n"
        + "evidence 水 " * 650
        + "\n## Section two\n\nshort text\n```\n# not heading\n```\n"
    )
    embedder = FakeEmbedder()
    chunks = chunk_document("synthetic", text, embedder)
    assert chunks == chunk_document("synthetic", text, embedder)
    assert all(chunk.text == text[chunk.start : chunk.end] for chunk in chunks)
    assert all("not heading" not in chunk.section for chunk in chunks)
    assert len({chunk.identifier for chunk in chunks}) == len(chunks)
    for previous, current in zip(chunks, chunks[1:], strict=False):
        if current.start < previous.end:
            assert current.section == previous.section
            assert len(embedder.offsets(text[current.start : previous.end])) == 48
    assert any("Section two" in chunk.section for chunk in chunks)


def test_fake_is_normalised_and_section_sensitive():
    embedder = FakeEmbedder()
    first, second = embedder.encode(
        ["Flood\nidentical content", "Theft\nidentical content"]
    )
    assert first != second
    assert sum(value * value for value in first) == pytest.approx(1)
    assert embedder.identity.startswith("synthetic-fake")


def test_chunk_ids_track_tokenizer_identity():
    embedder = FakeEmbedder()
    first = chunk_document("synthetic", "# Synthetic\n\nContent", embedder)
    embedder.identity = "different-tokenizer"
    second = chunk_document("synthetic", "# Synthetic\n\nContent", embedder)
    assert first[0].identifier != second[0].identifier


def test_ingestion_rejects_invalid_metadata_before_database(tmp_path):
    from rag_audit.ingestion import ingest

    manifest = generate(tmp_path)
    manifest["documents"][0].pop("tier")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="classification"):
        ingest(Mock(), tmp_path, FakeEmbedder())
