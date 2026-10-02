import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime

from rag_audit.accounting import Price, estimate, preflight, validate_usage
from rag_audit.embeddings import Embedder
from rag_audit.generation import Evidence, FakeGenerator, GenerationRequest, Generator
from rag_audit.policy import (
    CONFIGURATION_VERSION,
    ECHO_VERSION,
    PROFILES,
    envelope,
    select_evidence,
    strict_json,
    verify,
)
from rag_audit.routing import route
from rag_audit.rules import templates
from rag_audit.settings import Settings
from rag_audit.store import Store


def new_trace() -> dict:
    return {
        "subject": None,
        "role": None,
        "question": None,
        "decision": "error",
        "reason": "request_invalid",
        "rule": None,
        "retrieved_ids": [],
        "sent_ids": [],
        "cited_ids": [],
        "signals": [],
        "skips": [],
        "durations": {
            name: 0.0 for name in ("route", "retrieve", "generate", "verify")
        },
        "usage": None,
        "requested_provider": None,
        "requested_model": None,
        "reported_provider": None,
        "reported_model": None,
        "cost_usd": None,
        "price_version": None,
        "corpus_version": None,
        "embedding_identity": None,
        "configuration_version": CONFIGURATION_VERSION,
        "profile_version": None,
        "instruction_echo_version": ECHO_VERSION,
        "answer_mode": "extractive",
    }


def finalize(store: Store, request_id: str, trace: dict, response: dict) -> dict:
    trace["decision"] = response["decision"]
    try:
        store.trace(request_id, trace)
    except Exception:
        return envelope("error")
    return response


async def ask(
    store: Store,
    subject: str,
    question: str,
    embedder: Embedder,
    provider: Generator | None = None,
    settings: Settings | None = None,
    *,
    rephrase: bool = False,
    prices: dict[str, Price] | None = None,
    clock: Callable[[], float] = time.monotonic,
    id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
    timestamp: Callable[[], str] = lambda: datetime.now(UTC).isoformat(),
) -> dict:
    trace = new_trace()
    request_id = id_factory()
    trace["timestamp"] = timestamp()
    response = envelope("error")
    provider = provider or FakeGenerator()
    prices = prices or {}
    try:
        settings = settings or Settings()
        if (
            type(question) is not str
            or not question.strip()
            or len(question) > settings.question_characters
        ):
            raise ValueError("Invalid question")
        trace["question"] = question
        started = clock()
        routed = route(question)
        trace["durations"]["route"] = clock() - started
        started = clock()
        trace["reason"] = "snapshot_error"
        snapshot = store.snapshot(subject, question, routed, embedder)
        trace["durations"]["retrieve"] = clock() - started
        trace.update(
            subject=snapshot.identity.subject,
            role=snapshot.identity.role,
            corpus_version=snapshot.corpus_version,
            embedding_identity=snapshot.model_identity,
        )
        trace["retrieved_ids"] = [chunk["id"] for chunk in snapshot.chunks]
        trace["signals"] = [
            {
                key: chunk[key]
                for key in ("id", "cosine_similarity", "keyword_score", "keyword_rank")
            }
            for chunk in snapshot.chunks
        ]
        trace["reason"] = "no_eligible_evidence"
        response = envelope()
        choices: tuple[str, ...] = templates(snapshot.rule) if snapshot.rule else ()
        selected: list[dict]
        if snapshot.rule:
            rule = asdict(snapshot.rule)
            trace["rule"] = rule
            response = envelope("answered", choices[0], rule=rule)
            trace["reason"] = "rule_template"
            selected = []
        else:
            selected, skips = select_evidence(
                snapshot.chunks, embedder.identity, settings
            )
            trace["skips"] = skips
            trace["profile_version"] = PROFILES[embedder.identity].version
        if selected or (choices and rephrase):
            trace["sent_ids"] = [chunk["id"] for chunk in selected]
            request = GenerationRequest(
                question,
                tuple(Evidence(chunk["id"], chunk["text"]) for chunk in selected),
                settings.output_units,
                settings.provider_seconds,
                CONFIGURATION_VERSION,
                choices,
                settings.answer_mode.value,
            )
            trace["requested_provider"] = provider.identity
            trace["requested_model"] = provider.model
            price = prices.get(provider.model)
            trace["price_version"] = price.version if price else None
            input_bound = len(request.serialized().encode())
            trace["reason"] = "provider_budget"
            if (
                input_bound > settings.prompt_bytes
                or not isinstance(provider, FakeGenerator)
                or (
                    price is not None
                    and (
                        price.unit != "synthetic_utf8_bytes"
                        or not preflight(
                            input_bound,
                            settings.output_units,
                            price,
                            settings.cost_ceiling,
                        )
                    )
                )
            ):
                raise ValueError("Provider budget")
            started = clock()
            trace["reason"] = "provider_error"
            try:
                result = await asyncio.wait_for(
                    provider.generate(request), settings.provider_seconds
                )
            finally:
                trace["durations"]["generate"] = clock() - started
            trace["reason"] = "provider_contract"
            validate_usage(result.usage)
            trace["usage"] = asdict(result.usage)
            cost = estimate(result.usage, prices.get(result.model))
            trace["cost_usd"] = str(cost) if cost is not None else None
            if (
                result.provider != provider.identity
                or result.model != provider.model
                or result.finish != "complete"
                or result.usage.unit != "synthetic_utf8_bytes"
                or result.usage.input is None
                or result.usage.output is None
                or result.usage.input > input_bound
                or result.usage.output > settings.output_units
                or result.usage.input != input_bound
                or result.usage.output != len(result.payload.encode())
                or len(result.payload.encode()) > settings.output_bytes
            ):
                raise ValueError("Provider contract")
            trace["reported_provider"] = result.provider
            trace["reported_model"] = result.model
            if cost is not None and cost > settings.cost_ceiling:
                raise ValueError("Reported cost exceeds ceiling")
            started = clock()
            trace["reason"] = "verification_failed"
            try:
                if choices:
                    data = strict_json(result.payload)
                    if (
                        type(data) is not dict
                        or set(data) != {"text"}
                        or data["text"] not in choices
                    ):
                        raise ValueError("Rule rephrase mismatch")
                    response["text"] = data["text"]
                    trace["reason"] = "rule_rephrased"
                else:
                    statements = verify(
                        result.payload, set(trace["retrieved_ids"]), selected, settings
                    )
                    response = envelope(
                        "answered",
                        "\n".join(item["text"] for item in statements),
                        statements,
                    )
                    trace["cited_ids"] = [item["chunk_id"] for item in statements]
                    trace["reason"] = "citations_verified"
            finally:
                trace["durations"]["verify"] = clock() - started
    except Exception:
        if trace["rule"] is not None:
            trace["reason"] = "rule_template_fallback"
        else:
            response = envelope("error")
    return finalize(store, request_id, trace, response)
