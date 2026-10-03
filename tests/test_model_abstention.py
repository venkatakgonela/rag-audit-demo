import json

import pytest
from test_answer_policy import chunk, payload
from test_answering import MemoryStore, run

from rag_audit.generation import FakeGenerator
from rag_audit.policy import VerificationError, verify
from rag_audit.settings import Settings


def test_explicit_abstention_is_empty_but_answer_is_verified():
    assert (
        verify(
            '{"outcome":"insufficient_evidence","statements":[]}', set(), [], Settings()
        )
        == []
    )
    assert verify(payload(), {"synthetic-chunk"}, [chunk()], Settings())


@pytest.mark.parametrize(
    "data",
    [
        {"outcome": "answer", "statements": []},
        {"outcome": "insufficient_evidence", "statements": [{}]},
        {"outcome": "other", "statements": []},
        {"outcome": None, "statements": []},
        {"outcome": [], "statements": []},
        {"outcome": "insufficient_evidence", "statements": None},
        {"outcome": "insufficient_evidence", "statements": {}, "extra": 0},
        {"statements": []},
        {"outcome": "answer"},
        {"outcome": "answer", "statements": [{}] * 6},
    ],
)
def test_malformed_outcome_combinations_fail(data):
    with pytest.raises(VerificationError):
        verify(json.dumps(data), {"synthetic-chunk"}, [chunk()], Settings())


@pytest.mark.parametrize(
    "text",
    [
        '{"outcome":"answer","outcome":"insufficient_evidence","statements":[]}',
        '{"outcome":"insufficient_evidence","statements":[]} extra',
        '{"outcome":"insufficient_evidence","statements":[],"extra":0}',
    ],
)
def test_abstention_json_strictness(text):
    with pytest.raises(VerificationError):
        verify(text, set(), [], Settings())


def test_abstention_envelope_and_trace_only_reason():
    store = MemoryStore()
    abstained = run(store=store, provider=FakeGenerator("abstain"))
    assert abstained == run(store=MemoryStore(chunks=[]))
    assert abstained == run(provider=FakeGenerator("malformed"))
    trace = store.traces[0][1]
    assert trace["reason"] == "model_abstained"
    assert trace["verification_reason"] is None
    assert trace["cited_ids"] == []
    assert trace["usage"]["output"] > 0
    assert "model_abstained" not in json.dumps(abstained)
