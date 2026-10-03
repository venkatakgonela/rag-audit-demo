import math

import pytest

from rag_audit.evaluation.reranker_trial import grid
from rag_audit.gate import Gate
from rag_audit.reranking import probability, rerank


class FixedReranker:
    identity = "synthetic-pair-scorer"

    def score(self, question, chunk):
        return chunk.get("synthetic_score", 0.8)


def test_corrected_reranker_grid_and_replacement():
    assert len(grid()) == len(set(grid())) == 44
    assert sum(gate.variant == "V4a" for gate in grid()) == 11
    chunk = dict(
        cosine_similarity=0.45,
        keyword_score=0,
        keyword_rank=None,
        reranker_score=0.8,
        section="Synthetic",
        text="Synthetic query evidence.",
    )
    assert Gate("V4a", 0.8).accepts(chunk, "query")
    assert Gate("V4b", 0.8, 0.4).accepts(chunk, "query")
    assert not Gate("V4b", 0.8, 0.5).accepts(chunk, "query")
    assert not Gate("V1", 0.75).accepts(chunk, "query")
    chunk["reranker_score"] = None
    assert not Gate("V4a", 0.1).accepts(chunk, "query")


def test_sigmoid_is_stable_and_finite():
    assert probability(0) == 0.5
    assert probability(1000) == 1
    assert probability(-1000) == 0
    for value in (math.inf, -math.inf, math.nan):
        with pytest.raises(ValueError):
            probability(value)


def test_reranking_preserves_candidates_and_ties():
    chunks = [dict(id="second", text="original"), dict(id="first", text="original")]
    scored = rerank("query", chunks, FixedReranker())
    assert [chunk["id"] for chunk in scored] == ["first", "second"]
    assert all(chunk["text"] == "original" for chunk in scored)
    assert all("reranker_score" not in chunk for chunk in chunks)
    with pytest.raises(ValueError):
        rerank("query", chunks * 11, FixedReranker())
    with pytest.raises(ValueError):
        rerank("query", [dict(id="bad", synthetic_score=math.nan)], FixedReranker())
