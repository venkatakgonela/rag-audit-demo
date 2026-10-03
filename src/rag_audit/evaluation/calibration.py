from dataclasses import asdict

from rag_audit.evaluation_data import Case
from rag_audit.gate import Gate


def grid() -> list[Gate]:
    cosine = [value / 100 for value in range(15, 101, 5)]
    return (
        [Gate()]
        + [Gate("V1", value) for value in cosine]
        + [
            Gate("V2", value, fraction)
            for value in cosine
            for fraction in (0.25, 0.5, 0.75, 1.0)
        ]
        + [Gate("V3", value / 100) for value in range(15, 126, 5)]
    )


def summarize(gate: Gate, cases: list[Case], results: list[dict]) -> dict:
    if any(case.split != "dev" for case in cases):
        raise ValueError("Calibration accepts dev labels only")
    lookup = {case.id: case for case in cases}
    counts = dict(off_domain=0, near_miss=0, id_lookup=0, free_text=0)
    sufficient = dict(natural=0, keyword=0)
    denominators = dict(natural=0, keyword=0)
    hard = sum(len(row["hard_failures"]) for row in results)
    for row in results:
        case = lookup[row["case"]]
        selected = bool(row["trace"]["sent_ids"])
        if case.challenge_kind in counts:
            counts[case.challenge_kind] += int(selected)
        if case.category in ("single", "multi"):
            denominators[row["style"]] += 1
            sufficient[row["style"]] += int(selected)
    errors = sum(row["response"]["decision"] == "error" for row in results)
    eligible = not (
        counts["off_domain"]
        or counts["id_lookup"]
        or counts["free_text"]
        or hard
        or errors
    )
    return dict(
        gate=asdict(gate),
        counts=counts,
        sufficient=sufficient,
        denominators=denominators,
        eligible=eligible,
        hard_failures=hard,
        errors=errors,
        descriptive_only=(
            counts["free_text"] == 1
            and not counts["off_domain"]
            and not counts["id_lookup"]
            and not hard
            and not errors
        ),
    )


def choose(rows: list[dict]) -> dict:
    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        return next(row for row in rows if row["gate"]["variant"] == "V0")
    minimum = min(sum(row["counts"].values()) for row in eligible)
    tied = [row for row in eligible if sum(row["counts"].values()) <= minimum + 1]
    return min(
        tied,
        key=lambda row: (
            -row["sufficient"]["natural"],
            -row["sufficient"]["keyword"],
            row["counts"]["near_miss"],
            row["gate"]["variant"],
            -row["gate"]["threshold"],
            -row["gate"]["fraction"],
        ),
    )
