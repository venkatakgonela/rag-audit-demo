import asyncio
import json
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import httpx
from pydantic import SecretStr

from rag_audit.accounting import validate_usage
from rag_audit.generation import GenerationRequest, GenerationResult, Usage
from rag_audit.policy import strict_json

BOUND_VERSION = "responses-utf8-margin-v1"
INPUT_MARGIN = 1024
MAX_INPUT_TOKENS = 272000
MAX_RESPONSE_BYTES = 131072


class ProviderError(ValueError):
    pass


def schema(rule: bool) -> dict:
    properties: dict
    text = {"type": "string"}
    if rule:
        properties = {"text": text}
    else:
        properties = {
            "outcome": {"type": "string", "enum": ["answer", "insufficient_evidence"]},
            "statements": {
                "type": "array",
                "minItems": 0,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "maxLength": 2048},
                        "quote": {"type": "string", "maxLength": 2048},
                        "chunk_id": text,
                    },
                    "required": ["text", "quote", "chunk_id"],
                    "additionalProperties": False,
                },
            },
        }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def counter(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ProviderError("Invalid provider usage")
    return value


def aliases(locations: list[dict], names: tuple[str, ...]) -> int | None:
    values = [
        counter(location[name])
        for location in locations
        for name in names
        if name in location and location[name] is not None
    ]
    if not values:
        return None
    if len(set(values)) != 1:
        raise ProviderError("Conflicting usage counters")
    return values[0]


def parse_usage(raw: object) -> Usage:
    if type(raw) is not dict:
        raise ProviderError("Missing provider usage")
    inputs, outputs = (
        counter(raw.get("input_tokens")),
        counter(raw.get("output_tokens")),
    )
    if counter(raw.get("total_tokens")) != inputs + outputs:
        raise ProviderError("Inconsistent provider usage")
    input_details = raw.get("input_tokens_details", {})
    output_details = raw.get("output_tokens_details", {})
    if type(input_details) is not dict or type(output_details) is not dict:
        raise ProviderError("Invalid provider usage details")
    cached = aliases([raw, input_details], ("cached_read_tokens", "cached_tokens"))
    writes = aliases(
        [raw, input_details], ("cached_write_tokens", "cache_write_tokens")
    )
    reasoning = aliases([output_details], ("reasoning_tokens",))
    if cached is None or reasoning is None:
        raise ProviderError("Missing usage semantics")
    if writes is None:
        raise ProviderError("Missing cache-write semantics")
    usage = Usage(
        inputs, outputs, cached, reasoning, unit="provider_tokens", cache_write=writes
    )
    validate_usage(usage)
    return usage


@dataclass(frozen=True)
class ResponsesProvider:
    base_url: str = field(repr=False)
    model: str
    reported_model: str
    key: SecretStr = field(repr=False)
    effort: str = "medium"
    transport: httpx.AsyncBaseTransport | None = field(
        default=None, repr=False, compare=False
    )
    identity: str = field(default="responses", init=False)

    def __post_init__(self):
        address = urlsplit(self.base_url)
        if (
            address.scheme not in ("http", "https")
            or not address.hostname
            or address.username
            or address.password
            or address.query
            or address.fragment
            or (
                address.scheme == "http"
                and address.hostname not in ("127.0.0.1", "localhost", "::1")
            )
            or not self.model
            or not self.reported_model
            or not self.key.get_secret_value()
            or self.effort not in ("low", "medium", "high")
        ):
            raise ProviderError("Invalid provider configuration")

    def body(self, request: GenerationRequest) -> bytes:
        data = {
            "question": request.question,
            "EVIDENCE_JSON": [
                {"chunk_id": item.chunk_id, "text": item.text}
                for item in request.evidence
            ],
            "templates": request.templates,
            "answer_mode": request.answer_mode,
        }
        payload = {
            "model": self.model,
            "instructions": request.system,
            "input": [
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
            ],
            "reasoning": {"effort": self.effort},
            "max_output_tokens": request.max_output_units,
            "stream": False,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "extractive_answer"
                    if not request.templates
                    else "rule_wording",
                    "strict": True,
                    "schema": schema(bool(request.templates)),
                }
            },
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()

    def input_bound(self, request: GenerationRequest) -> int:
        return len(self.body(request)) + INPUT_MARGIN

    def parse(self, data: object) -> GenerationResult:
        if type(data) is not dict or type(data.get("model")) is not str:
            raise ProviderError("Invalid provider response")
        usage = parse_usage(data.get("usage"))
        status = data.get("status")
        if status not in ("completed", "incomplete"):
            raise ProviderError("Invalid provider status")
        if status == "incomplete":
            return GenerationResult(
                "", usage, self.identity, data["model"], "incomplete"
            )
        output = data.get("output")
        if type(output) is not list:
            raise ProviderError("Missing provider output")
        texts = []
        for item in output:
            if type(item) is not dict:
                raise ProviderError("Invalid provider output")
            if item.get("type") == "reasoning":
                continue
            if (
                item.get("type") != "message"
                or item.get("role") != "assistant"
                or item.get("status") != "completed"
            ):
                raise ProviderError("Unexpected provider output")
            content = item.get("content")
            if type(content) is not list:
                raise ProviderError("Invalid provider content")
            for part in content:
                if type(part) is not dict:
                    raise ProviderError("Invalid provider content")
                if part.get("type") == "refusal":
                    return GenerationResult(
                        "", usage, self.identity, data["model"], "refusal"
                    )
                if (
                    part.get("type") != "output_text"
                    or type(part.get("text")) is not str
                ):
                    raise ProviderError("Unexpected provider content")
                texts.append(part["text"])
        if len(texts) != 1:
            raise ProviderError("Ambiguous provider output")
        return GenerationResult(texts[0], usage, self.identity, data["model"])

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            async with asyncio.timeout(request.timeout_seconds):
                async with httpx.AsyncClient(
                    transport=self.transport,
                    trust_env=False,
                    follow_redirects=False,
                    timeout=httpx.Timeout(request.timeout_seconds),
                ) as client:
                    async with client.stream(
                        "POST",
                        self.base_url.rstrip("/") + "/responses",
                        headers={
                            "Authorization": "Bearer " + self.key.get_secret_value(),
                            "Content-Type": "application/json",
                        },
                        content=self.body(request),
                    ) as response:
                        if response.status_code != 200:
                            raise ProviderError("Provider HTTP failure")
                        raw = bytearray()
                        async for block in response.aiter_bytes():
                            if len(raw) + len(block) > MAX_RESPONSE_BYTES:
                                raise ProviderError("Provider response limit")
                            raw.extend(block)
                        if self.key.get_secret_value().encode() in raw:
                            raise ProviderError("Provider response rejected")
                        return self.parse(strict_json(raw.decode("utf-8")))
        except Exception:
            raise ProviderError("Provider request failed") from None
