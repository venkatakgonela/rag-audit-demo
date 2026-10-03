import json
from dataclasses import dataclass
from enum import StrEnum

from rag_audit.embeddings import MODEL, REVISION, FakeEmbedder
from rag_audit.gate import Gate
from rag_audit.settings import AnswerMode, Settings

CONFIGURATION_VERSION = "extractive-policy-v1"
ECHO_VERSION = "instruction-echo-v1"
ECHO_PHRASES = (
    "ignore previous instructions",
    "reveal all claims",
    "<|system|>",
    "[system]",
    "</evidence>",
    "<system>",
)


class VerificationReason(StrEnum):
    SCHEMA = "schema"
    CITATION = "citation"
    QUOTATION = "quotation"
    INSTRUCTION_ECHO = "instruction_echo"
    DUPLICATE = "duplicate"


class VerificationError(ValueError):
    def __init__(self, reason: VerificationReason, message: str):
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class Profile:
    version: str
    cosine_floor: float
    variant: str = "V0"


PROFILES = {
    FakeEmbedder.identity: Profile("fake-demo-v1", 0.15),
    f"{MODEL}@{REVISION}:cls:l2:section-v1": Profile("local-calibrated-v1", 0.55, "V1"),
}


def envelope(
    decision: str = "no_answer",
    text: str | None = None,
    statements: list | None = None,
    rule: dict | None = None,
) -> dict:
    if text is None:
        text = (
            "The service could not complete this request."
            if decision == "error"
            else "I cannot answer from the available evidence."
        )
    return {
        "decision": decision,
        "text": text,
        "statements": statements or [],
        "rule": rule,
    }


def serialize(response: dict) -> str:
    return json.dumps(
        response, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


def select_evidence(
    chunks: list[dict],
    model: str,
    settings: Settings,
    *,
    gate: Gate | None = None,
    question: str = "",
) -> tuple[list[dict], list[str]]:
    profile = PROFILES.get(model)
    if profile is None:
        raise ValueError("Unknown evidence profile")
    selected: list[dict] = []
    skips = []
    used = 0
    effective_gate = gate or Gate(profile.variant, profile.cosine_floor)
    for chunk in chunks:
        if not effective_gate.accepts(chunk, question):
            skips.append("weak_signal")
            continue
        size = len(chunk["text"].encode())
        if used + size > settings.evidence_bytes:
            skips.append("whole_chunk_budget_skip")
            continue
        if len(selected) >= settings.context_chunks:
            skips.append("chunk_count_skip")
            continue
        used += size
        selected.append(chunk)
    return selected, skips


def strict_json(payload: str) -> object:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate key")
            result[key] = value
        return result

    return json.loads(
        payload,
        object_pairs_hook=unique_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError()),
    )


def verify(
    payload: str, authorised: set[str], sent: list[dict], settings: Settings
) -> list[dict]:
    if (
        settings.answer_mode != AnswerMode.EXTRACTIVE
        or len(payload.encode()) > settings.output_bytes
    ):
        raise VerificationError(VerificationReason.SCHEMA, "Output limit")
    try:
        data = strict_json(payload)
    except ValueError:
        raise VerificationError(VerificationReason.SCHEMA, "Invalid JSON") from None
    if type(data) is not dict or set(data) != {"statements"}:
        raise VerificationError(VerificationReason.SCHEMA, "Invalid schema")
    statements = data["statements"]
    if (
        type(statements) is not list
        or not 1 <= len(statements) <= settings.max_statements
    ):
        raise VerificationError(VerificationReason.SCHEMA, "Invalid statements")
    sources = {chunk["id"]: chunk for chunk in sent}
    verified = []
    seen = set()
    for statement in statements:
        if type(statement) is not dict or set(statement) != {
            "text",
            "chunk_id",
            "quote",
        }:
            raise VerificationError(VerificationReason.SCHEMA, "Invalid statement")
        if any(type(value) is not str for value in statement.values()):
            raise VerificationError(VerificationReason.SCHEMA, "Invalid field")
        identifier, quote, text = (
            statement["chunk_id"],
            statement["quote"],
            statement["text"],
        )
        if identifier not in authorised or identifier not in sources:
            raise VerificationError(VerificationReason.CITATION, "Invalid citation")
        if (
            not quote.strip()
            or len(quote) > settings.statement_characters
            or text != quote
            or quote not in sources[identifier]["text"]
        ):
            raise VerificationError(VerificationReason.QUOTATION, "Invalid quotation")
        if any(phrase in text.casefold() for phrase in ECHO_PHRASES):
            raise VerificationError(
                VerificationReason.INSTRUCTION_ECHO, "Instruction echo"
            )
        if (identifier, quote) in seen:
            raise VerificationError(VerificationReason.DUPLICATE, "Duplicate statement")
        seen.add((identifier, quote))
        source = sources[identifier]
        verified.append(
            {
                **statement,
                "section": source["section"],
                "start_offset": source["start_offset"],
                "end_offset": source["end_offset"],
            }
        )
    return verified
