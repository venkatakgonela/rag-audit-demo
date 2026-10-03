import math
import re
from dataclasses import dataclass

STOPWORDS = frozenset(
    "a an and are as at be been being but by can could did do does for from had "
    "has have how i if in into is it its may might of on or our should so that "
    "the their them there these they this those to was we were what when where "
    "which who why will with would you your".split()
)


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold())) - STOPWORDS


def lexical_coverage(question: str, chunk: dict) -> float:
    terms = tokens(question)
    return (
        len(terms & tokens(chunk["section"] + "\n" + chunk["text"])) / len(terms)
        if terms
        else 0.0
    )


@dataclass(frozen=True)
class Gate:
    variant: str = "V0"
    threshold: float = 0.55
    fraction: float = 0.0

    def __post_init__(self):
        if self.variant not in ("V0", "V1", "V2", "V3"):
            raise ValueError("Unknown gate variant")
        if not all(math.isfinite(value) for value in (self.threshold, self.fraction)):
            raise ValueError("Invalid gate threshold")

    def accepts(self, chunk: dict, question: str) -> bool:
        cosine, keyword = chunk["cosine_similarity"], chunk["keyword_score"]
        if not math.isfinite(cosine) or not math.isfinite(keyword):
            return False
        coverage = lexical_coverage(question, chunk)
        if self.variant == "V0":
            return (
                cosine >= self.threshold
                and keyword > 0
                and chunk["keyword_rank"] is not None
            )
        if self.variant == "V1":
            return cosine >= self.threshold
        if self.variant == "V2":
            return cosine >= self.threshold and coverage >= self.fraction
        return cosine + 0.25 * coverage >= self.threshold
