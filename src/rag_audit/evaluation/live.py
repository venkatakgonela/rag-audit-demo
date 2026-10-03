import base64
import hashlib
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import httpx

from rag_audit.accounting import estimate
from rag_audit.evaluation.data import append_event
from rag_audit.provider_config import configured_provider
from rag_audit.responses import (
    INPUT_MARGIN,
    MAX_RESPONSE_BYTES,
    ResponsesProvider,
    parse_usage,
)


class Ledger:
    def __init__(self, path: Path, forecast: dict, cap: Decimal = Decimal("3.00")):
        if path.exists():
            raise ValueError("Live ledger already exists; no automatic second run")
        self.path = path
        self.cap = cap
        self.total = Decimal(0)
        self.stopped = False
        append_event(path, dict(event="forecast", cap=str(cap), **forecast))

    def reserve(self, bound: int, output: int, request_hash: str) -> Decimal:
        if bound < 0 or output < 0:
            raise ValueError("Invalid reservation bound")
        amount = (Decimal(bound) * Decimal("12.5") + Decimal(output) * 50) / 1000000
        if self.stopped or self.total + amount > self.cap:
            self.stopped = True
            append_event(
                self.path,
                dict(
                    event="cap_stop",
                    retained=str(self.total),
                    next_reservation=str(amount),
                ),
            )
            raise ValueError("Live spend cap prevents dispatch")
        self.total += amount
        append_event(
            self.path,
            dict(
                event="reserved",
                request_hash=request_hash,
                amount=str(amount),
                retained=str(self.total),
            ),
        )
        return amount

    def settle(self, reserved: Decimal, actual: Decimal | None, request_hash: str):
        if actual is not None and actual <= reserved:
            self.total += actual - reserved
        elif actual is not None:
            self.total += actual - reserved
            self.stopped = True
        append_event(
            self.path,
            dict(
                event="settled",
                request_hash=request_hash,
                actual=str(actual) if actual is not None else None,
                retained=str(self.total),
            ),
        )


class RecordingTransport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        ledger: Ledger,
        prices: dict,
        output: Path,
        secret: str,
        transport_factory=None,
    ):
        self.ledger = ledger
        self.prices = prices
        self.output = output
        self.calls = 0
        self.secret_variants = {
            secret.encode(),
            json.dumps(secret)[1:-1].encode(),
            quote(secret, safe="").encode(),
            base64.b64encode(secret.encode()),
        }
        self.transport_factory = transport_factory or (
            lambda: httpx.AsyncHTTPTransport(retries=0)
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body = await request.aread()
        data = json.loads(body)
        request_hash = hashlib.sha256(body).hexdigest()
        reserved = self.ledger.reserve(
            len(body) + INPUT_MARGIN, data["max_output_tokens"], request_hash
        )
        self.calls += 1
        transport = None
        actual = None
        try:
            transport = self.transport_factory()
            response = await transport.handle_async_request(request)
            content = b""
            async for part in response.aiter_bytes():
                content += part
                if len(content) > MAX_RESPONSE_BYTES:
                    raise ValueError("Provider output exceeds recording limit")
            if any(value and value in content for value in self.secret_variants):
                raise ValueError("Sensitive provider content rejected")
            decoded = json.loads(content)
            append_event(
                self.output,
                dict(
                    event="raw_output",
                    request_hash=request_hash,
                    payload=decoded.get("output"),
                    usage=decoded.get("usage"),
                    status=decoded.get("status"),
                    reported_model=decoded.get("model"),
                    http_status=response.status_code,
                ),
            )
            if response.status_code != 200:
                raise ValueError("Provider rejected request; retain unknown hold")
            usage = parse_usage(decoded["usage"])
            actual = estimate(usage, self.prices.get(decoded.get("model")))
            if (
                usage.input is None
                or usage.output is None
                or usage.input > len(body) + INPUT_MARGIN
                or usage.output > data["max_output_tokens"]
            ):
                self.ledger.stopped = True
                append_event(
                    self.ledger.path,
                    dict(event="usage_bound_exceeded", request_hash=request_hash),
                )
            return httpx.Response(response.status_code, content=content)
        finally:
            self.ledger.settle(reserved, actual, request_hash)
            if transport is not None:
                await transport.aclose()

    async def aclose(self):
        pass


def live_provider(settings, ledger: Ledger, raw_output: Path):
    if (
        settings.generation_input_price,
        settings.generation_cached_price,
        settings.generation_write_price,
        settings.generation_output_price,
    ) != (Decimal("10"), Decimal("1"), Decimal("12.5"), Decimal("50")):
        raise ValueError("Evaluation requires declared operator reservation prices")
    provider, prices = configured_provider(settings)
    if not isinstance(provider, ResponsesProvider):
        raise ValueError("Live mode requires explicitly configured provider")
    transport = RecordingTransport(
        ledger, prices, raw_output, provider.key.get_secret_value()
    )
    return replace(provider, transport=transport), prices, transport
