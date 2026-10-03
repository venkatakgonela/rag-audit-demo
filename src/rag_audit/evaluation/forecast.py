from dataclasses import replace
from decimal import Decimal

from pydantic import SecretStr

from rag_audit.generation import Evidence, GenerationRequest
from rag_audit.responses import ResponsesProvider


def forecast(rows: list[dict], settings) -> dict:
    provider = ResponsesProvider(
        settings.generation_base_url,
        settings.generation_model,
        settings.generation_reported_model,
        SecretStr("forecast-only"),
        settings.generation_reasoning_effort,
    )
    reservations = []
    for primary in rows:
        for row in (primary, primary.get("counterfactual")):
            if row is None:
                continue
            for raw in row.get("generation_requests", []):
                raw = dict(raw)
                raw["evidence"] = tuple(Evidence(**item) for item in raw["evidence"])
                raw["templates"] = tuple(raw["templates"])
                request = replace(
                    GenerationRequest(**raw),
                    max_output_units=settings.generation_output_tokens,
                    timeout_seconds=settings.generation_seconds,
                )
                bound = provider.input_bound(request)
                reserve = (
                    Decimal(bound) * Decimal("12.5")
                    + Decimal(request.max_output_units) * 50
                ) / 1000000
                reservations.append(
                    dict(
                        case=row["case"],
                        style=row["style"],
                        counterfactual=row is not primary,
                        input_bound=bound,
                        reservation=str(reserve),
                    )
                )
    total = sum((Decimal(row["reservation"]) for row in reservations), Decimal(0))
    return dict(
        provider_calls=len(reservations),
        conservative_total=str(total),
        cap_shortfall=str(max(Decimal(0), total - 3)),
        reservations=reservations,
        basis="Operator list prices; conservative estimates, not billing.",
    )
