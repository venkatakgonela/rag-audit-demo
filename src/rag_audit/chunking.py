import hashlib
import re
from dataclasses import dataclass
from typing import Protocol


class OffsetTokenizer(Protocol):
    def offsets(self, text: str) -> list[tuple[int, int]]: ...


@dataclass(frozen=True)
class Chunk:
    identifier: str
    section: str
    ordinal: int
    start: int
    end: int
    text: str


def sections(text: str) -> list[tuple[int, int, str]]:
    boundaries = [(0, "Document")]
    headings: list[str] = []
    position = 0
    fence = ""
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            if not fence:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = ""
        if not fence:
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            clause = re.match(r"^\d+(?:\.\d+)+[.)]?\s+[^\n]+$", line.rstrip())
            if heading:
                headings = headings[: len(heading[1]) - 1] + [heading[2]]
                boundaries.append((position, " / ".join(headings)))
            elif clause:
                boundaries.append((position, " / ".join(headings + [line.strip()])))
        position += len(line)
    return [
        (
            start,
            boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text),
            path,
        )
        for index, (start, path) in enumerate(boundaries)
        if (boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text))
        > start
    ]


def chunk_document(
    document_id: str, text: str, tokenizer: OffsetTokenizer
) -> list[Chunk]:
    chunks: list[Chunk] = []
    tokenizer_identity = getattr(tokenizer, "identity", "offset-tokenizer-v1")
    source_hash = hashlib.sha256(text.encode()).hexdigest()
    for begin, end, path in sections(text):
        prefix_tokens = len(tokenizer.offsets(path + "\n"))
        ceiling = min(480, 510 - prefix_tokens)
        if ceiling < 64:
            raise ValueError("Section path exceeds embedding budget")
        target = min(384, ceiling)
        spans = tokenizer.offsets(text[begin:end])
        cursor = 0
        while cursor < len(spans):
            stop = min(cursor + target, len(spans))
            if len(spans) <= ceiling:
                stop = len(spans)
            start_char = begin if cursor == 0 else begin + spans[cursor][0]
            end_char = end if stop == len(spans) else begin + spans[stop][0]
            content = text[start_char:end_char]
            if len(tokenizer.offsets(path + "\n" + content)) > 510:
                raise ValueError("Chunk exceeds embedding budget")
            digest = hashlib.sha256(
                (
                    f"v1:384:480:48:{tokenizer_identity}:{source_hash}:"
                    f"{document_id}:{path}:{start_char}:{end_char}:{content}"
                ).encode()
            ).hexdigest()
            chunks.append(
                Chunk(digest, path, len(chunks), start_char, end_char, content)
            )
            if stop == len(spans):
                break
            cursor = stop - 48
    return chunks
