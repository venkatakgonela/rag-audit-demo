import math
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from rag_audit.evaluation.reranker_trial import grid
from rag_audit.gate import Gate
from rag_audit.reranking import OnnxReranker, probability, rerank


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


@pytest.mark.parametrize("length", [512, 513])
def test_onnx_pair_limit_never_truncates_or_batches(length):
    model = object.__new__(OnnxReranker)
    encoded = SimpleNamespace(
        ids=list(range(length)), attention_mask=[1] * length, type_ids=[0] * length
    )
    model.tokenizer = MagicMock()
    model.tokenizer.encode.return_value = encoded
    model.np = MagicMock()
    model.np.array.side_effect = lambda values, dtype: values
    output = MagicMock()
    output.shape = (1, 1)
    output.__getitem__.return_value = 0.0
    model.session = MagicMock()
    model.session.run.return_value = [output]
    score = model.score("question", dict(section="Synthetic", text="passage"))
    model.tokenizer.encode.assert_called_once_with("question", "Synthetic\npassage")
    if length == 513:
        assert score is None
        model.session.run.assert_not_called()
        model.np.array.assert_not_called()
    else:
        assert score == 0.5
        model.session.run.assert_called_once_with(
            None,
            dict(
                input_ids=[encoded.ids],
                attention_mask=[encoded.attention_mask],
                token_type_ids=[encoded.type_ids],
            ),
        )
        assert all(
            call.kwargs == {"dtype": "int64"} for call in model.np.array.call_args_list
        )


@pytest.mark.parametrize("shape, value", [((1, 2), 0), ((1, 1), math.nan)])
def test_onnx_bad_output_fails_closed(shape, value):
    model = object.__new__(OnnxReranker)
    model.tokenizer = MagicMock()
    model.tokenizer.encode.return_value = SimpleNamespace(
        ids=[1], attention_mask=[1], type_ids=[0]
    )
    model.np = MagicMock()
    output = MagicMock()
    output.shape = shape
    output.__getitem__.return_value = value
    model.session = MagicMock()
    model.session.run.return_value = [output]
    with pytest.raises(ValueError):
        model.score("question", dict(section="Synthetic", text="passage"))


def test_unscorable_candidates_sort_last_and_remain_ineligible():
    chunks: list[dict] = [
        dict(id="unscorable", synthetic_score=None),
        dict(id="selected"),
    ]
    scored = rerank("question", chunks, FixedReranker())
    assert [chunk["id"] for chunk in scored] == ["selected", "unscorable"]
    assert not Gate("V4a", 0.1).accepts(
        {**scored[-1], "cosine_similarity": 1.0, "keyword_score": 1.0}, "question"
    )
