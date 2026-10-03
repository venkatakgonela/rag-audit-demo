from dataclasses import asdict

from rag_audit.evaluation_data import digest
from rag_audit.gate import Gate
from rag_audit.policy import PROFILES


def policy_configuration(identity: str, gate: Gate | None) -> dict:
    profile = PROFILES[identity]
    return dict(
        profile=asdict(profile),
        effective_gate=asdict(gate or Gate(profile.variant, profile.cosine_floor)),
    )


def validate_forecast(baseline: dict, config: dict, commit: str, expected: int) -> None:
    if (
        baseline.get("commit") != commit
        or baseline.get("status") != "complete"
        or len(baseline.get("rows", [])) != expected
        or baseline["config"].get("generator") != "sentence-overlap-v1"
        or any(
            baseline["config"].get(key) != config.get(key)
            for key in (
                "freeze",
                "embedder",
                "gate",
                "profile",
                "effective_gate",
                "settings",
                "split",
            )
        )
        or any(row["hard_failures"] for row in baseline["rows"])
    ):
        raise ValueError("Forecast baseline configuration mismatch")


def outcome(rows: list[dict], cases: list, stopped: bool = False) -> dict:
    expected = {
        (case.id, phrasing.style) for case in cases for phrasing in case.phrasings
    }
    observed = {(row["case"], row["style"]) for row in rows}
    complete = observed == expected and len(rows) == len(expected) and not stopped
    failures = any(
        row["hard_failures"] or row["response"]["decision"] == "error" for row in rows
    )
    return dict(
        status="complete"
        if complete and not failures
        else "failed"
        if complete
        else "partial",
        coverage=dict(
            expected=len(expected),
            attempted=len(rows),
            not_run=len(expected - observed),
            missing=[list(item) for item in sorted(expected - observed)],
        ),
        failed=failures or not complete,
        result_identity=digest(
            [
                {
                    key: row[key]
                    for key in (
                        "case",
                        "style",
                        "response",
                        "assessment",
                        "hard_failures",
                    )
                }
                for row in rows
            ]
        ),
    )
