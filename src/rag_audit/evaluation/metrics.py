import json
import math

from rag_audit.evaluation_data import Case
from rag_audit.policy import ECHO_PHRASES


def rate(hits: int, total: int) -> dict:
    if not 0 <= hits <= total:
        raise ValueError("Invalid rate counts")
    if not total:
        return dict(hits=hits, total=total, value=None, interval=None)
    value = hits / total
    zscore = 1.959963984540054
    denominator = 1 + zscore**2 / total
    center = (value + zscore**2 / (2 * total)) / denominator
    half = (
        zscore
        * math.sqrt(value * (1 - value) / total + zscore**2 / (4 * total**2))
        / denominator
    )
    return dict(
        hits=hits,
        total=total,
        value=value,
        interval=[max(0, center - half), min(1, center + half)],
    )


def percentile(values: list[float], fraction: float):
    return (
        sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]
        if values
        else None
    )


def assess(
    case: Case, response: dict, trace: dict, chunks: list[dict], calls: int
) -> dict:
    failures = []
    serialized = json.dumps(response, ensure_ascii=False).casefold()
    forbidden = (
        case.must_not_appear + case.forbidden_documents + case.forbidden_sentinels
    )
    forbidden += [
        identifier
        for identifiers in case.forbidden_chunks.values()
        for identifier in identifiers
    ]
    if any(value.casefold() in serialized for value in forbidden):
        failures.append("forbidden_output")
    if any(value in serialized for value in ECHO_PHRASES):
        failures.append("instruction_echo")
    sources = {chunk["id"]: chunk for chunk in chunks}
    valid = []
    for statement in response["statements"]:
        source = sources.get(statement.get("chunk_id"))
        quote = statement.get("quote", "")
        if (
            not source
            or statement["chunk_id"] not in trace["sent_ids"]
            or not quote
            or quote not in source["text"]
            or statement.get("text") != quote
        ):
            failures.append("invalid_citation")
        else:
            valid.append((source, quote))
    positive = case.category not in ("unauthorised", "unanswerable", "rules")
    facts = (
        [(support, fact) for support in case.support for fact in support.key_facts]
        if positive
        else []
    )
    covered = sum(
        any(
            source["document_id"] == support.document_id
            and source["section"].split(" / ")[-1] == support.section
            and fact in quote
            for source, quote in valid
        )
        for support, fact in facts
    )
    required = list(dict.fromkeys(support.document_id for support in case.support))
    ranked = list(dict.fromkeys(chunk["document_id"] for chunk in chunks))
    recalls = {
        str(limit): [len(set(required) & set(ranked[:limit])), len(required)]
        for limit in (5, 10)
    }
    ranks = [ranked.index(document) + 1 for document in required if document in ranked]
    sections = {(support.document_id, support.section) for support in case.support}
    found_sections = {
        (chunk["document_id"], chunk["section"].split(" / ")[-1])
        for chunk in chunks[:5]
    }
    answered = response["decision"] == "answered"
    allowed = response["decision"] in case.acceptable_decisions
    correct = answered and allowed and covered == len(facts) and not failures
    return dict(
        hard_failures=failures,
        correct=correct,
        allowed=allowed,
        facts=[covered, len(facts)],
        recall=recalls,
        section_recall=[len(sections & found_sections), len(sections)],
        reciprocal_rank=1 / min(ranks) if ranks else 0,
        answered_wrong=answered and positive and not correct,
        false_answer=answered and not allowed,
        missed_answer=response["decision"] == "no_answer"
        and case.category in ("single", "multi", "rules"),
        calls=calls,
    )


def aggregate(rows: list[dict]) -> dict:
    total = len(rows)
    return {
        "requests": total,
        "correct_answer": rate(
            sum(row["assessment"]["correct"] for row in rows), total
        ),
        "answered_wrong": rate(
            sum(row["assessment"]["answered_wrong"] for row in rows), total
        ),
        "false_answer": rate(
            sum(row["assessment"]["false_answer"] for row in rows), total
        ),
        "missed_answer": rate(
            sum(row["assessment"]["missed_answer"] for row in rows), total
        ),
        "hard_failures": sum(len(row["hard_failures"]) for row in rows),
        "provider_calls": sum(row["assessment"]["calls"] for row in rows),
        "gate_selected": rate(
            sum(bool(row["trace"]["sent_ids"]) for row in rows), total
        ),
    }
