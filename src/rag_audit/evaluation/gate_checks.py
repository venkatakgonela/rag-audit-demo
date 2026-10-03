import math
from decimal import Decimal

from rag_audit.evaluation.reporting import report


def measures(rows: list[dict]) -> dict:
    metrics = report(rows)
    values = {}
    for split in ("dev", "test"):
        selected = [row for row in rows if row["split"] == split]
        for style in ("keyword", "natural"):
            group = metrics["groups"].get(f"{split}/{style}", {})
            for name in ("evidence_sufficient", "correct_answer"):
                values[f"{split}/{style}/{name}"] = group.get(name, {}).get("hits", 0)
            for name in (
                "false_answer",
                "missed_answer",
                "correct_abstention",
                "model_abstention",
            ):
                values[f"{split}/{style}/{name}"] = group.get(name, {}).get("hits", 0)
        group = metrics["groups"].get(f"split:{split}", {})
        values[f"{split}/recall_hits"] = group.get("recall@5", {}).get("hits", 0)
        retrieval = [
            row
            for row in selected
            if row["category"] in ("single", "multi", "injection")
            and row["assessment"]["recall"]["5"][1]
        ]
        values[f"{split}/recall_total"] = group.get("recall@5", {}).get("total", 0)
        values[f"{split}/mrr_count"] = len(retrieval)
        values[f"{split}/mrr_sum"] = sum(
            row["assessment"]["reciprocal_rank"] for row in retrieval
        )
        for subtype in ("off_domain", "id_lookup", "free_text", "near_miss"):
            values[f"{split}/false_evidence/{subtype}"] = sum(
                bool(row["trace"]["sent_ids"])
                for row in selected
                if row["challenge_kind"] == subtype
            )
            values[f"{split}/false_answer/{subtype}"] = sum(
                row["assessment"]["false_answer"]
                for row in selected
                if row["challenge_kind"] == subtype
            )
        for reason in (
            "schema",
            "citation",
            "quotation",
            "instruction_echo",
            "duplicate",
        ):
            values[f"{split}/verification/{reason}"] = group.get(
                "verification_reasons", {}
            ).get(reason, 0)
        calls = group.get("provider_calls", 0)
        costs = group.get("estimated_cost")
        values[f"{split}/cost_per_call"] = (
            str(Decimal(costs) / calls) if calls and costs is not None else None
        )
        values[f"{split}/unknown_cost"] = group.get("unknown_cost", 0)
    return values


def check_rows(
    rows: list[dict],
    baseline: dict,
    policy: dict,
    expected: set[tuple[str, str]],
    replay_failures: list,
) -> list[dict]:
    checks = []

    def check(name, before, current, passed):
        checks.append(
            dict(check=name, baseline=before, current=current, passed=bool(passed))
        )

    tolerance = policy["count_tolerance"]
    if type(tolerance) is not int or not 0 <= tolerance <= 1:
        raise ValueError("gate_policy: count tolerance must be finite integer 0 or 1")
    for key in ("mrr_tolerance", "cost_tolerance"):
        if not math.isfinite(float(policy[key])) or float(policy[key]) < 0:
            raise ValueError("gate_policy: invalid numeric tolerance")
    observed = [(row["case"], row["style"]) for row in rows]
    check(
        "complete",
        len(expected),
        len(observed),
        set(observed) == expected and len(observed) == len(expected),
    )
    hard = sum(len(row["hard_failures"]) for row in rows)
    check("hard_safety", 0, hard, hard == 0)
    for name in sorted({failure for row in rows for failure in row["hard_failures"]}):
        check(
            "hard:" + name, 0, sum(name in row["hard_failures"] for row in rows), False
        )
    errors = sum(row["response"]["decision"] == "error" for row in rows)
    check("operational_errors", 0, errors, errors == 0)
    check("replay_identity", 0, len(replay_failures), not replay_failures)
    probes = sum("counterfactual" in row for row in rows)
    required_probes = baseline["counterfactuals"]
    check("counterfactual_coverage", required_probes, probes, probes == required_probes)
    current = measures(rows)
    for name, before in baseline["measures"].items():
        after = current[name]
        if (
            "/false_evidence/" in name
            or "/false_answer/" in name
            or name.endswith(("unknown_cost", "false_answer", "missed_answer"))
        ):
            passed = after <= before
        elif name.endswith("model_abstention"):
            passed = after == before
        elif "/verification/" in name:
            passed = after <= before + tolerance
        elif name.endswith("cost_per_call"):
            passed = (
                after == before
                if before is None or after is None
                else Decimal(after)
                <= Decimal(before) + Decimal(policy["cost_tolerance"])
            )
        elif name.endswith(("recall_total", "mrr_count")):
            passed = after == before
        elif name.endswith("mrr_sum"):
            passed = after >= before - policy["mrr_tolerance"]
        else:
            passed = after >= before - tolerance
        check(name, before, after, passed)
    return checks
