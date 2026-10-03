import asyncio
import json
import socket
from dataclasses import replace
from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr
from test_answering import MemoryStore

from rag_audit.accounting import Price, estimate, preflight
from rag_audit.answering import ask
from rag_audit.embeddings import FakeEmbedder
from rag_audit.generation import Evidence, GenerationRequest, Usage
from rag_audit.provider_config import configured_provider
from rag_audit.responses import ProviderError, ResponsesProvider, parse_usage
from rag_audit.settings import Settings

SECRET = "synthetic-canary-key-not-a-real-credential"
MODEL = "synthetic-reported-model"
PRICE = Price(
    "synthetic-v1",
    Decimal(10),
    Decimal(50),
    Decimal(1),
    Decimal(50),
    "provider_tokens",
    Decimal("12.50"),
    "Synthetic list estimate, not billing",
)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Network forbidden in offline adapter tests")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def response(payload=None, **changes):
    if payload is None:
        payload = json.dumps(
            {
                "statements": [
                    {
                        "text": "Synthetic receipt evidence.",
                        "quote": "Synthetic receipt evidence.",
                        "chunk_id": "synthetic-chunk",
                    }
                ]
            }
        )
    return {
        "model": MODEL,
        "status": "completed",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 30,
            "total_tokens": 130,
            "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 10},
        },
        "output": [
            {"type": "reasoning"},
            {
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": payload}],
            },
        ],
        **changes,
    }


def provider(handler=None):
    return ResponsesProvider(
        "https://synthetic.invalid/v1",
        "synthetic-alias",
        MODEL,
        SecretStr(SECRET),
        transport=httpx.MockTransport(
            handler or (lambda request: httpx.Response(200, json=response()))
        ),
    )


def request(rule=False):
    return GenerationRequest(
        "synthetic receipts",
        (Evidence("synthetic-chunk", "Synthetic receipt evidence."),),
        2048,
        1,
        "synthetic-v1",
        ("Claim status: pending.",) if rule else (),
    )


def run(real, store=None, settings=None, prices=None):
    return asyncio.run(
        ask(
            store or MemoryStore(),
            "synthetic-customer-a",
            "receipts",
            FakeEmbedder(),
            real,
            settings or Settings(),
            prices={MODEL: PRICE} if prices is None else prices,
        )
    )


def test_strict_request_no_tools_and_usage_mapping():
    captured = []

    def handler(sent):
        captured.append(json.loads(sent.content))
        assert sent.headers["authorization"] == "Bearer " + SECRET
        return httpx.Response(200, json=response())

    real = provider(handler)
    result = asyncio.run(real.generate(request()))
    assert result.usage == Usage(100, 30, 0, 10, unit="provider_tokens", cache_write=0)
    body = captured[0]
    assert body["reasoning"] == {"effort": "medium"}
    assert body["max_output_tokens"] == 2048 and not body["stream"]
    assert "tools" not in body and "tool_choice" not in body
    assert body["text"]["format"]["strict"] is True
    assert not body["text"]["format"]["schema"]["additionalProperties"]
    assert real.input_bound(request()) == len(real.body(request())) + 1024
    assert set(
        json.loads(real.body(request(True)))["text"]["format"]["schema"]["properties"]
    ) == {"text"}
    assert SECRET not in repr(real)


def test_real_pipeline_accepts_expected_mapping_and_reports_cost():
    store = MemoryStore()
    assert run(provider(), store)["decision"] == "answered"
    trace = store.traces[0][1]
    assert trace["requested_model"] == "synthetic-alias"
    assert trace["reported_model"] == MODEL
    assert trace["cost_usd"] == "0.0025"
    assert "not billing" in trace["cost_basis"]


@pytest.mark.parametrize(
    "changes",
    [
        {"model": "synthetic-other"},
        {"status": "incomplete"},
        {"usage": None},
        {"output": []},
        {"status": "failed"},
        {"output": [{"type": "function_call"}]},
    ],
)
def test_contract_failures_do_not_answer(changes):
    store = MemoryStore()
    assert (
        run(provider(lambda _: httpx.Response(200, json=response(**changes))), store)[
            "decision"
        ]
        == "error"
    )
    assert not store.traces[0][1]["cited_ids"]


def test_incomplete_retains_usage_and_cost():
    store = MemoryStore()
    assert (
        run(
            provider(lambda _: httpx.Response(200, json=response(status="incomplete"))),
            store,
        )["decision"]
        == "error"
    )
    assert store.traces[0][1]["usage"]["reasoning"] == 10
    assert store.traces[0][1]["cost_usd"] == "0.0025"


@pytest.mark.parametrize(
    "payload",
    [
        "not JSON",
        '{"statements":[],"extra":true}',
        '{"statements":[{"text":"changed","quote":"changed","chunk_id":"synthetic-chunk"}]}',
        '{"statements":[],"statements":[]}',
    ],
)
def test_output_schema_rejected_by_unchanged_policy(payload):
    assert (
        run(provider(lambda _: httpx.Response(200, json=response(payload))))["decision"]
        == "no_answer"
    )


@pytest.mark.parametrize(
    "mode", ["http", "redirect", "timeout", "oversized", "malformed", "echo"]
)
def test_transport_errors_sanitized_no_retry(mode, caplog):
    calls = []

    def handler(sent):
        calls.append(1)
        if mode == "timeout":
            raise httpx.ReadTimeout(SECRET, request=sent)
        if mode in ("http", "redirect"):
            return httpx.Response(429 if mode == "http" else 302, text=SECRET)
        if mode == "oversized":
            return httpx.Response(200, content=b"x" * 131073)
        if mode == "malformed":
            return httpx.Response(200, text="invalid-json")
        return httpx.Response(200, json=response(SECRET))

    real = provider(handler)
    with pytest.raises(ProviderError) as error:
        asyncio.run(real.generate(request()))
    assert SECRET not in str(error.value)
    store = MemoryStore()
    assert run(real, store)["decision"] == "error"
    assert len(calls) == 2
    assert SECRET not in str(store.traces) + caplog.text


def test_price_missing_and_ceiling_prevent_dispatch():
    def forbidden(sent):
        raise AssertionError("Provider must not be called")

    real = provider(forbidden)
    for prices in ({}, {MODEL: replace(PRICE, cache_write_per_million=None)}):
        store = MemoryStore()
        assert run(real, store, prices=prices)["decision"] == "error"
        assert store.traces[0][1]["reason"] == "provider_budget"
    store = MemoryStore()
    assert (
        run(real, store, Settings(generation_cost_ceiling=Decimal(0)))["decision"]
        == "error"
    )
    assert store.traces[0][1]["reason"] == "provider_budget"


def test_usage_aliases_and_cache_write_arithmetic():
    raw = response()["usage"]
    raw["cached_read_tokens"] = 0
    raw["cache_write_tokens"] = raw["cached_write_tokens"] = 0
    assert parse_usage(raw).cached == 0
    raw["cached_read_tokens"] = 1
    with pytest.raises(ProviderError):
        parse_usage(raw)
    usage = Usage(100, 30, 20, 10, unit="provider_tokens", cache_write=5)
    assert estimate(usage, PRICE) == Decimal("0.0023325")
    assert estimate(replace(usage, reasoning_subset=False), PRICE) == Decimal(
        "0.0028325"
    )
    assert estimate(replace(usage, cache_write_subset=False), PRICE) == Decimal(
        "0.0023825"
    )
    assert estimate(usage, replace(PRICE, cache_write_per_million=None)) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"input_tokens": -1},
        {"output_tokens": True},
        {"total_tokens": 99},
        {"cached_write_tokens": 1},
        {"input_tokens_details": {"cached_tokens": 101}},
        {"output_tokens_details": {"reasoning_tokens": 31}},
    ],
)
def test_invalid_or_unverified_usage(changes):
    with pytest.raises(ValueError):
        parse_usage({**response()["usage"], **changes})


def test_input_tier_and_bound_guards():
    with pytest.raises(ValueError, match="tier"):
        estimate(Usage(272001, 1, unit="provider_tokens"), PRICE)
    assert estimate(Usage(272000, 1, unit="provider_tokens"), PRICE) is not None
    assert not preflight(272001, 1, PRICE, Decimal(100))
    raw = response()["usage"]
    raw.update(input_tokens=272001, total_tokens=272031)
    store = MemoryStore()
    assert (
        run(provider(lambda _: httpx.Response(200, json=response(usage=raw))), store)[
            "decision"
        ]
        == "error"
    )
    assert store.traces[0][1]["cost_usd"] is None
    raw.update(input_tokens=50000, total_tokens=50030)
    assert (
        run(provider(lambda _: httpx.Response(200, json=response(usage=raw))))[
            "decision"
        ]
        == "error"
    )


def test_environment_only_configuration(monkeypatch):
    settings = Settings(
        generation_backend="responses",
        generation_base_url="https://synthetic.invalid",
        generation_model="synthetic-alias",
        generation_reported_model=MODEL,
        generation_key_env="SYNTHETIC_TEST_KEY",
        generation_price_version="synthetic-v1",
        generation_price_source="Synthetic list estimate, not billing",
        generation_input_price=Decimal(10),
        generation_cached_price=Decimal(1),
        generation_write_price=Decimal("12.50"),
        generation_output_price=Decimal(50),
    )
    with pytest.raises(ValueError):
        configured_provider(settings)
    monkeypatch.setenv("SYNTHETIC_TEST_KEY", SECRET)
    real, prices = configured_provider(settings)
    assert prices[MODEL].unit == "provider_tokens"
    assert SECRET not in repr(real) + repr(settings)


def test_wrong_model_rejected_even_if_also_priced():
    real = provider(
        lambda _: httpx.Response(200, json=response(model="synthetic-other"))
    )
    assert (
        run(real, prices={MODEL: PRICE, "synthetic-other": PRICE})["decision"]
        == "error"
    )


def test_output_total_cap_and_cache_disjointness():
    raw = response()["usage"]
    raw.update(output_tokens=2049, total_tokens=2149)
    assert (
        run(provider(lambda _: httpx.Response(200, json=response(usage=raw))))[
            "decision"
        ]
        == "error"
    )
    with pytest.raises(ValueError):
        estimate(Usage(100, 10, 80, cache_write=30, unit="provider_tokens"), PRICE)


def test_deadline_cancels_http_work_without_retry():
    cancelled = []

    async def handler(sent):
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.append(True)
        return httpx.Response(200, json=response())

    real = provider(handler)
    with pytest.raises(ProviderError):
        asyncio.run(real.generate(replace(request(), timeout_seconds=0.01)))
    assert cancelled == [True]


def test_refusal_and_multiple_outputs_fail_closed():
    data = response()
    data["output"][1]["content"] = [{"type": "refusal", "refusal": "synthetic refusal"}]
    store = MemoryStore()
    assert (
        run(provider(lambda _: httpx.Response(200, json=data)), store)["decision"]
        == "error"
    )
    assert store.traces[0][1]["usage"]["output"] == 30
    data = response()
    data["output"].append(data["output"][1])
    assert (
        run(provider(lambda _: httpx.Response(200, json=data)))["decision"] == "error"
    )


def test_real_rule_rephrase_preserves_template():
    from rag_audit.rules import RuleResult

    rule = RuleResult("status", ("synthetic-claim-0",), {}, "pending", "v2")
    for text, expected in (
        ("Claim status: pending.", "rule_rephrased"),
        ("Claim status: paid.", "rule_template_fallback"),
    ):
        store = MemoryStore(rule=rule)
        real = provider(
            lambda _, text=text: httpx.Response(
                200, json=response(json.dumps({"text": text}))
            )
        )
        result = asyncio.run(
            ask(
                store,
                "synthetic-customer-a",
                "status synthetic-claim-0",
                FakeEmbedder(),
                real,
                Settings(),
                prices={MODEL: PRICE},
                rephrase=True,
            )
        )
        assert result["text"] == "Claim status: pending."
        assert store.traces[0][1]["reason"] == expected


def test_trace_failure_discards_real_answer():
    assert run(provider(), MemoryStore(fail_trace=True))["decision"] == "error"
