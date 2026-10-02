import os

from pydantic import SecretStr

from rag_audit.accounting import Price
from rag_audit.generation import FakeGenerator, Generator
from rag_audit.responses import ResponsesProvider
from rag_audit.settings import Settings


def configured_provider(settings: Settings) -> tuple[Generator, dict[str, Price]]:
    if settings.generation_backend == "fake":
        return FakeGenerator(), {}
    if (
        not settings.generation_base_url
        or not settings.generation_model
        or not settings.generation_reported_model
        or not settings.generation_key_env
        or not settings.generation_price_version
        or not settings.generation_price_source
        or settings.generation_input_price is None
        or settings.generation_cached_price is None
        or settings.generation_write_price is None
        or settings.generation_output_price is None
    ):
        raise ValueError("Incomplete provider configuration")
    key = os.environ.get(settings.generation_key_env)
    if not key:
        raise ValueError("Provider environment key unavailable")
    provider = ResponsesProvider(
        settings.generation_base_url,
        settings.generation_model,
        settings.generation_reported_model,
        SecretStr(key),
        settings.generation_reasoning_effort,
    )
    price = Price(
        settings.generation_price_version,
        settings.generation_input_price,
        settings.generation_output_price,
        settings.generation_cached_price,
        settings.generation_output_price,
        "provider_tokens",
        settings.generation_write_price,
        settings.generation_price_source,
    )
    return provider, {settings.generation_reported_model: price}
