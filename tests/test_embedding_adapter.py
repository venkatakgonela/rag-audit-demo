import os
from pathlib import Path

import pytest

from rag_audit.embeddings import MODEL, REVISION, OnnxEmbedder


@pytest.mark.model
def test_real_offsets_section_signals_and_query_instruction():
    directory = os.environ.get("SYNTHETIC_MODEL_DIRECTORY")
    if not directory:
        pytest.skip("Set SYNTHETIC_MODEL_DIRECTORY for explicit real-model smoke")
    model = OnnxEmbedder(Path(directory))
    text = "Synthetic café 水 damage."
    offsets = model.offsets(text)
    assert any(text[start:end] == "水" for start, end in offsets)
    vectors = model.encode(
        ["Flood cover\nidentical content", "Theft cover\nidentical content"]
    )
    assert len(vectors[0]) == 384
    assert sum(value * value for value in vectors[0]) == pytest.approx(1, abs=1e-5)
    assert vectors[0] != vectors[1]
    assert model.encode([text], query=True) != model.encode([text])
    with pytest.raises(ValueError, match="token limit"):
        model.encode(["water " * 1000])


def test_model_metadata_constants():
    assert MODEL == "BAAI/bge-small-en-v1.5"
    assert len(REVISION) == 40
    assert OnnxEmbedder.identity.endswith(":section-v1")
