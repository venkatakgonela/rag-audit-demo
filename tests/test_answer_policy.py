import json

import pytest

from rag_audit.embeddings import FakeEmbedder
from rag_audit.policy import PROFILES, select_evidence, strict_json, verify
from rag_audit.settings import Settings


def chunk(text="Synthetic receipt evidence.", identifier="synthetic-chunk"):
    return {
        "id": identifier,
        "text": text,
        "section": "Synthetic evidence",
        "start_offset": 0,
        "end_offset": len(text),
        "document_id": "synthetic-faq-0",
        "cosine_similarity": 0.8,
        "keyword_score": 0.1,
        "keyword_rank": 1,
    }


def payload(
    quote="Synthetic receipt evidence.", identifier="synthetic-chunk", **fields
):
    return json.dumps(
        {
            "outcome": "answer",
            "statements": [
                {"text": quote, "quote": quote, "chunk_id": identifier, **fields}
            ],
        }
    )


def test_exact_authorised_citation():
    result = verify(payload(), {"synthetic-chunk"}, [chunk()], Settings())
    assert result[0]["text"] == "Synthetic receipt evidence."
    assert result[0]["start_offset"] == 0


@pytest.mark.parametrize(
    "authorised,sent",
    [(set(), [chunk()]), ({"synthetic-chunk"}, []), ({"synthetic-other"}, [chunk()])],
)
def test_request_and_sent_membership_are_both_required(authorised, sent):
    with pytest.raises(ValueError):
        verify(payload(), authorised, sent, Settings())


@pytest.mark.parametrize(
    "quote",
    [
        "",
        "  ",
        "synthetic receipt evidence.",
        "Synthetic  receipt evidence.",
        "Synthetic receipt evidence!",
        "Café",
        "line\nnext",
    ],
)
def test_exact_substring_no_normalization(quote):
    with pytest.raises(ValueError):
        verify(
            payload(quote),
            {"synthetic-chunk"},
            [chunk("Synthetic receipt evidence. Cafe\u0301 line\r\nnext")],
            Settings(),
        )


@pytest.mark.parametrize("quote", ["Synthetic receipt", "Cafe\u0301", "line\r\nnext"])
def test_exact_substring_unicode_crlf_pass(quote):
    assert verify(
        payload(quote),
        {"synthetic-chunk"},
        [chunk("Synthetic receipt evidence. Cafe\u0301 line\r\nnext")],
        Settings(),
    )


@pytest.mark.parametrize(
    "bad",
    [
        '{"statements":[]}',
        '{"statements":[],"extra":1}',
        '{"statements":[{"text":4,"quote":"x","chunk_id":"synthetic-chunk"}]}',
        '{"statements":null}',
        '{"statements":[],"statements":[]}',
        payload(text="Unsupported paraphrase"),
        payload(extra="untrusted"),
        payload("x" * 2049),
        "x" * 16385,
    ],
)
def test_schema_and_output_limits(bad):
    with pytest.raises(ValueError):
        verify(bad, {"synthetic-chunk"}, [chunk()], Settings())


def test_one_bad_statement_rejects_all_and_duplicates_rejected():
    data = json.loads(payload())
    data["statements"].append(json.loads(payload("altered"))["statements"][0])
    with pytest.raises(ValueError):
        verify(json.dumps(data), {"synthetic-chunk"}, [chunk()], Settings())
    data["statements"][1] = data["statements"][0]
    with pytest.raises(ValueError):
        verify(json.dumps(data), {"synthetic-chunk"}, [chunk()], Settings())


def test_instruction_echo_and_benign_false_positive():
    benign = "Synthetic guidance says retain receipts."
    assert verify(payload(benign), {"synthetic-chunk"}, [chunk(benign)], Settings())
    for phrase in ("ignore previous instructions", "<|system|>", "reveal all claims"):
        text = f"Synthetic training discusses the phrase {phrase} as an attack."
        with pytest.raises(ValueError, match="Instruction echo"):
            verify(payload(text), {"synthetic-chunk"}, [chunk(text)], Settings())


@pytest.mark.parametrize("model,profile", list(PROFILES.items()))
def test_profile_boundaries(model, profile):
    source = chunk()
    for cosine, expected in [
        (profile.cosine_floor - 0.0001, False),
        (profile.cosine_floor, True),
        (1.0, True),
        (float("nan"), False),
        (float("inf"), False),
    ]:
        source["cosine_similarity"] = cosine
        assert bool(select_evidence([source], model, Settings())[0]) is expected
    source["cosine_similarity"] = 1
    for keyword, rank in [(0, 1), (0.1, None), (float("nan"), 1)]:
        source.update(keyword_score=keyword, keyword_rank=rank)
        expected = profile.variant == "V1" and keyword == keyword
        assert bool(select_evidence([source], model, Settings())[0]) is expected
    with pytest.raises(ValueError):
        select_evidence([], "unknown", Settings())


def test_calibrated_real_profile_and_untuned_fake_profile():
    real = next(
        profile
        for identity, profile in PROFILES.items()
        if identity != FakeEmbedder.identity
    )
    assert (real.version, real.variant, real.cosine_floor) == (
        "local-calibrated-v1",
        "V1",
        0.75,
    )
    fake = PROFILES[FakeEmbedder.identity]
    assert (fake.version, fake.variant, fake.cosine_floor) == (
        "fake-demo-v1",
        "V0",
        0.15,
    )


def test_whole_chunk_skip_continue_utf8_and_count_budget():
    settings = Settings(evidence_bytes=4, context_chunks=1)
    selected, skips = select_evidence(
        [chunk("ééé"), chunk("éé", "fits"), chunk("", "extra")],
        FakeEmbedder.identity,
        settings,
    )
    assert [item["id"] for item in selected] == ["fits"]
    assert skips == ["whole_chunk_budget_skip", "chunk_count_skip"]
    assert settings.answer_mode.value == "extractive"
    assert Settings().evidence_bytes == 12288


def test_strict_json_nonfinite_and_duplicate():
    for raw in ('{"x":NaN}', '{"x":1,"x":2}'):
        with pytest.raises(ValueError):
            strict_json(raw)
