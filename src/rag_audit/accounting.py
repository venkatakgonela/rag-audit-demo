from dataclasses import dataclass
from decimal import Decimal

from rag_audit.generation import Usage


@dataclass(frozen=True)
class Price:
    version: str
    input_per_million: Decimal
    output_per_million: Decimal
    cached_per_million: Decimal | None = None
    reasoning_per_million: Decimal | None = None
    unit: str = "synthetic_utf8_bytes"
    cache_write_per_million: Decimal | None = None
    source: str = "synthetic fixture prices"

    def __post_init__(self):
        for value in (
            self.input_per_million,
            self.output_per_million,
            self.cached_per_million,
            self.reasoning_per_million,
            self.cache_write_per_million,
        ):
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError("Invalid price")
        if not self.version:
            raise ValueError("Price version required")


def validate_usage(usage: Usage) -> None:
    for value in (
        usage.input,
        usage.output,
        usage.cached,
        usage.reasoning,
        usage.cache_write,
    ):
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError("Invalid usage")
    if any(
        type(flag) is not bool
        for flag in (
            usage.cached_subset,
            usage.reasoning_subset,
            usage.cache_write_subset,
        )
    ):
        raise ValueError("Invalid subset semantics")
    included = ((usage.cached or 0) if usage.cached_subset else 0) + (
        (usage.cache_write or 0) if usage.cache_write_subset else 0
    )
    if included and (usage.input is None or included > usage.input):
        raise ValueError("Invalid disjoint input subsets")
    if (
        usage.cached_subset
        and usage.cached is not None
        and (usage.input is None or usage.cached > usage.input)
    ):
        raise ValueError("Invalid cached subset")
    if (
        usage.reasoning_subset
        and usage.reasoning is not None
        and (usage.output is None or usage.reasoning > usage.output)
    ):
        raise ValueError("Invalid reasoning subset")


def estimate(usage: Usage, price: Price | None) -> Decimal | None:
    validate_usage(usage)
    if (
        price is None
        or usage.input is None
        or usage.output is None
        or price.unit != usage.unit
    ):
        return None
    cached = usage.cached or 0
    reasoning = usage.reasoning or 0
    writes = usage.cache_write or 0
    if usage.unit == "provider_tokens" and usage.input > 272000:
        raise ValueError("Unsupported input pricing tier")
    if writes and price.cache_write_per_million is None:
        return None
    if cached and price.cached_per_million is None:
        return None
    if reasoning and not usage.reasoning_subset and price.reasoning_per_million is None:
        return None
    amount = (
        Decimal(
            usage.input
            - (cached if usage.cached_subset else 0)
            - (writes if usage.cache_write_subset else 0)
        )
        * price.input_per_million
    )
    amount += Decimal(usage.output) * price.output_per_million
    amount += Decimal(cached) * (price.cached_per_million or Decimal(0))
    amount += Decimal(writes) * (price.cache_write_per_million or Decimal(0))
    if not usage.reasoning_subset:
        amount += Decimal(reasoning) * (price.reasoning_per_million or Decimal(0))
    return amount / Decimal(1000000)


def preflight(
    input_bound: int, output_bound: int, price: Price, ceiling: Decimal
) -> bool:
    if (
        input_bound < 0
        or output_bound < 0
        or (price.unit == "provider_tokens" and input_bound > 272000)
    ):
        return False
    input_rate = max(
        price.input_per_million,
        price.cached_per_million or Decimal(0),
        price.cache_write_per_million or Decimal(0),
    )
    output_rate = max(
        price.output_per_million, price.reasoning_per_million or Decimal(0)
    )
    return (
        Decimal(input_bound) * input_rate + Decimal(output_bound) * output_rate
    ) / Decimal(1000000) <= ceiling
