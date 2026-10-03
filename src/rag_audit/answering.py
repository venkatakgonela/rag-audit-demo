import asyncio
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime

from rag_audit.accounting import Price, estimate, preflight, validate_usage
from rag_audit.embeddings import Embedder
from rag_audit.gate import Gate
from rag_audit.generation import (
    RULE_SYSTEM,
    SYSTEM,
    Evidence,
    FakeGenerator,
    GenerationRequest,
    Generator,
)
from rag_audit.policy import (
    CONFIGURATION_VERSION,
    ECHO_VERSION,
    PROFILES,
    VerificationError,
    envelope,
    select_evidence,
    strict_json,
    verify,
)
from rag_audit.reranking import Reranker, rerank
from rag_audit.responses import BOUND_VERSION, MAX_INPUT_TOKENS, ResponsesProvider
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
        "verification_reason": None,
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
        "cost_basis": None,
        "input_bound": None,
        "bound_version": None,
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
    gate: Gate | None = None,
    reranker: Reranker | None = None,
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
            candidates = snapshot.chunks
            if gate is not None and gate.variant in ("V4a", "V4b"):
                if reranker is None:
                    raise ValueError("Reranker gate requires scoring model")
                started = clock()
                candidates = rerank(question, candidates, reranker)
                trace["reranker_duration"] = clock() - started
                trace["reranker_identity"] = reranker.identity
                trace["reranker_scores"] = [
                    {"id": chunk["id"], "score": chunk["reranker_score"]}
                    for chunk in candidates
                ]
            gate_started = clock()
            selected, skips = select_evidence(
                candidates,
                embedder.identity,
                settings,
                gate=gate,
                question=question,
            )
            trace["skips"] = skips
            trace["gate_duration"] = clock() - gate_started
            trace["profile_version"] = PROFILES[embedder.identity].version
            if gate is not None:
                trace["gate_configuration"] = asdict(gate)
        if selected or (choices and rephrase):
            real = isinstance(provider, ResponsesProvider)
            output_cap = (
                settings.generation_output_tokens if real else settings.output_units
            )
            seconds = settings.generation_seconds if real else settings.provider_seconds
            ceiling = (
                settings.generation_cost_ceiling if real else settings.cost_ceiling
            )
            trace["sent_ids"] = [chunk["id"] for chunk in selected]
            request = GenerationRequest(
                question,
                tuple(Evidence(chunk["id"], chunk["text"]) for chunk in selected),
                output_cap,
                seconds,
                CONFIGURATION_VERSION,
                choices,
                settings.answer_mode.value,
                system=RULE_SYSTEM if choices else SYSTEM,
            )
            trace["requested_provider"] = provider.identity
            trace["requested_model"] = provider.model
            expected_model = (
                provider.reported_model
                if isinstance(provider, ResponsesProvider)
                else provider.model
            )
            price = prices.get(expected_model)
            trace["price_version"] = price.version if price else None
            prompt_size = (
                len(provider.body(request))
                if isinstance(provider, ResponsesProvider)
                else len(request.serialized().encode())
            )
            input_bound = (
                provider.input_bound(request)
                if isinstance(provider, ResponsesProvider)
                else prompt_size
            )
            trace["input_bound"] = input_bound
            trace["bound_version"] = BOUND_VERSION if real else "synthetic_utf8_bytes"
            trace["cost_basis"] = price.source if price else None
            trace["reason"] = "provider_budget"
            if (
                prompt_size > settings.prompt_bytes
                or not isinstance(provider, (FakeGenerator, ResponsesProvider))
                or (
                    real
                    and (
                        price is None
                        or input_bound > MAX_INPUT_TOKENS
                        or price.cached_per_million is None
                        or price.cache_write_per_million is None
                    )
                )
                or (
                    price is not None
                    and (
                        price.unit
                        != ("provider_tokens" if real else "synthetic_utf8_bytes")
                        or not preflight(
                            input_bound,
                            output_cap,
                            price,
                            ceiling,
                        )
                    )
                )
            ):
                raise ValueError("Provider budget")
            started = clock()
            trace["reason"] = "provider_error"
            try:
                result = await asyncio.wait_for(provider.generate(request), seconds)
            finally:
                trace["durations"]["generate"] = clock() - started
            trace["reason"] = "provider_contract"
            validate_usage(result.usage)
            trace["usage"] = asdict(result.usage)
            if result.model == expected_model:
                trace["reported_provider"] = result.provider
                trace["reported_model"] = result.model
            cost = estimate(result.usage, prices.get(result.model))
            trace["cost_usd"] = str(cost) if cost is not None else None
            if (
                result.provider != provider.identity
                or result.model != expected_model
                or result.finish != "complete"
                or result.usage.unit
                != ("provider_tokens" if real else "synthetic_utf8_bytes")
                or result.usage.input is None
                or result.usage.output is None
                or result.usage.input > input_bound
                or (
                    result.usage.output
                    + (
                        0
                        if result.usage.reasoning_subset
                        else (result.usage.reasoning or 0)
                    )
                )
                > output_cap
                or (not real and result.usage.input != input_bound)
                or (not real and result.usage.output != len(result.payload.encode()))
                or (real and (result.usage.input > MAX_INPUT_TOKENS or cost is None))
                or len(result.payload.encode()) > settings.output_bytes
            ):
                raise ValueError("Provider contract")
            trace["reported_provider"] = result.provider
            trace["reported_model"] = result.model
            if cost is not None and cost > ceiling:
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
                    response = (
                        envelope(
                            "answered",
                            "\n".join(item["text"] for item in statements),
                            statements,
                        )
                        if statements
                        else envelope()
                    )
                    trace["cited_ids"] = [item["chunk_id"] for item in statements]
                    trace["reason"] = (
                        "citations_verified" if statements else "model_abstained"
                    )
            except VerificationError as error:
                trace["verification_reason"] = error.reason.value
                raise
            finally:
                trace["durations"]["verify"] = clock() - started
    except Exception:
        if trace["rule"] is not None:
            trace["reason"] = "rule_template_fallback"
        elif trace["reason"] == "verification_failed":
            response = envelope()
        else:
            response = envelope("error")
    return finalize(store, request_id, trace, response)
