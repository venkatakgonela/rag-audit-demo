import json
import re

from rag_audit.gate import tokens
from rag_audit.generation import (
    FakeGenerator,
    GenerationRequest,
    GenerationResult,
    Usage,
)


class BaselineGenerator(FakeGenerator):
    identity = "offline-extractive"
    model = "sentence-overlap-v1"

    def __init__(self):
        super().__init__()
        self.calls = 0
        self.requests: list[GenerationRequest] = []

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls += 1
        self.requests.append(request)
        statements = []
        if request.evidence:
            evidence = request.evidence[0]
            spans = re.split(r"(?<=[.?!])\s+|\n", evidence.text)
            candidates = [span for span in spans if span.strip() and len(span) <= 2048]
            if candidates:
                quote = max(
                    candidates,
                    key=lambda span: len(tokens(request.question) & tokens(span)),
                )
                statements = [
                    {"text": quote, "quote": quote, "chunk_id": evidence.chunk_id}
                ]
        payload = json.dumps(
            {
                "outcome": "answer" if statements else "insufficient_evidence",
                "statements": statements,
            },
            ensure_ascii=False,
        )
        return GenerationResult(
            payload,
            Usage(
                input=len(request.serialized().encode()), output=len(payload.encode())
            ),
            self.identity,
            self.model,
        )
