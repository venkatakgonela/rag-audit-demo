import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from rag_audit.chunking import chunk_document
from rag_audit.corpus import validate_sources
from rag_audit.embeddings import FakeEmbedder


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Phrasing(StrictModel):
    style: Literal["keyword", "natural"]
    text: str = Field(min_length=1)


class Support(StrictModel):
    document_id: str
    section: str
    key_facts: list[str] = Field(min_length=1)


class RuleLabel(StrictModel):
    operation: Literal["status", "payout", "eligibility"]
    value: str
    status: str | None


class Case(StrictModel):
    id: str
    split: Literal["dev", "test"]
    subject: str
    category: Literal[
        "single", "multi", "unanswerable", "unauthorised", "rules", "injection"
    ]
    information_need: str = Field(min_length=20)
    phrasings: list[Phrasing]
    expected_decision: Literal["answered", "no_answer"]
    scope: str
    support: list[Support]
    forbidden_documents: list[str]
    forbidden_chunks: dict[str, list[str]]
    forbidden_sentinels: list[str]
    expected_rule: RuleLabel | None
    absent_phrasings: list[str]
    missing_terms: list[str]
    rationale: str = Field(min_length=20)
    fact_group: str
    labeller: str
    label_date: str
    label_status: Literal["drafted", "reviewed"]


class Golden(StrictModel):
    version: Literal[1]
    cases: list[Case]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def semantic_cases(golden: dict) -> list[dict]:
    return [
        {key: value for key, value in case.items() if key != "label_status"}
        for case in golden["cases"]
    ]


def freeze_digests(root: Path) -> dict[str, str]:
    directory = root / "datasets/evaluation"
    cases = semantic_cases(read_json(directory / "golden.json"))
    return {
        "corpus": digest(read_json(root / "datasets/corpus-v3/manifest.json")),
        "access": digest(read_json(directory / "access-intent.json")),
        "chunks": digest(read_json(directory / "chunk-references.json")),
        "cases": digest(cases),
        "test": digest([case for case in cases if case["split"] == "test"]),
    }


def check_dataset(root: Path, *, frozen: bool = True) -> dict:
    corpus = root / "datasets/corpus-v3"
    directory = root / "datasets/evaluation"
    manifest = read_json(corpus / "manifest.json")
    validate_sources(corpus, manifest)
    golden = Golden.model_validate(read_json(directory / "golden.json"))
    access = read_json(directory / "access-intent.json")
    index = read_json(directory / "chunk-references.json")
    documents = {document["id"]: document for document in manifest["documents"]}
    texts = {
        identifier: (corpus / document["path"]).read_text()
        for identifier, document in documents.items()
    }
    subjects = set(access["subjects"])
    assert subjects == {user["subject"] for user in manifest["users"]}
    visibility = {
        entry["document_id"]: set(entry["allowed_subjects"])
        for entry in access["documents"]
    }
    assert len(visibility) == len(access["documents"]) == 72
    assert set(visibility) == set(documents)
    assert all(allowed and allowed <= subjects for allowed in visibility.values())
    assert Counter(document["kind"] for document in documents.values()) == {
        "policy": 12,
        "handling": 12,
        "faq": 12,
        "underwriting": 12,
        "guide": 8,
        "claim": 16,
    }
    assert Counter(document["tier"] for document in documents.values()) == {
        "public": 36,
        "internal": 12,
        "broker": 8,
        "restricted": 16,
    }
    assert len(index["profiles"]) == 2
    profile_chunks = {}
    for profile in index["profiles"]:
        chunks = {item["id"]: item for item in profile["chunks"]}
        assert len(chunks) == len(profile["chunks"])
        for item in chunks.values():
            text = texts[item["document_id"]]
            assert item["source_hash"] == hashlib.sha256(text.encode()).hexdigest()
            content = text[item["start"] : item["end"]]
            assert content and item["start"] >= 0 and item["end"] <= len(text)
            expected = hashlib.sha256(
                (
                    f"v1:384:480:48:{profile['identity']}:{item['source_hash']}:"
                    f"{item['document_id']}:{item['section']}:{item['start']}:{item['end']}:{content}"
                ).encode()
            ).hexdigest()
            assert item["id"] == expected
        if profile["identity"] == FakeEmbedder.identity:
            expected_ids = {
                chunk.identifier
                for identifier, text in texts.items()
                for chunk in chunk_document(identifier, text, FakeEmbedder())
            }
            assert set(chunks) == expected_ids
        profile_chunks[profile["identity"]] = chunks
    assert len(profile_chunks) == 2 and FakeEmbedder.identity in profile_chunks
    assert Counter(case.category for case in golden.cases) == {
        "single": 20,
        "multi": 8,
        "unanswerable": 10,
        "unauthorised": 10,
        "rules": 6,
        "injection": 6,
    }
    expected_test = {
        "single": 7,
        "multi": 3,
        "unanswerable": 3,
        "unauthorised": 3,
        "rules": 2,
        "injection": 2,
    }
    assert (
        Counter(case.category for case in golden.cases if case.split == "test")
        == expected_test
    )
    assert len({case.id for case in golden.cases}) == 60
    assert all(
        {case.subject for case in golden.cases if case.split == split} == subjects
        for split in ("dev", "test")
    )
    questions = set()
    fact_splits: dict[tuple[str, str], str] = {}
    group_splits: dict[str, str] = {}
    for case in golden.cases:
        assert case.subject in subjects
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", case.label_date)
        assert len(case.phrasings) == 2 and {item.style for item in case.phrasings} == {
            "keyword",
            "natural",
        }
        for phrasing in case.phrasings:
            normalized = " ".join(phrasing.text.casefold().split())
            assert normalized not in questions
            questions.add(normalized)
            if (
                case.category in ("single", "multi", "rules")
                and case.scope != "all products and editions"
            ):
                assert case.scope.casefold() in phrasing.text.casefold()
        expected = (
            "answered" if case.category in ("single", "multi", "rules") else "no_answer"
        )
        assert case.expected_decision == expected
        assert bool(case.support) == (case.category != "unanswerable")
        assert len(case.support) == 1 if case.category == "single" else True
        assert (
            len({item.document_id for item in case.support}) >= 2
            if case.category == "multi"
            else True
        )
        group_splits.setdefault(case.fact_group, case.split)
        assert group_splits[case.fact_group] == case.split
        for support in case.support:
            assert support.document_id in documents
            assert f"## {support.section}\n" in texts[support.document_id]
            passage = (
                texts[support.document_id]
                .split(f"## {support.section}\n", 1)[1]
                .split("\n## ", 1)[0]
            )
            assert (case.subject in visibility[support.document_id]) == (
                case.category != "unauthorised"
            )
            for fact in support.key_facts:
                assert fact and fact in passage
                key = (support.document_id, fact)
                fact_splits.setdefault(key, case.split)
                assert fact_splits[key] == case.split
        if case.category == "multi":
            facts = [fact for support in case.support for fact in support.key_facts]
            assert not any(
                all(fact in text for fact in facts) for text in texts.values()
            )
        assert (
            set(case.forbidden_chunks) == set(profile_chunks)
            if case.forbidden_documents
            else not case.forbidden_chunks
        )
        for identifier in case.forbidden_documents:
            assert (
                identifier in documents and case.subject not in visibility[identifier]
            )
        for profile, identifiers in case.forbidden_chunks.items():
            expected_ids = {
                identifier
                for identifier, item in profile_chunks[profile].items()
                if item["document_id"] in case.forbidden_documents
            }
            assert set(identifiers) == expected_ids and identifiers
        for sentinel in case.forbidden_sentinels:
            assert any(
                sentinel in texts[identifier] for identifier in case.forbidden_documents
            )
            assert not any(
                sentinel in text
                for identifier, text in texts.items()
                if case.subject in visibility[identifier]
            )
        if case.category == "unauthorised":
            assert len(case.absent_phrasings) == 2 and case.forbidden_documents
        if case.category == "unanswerable":
            assert case.missing_terms
            assert not any(
                term.casefold() in text.casefold()
                for term in case.missing_terms
                for identifier, text in texts.items()
                if case.subject in visibility[identifier]
            )
        assert (case.expected_rule is not None) == (case.category == "rules")
    if frozen:
        freeze = read_json(directory / "freeze.json")
        assert freeze["state"] in ("candidate-awaiting-acceptance", "accepted")
        assert freeze["digests"] == freeze_digests(root)
    return {
        "documents": len(documents),
        "cases": len(golden.cases),
        "phrasings": len(questions),
        "hidden_documents": {
            subject: sum(subject not in allowed for allowed in visibility.values())
            for subject in sorted(subjects)
        },
    }
