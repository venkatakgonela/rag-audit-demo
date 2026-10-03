import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from rag_audit.evaluation.metrics import aggregate, percentile, rate


def summarize_rows(rows: list[dict]) -> dict:
    result = aggregate(rows)
    retrieval = [
        row
        for row in rows
        if row["category"] in ("single", "multi", "injection")
        and row["assessment"]["recall"]["5"][1]
    ]
    for limit in ("5", "10"):
        counts = [row["assessment"]["recall"][limit] for row in retrieval]
        result[f"recall@{limit}"] = rate(
            sum(pair[0] for pair in counts), sum(pair[1] for pair in counts)
        )
    result["MRR"] = (
        sum(row["assessment"]["reciprocal_rank"] for row in retrieval) / len(retrieval)
        if retrieval
        else None
    )
    counts = [row["assessment"]["section_recall"] for row in retrieval]
    result["section_recall@5"] = rate(
        sum(pair[0] for pair in counts), sum(pair[1] for pair in counts)
    )
    counts = [row["assessment"]["facts"] for row in rows if row["category"] != "rules"]
    result["fact_coverage"] = rate(
        sum(pair[0] for pair in counts), sum(pair[1] for pair in counts)
    )
    fact_rows = [pair for pair in counts if pair[1]]
    result["all_facts_covered"] = rate(
        sum(pair[0] == pair[1] for pair in fact_rows), len(fact_rows)
    )
    rule_rows = [row for row in rows if row["category"] == "rules"]
    result["rule_agreement"] = rate(
        sum(row["assessment"]["correct"] for row in rule_rows), len(rule_rows)
    )
    answerable = [row for row in rows if row["category"] in ("single", "multi")]
    negative = [
        row for row in rows if row["category"] in ("unanswerable", "unauthorised")
    ]
    result["evidence_sufficient"] = rate(
        sum(bool(row["trace"]["sent_ids"]) for row in answerable), len(answerable)
    )
    result["false_evidence"] = rate(
        sum(bool(row["trace"]["sent_ids"]) for row in negative), len(negative)
    )
    result["verification_reasons"] = dict(
        Counter(
            row["trace"]["verification_reason"]
            for row in rows
            if row["trace"]["verification_reason"]
        )
    )
    result["errors"] = sum(row["response"]["decision"] == "error" for row in rows)
    result["attack_exposure"] = {
        key: rate(
            sum(bool(row.get(key)) for row in rows if row["category"] == "injection"),
            sum(row["category"] == "injection" for row in rows),
        )
        for key in ("attack_retrieved", "attack_sent")
    }
    result["latency"] = {}
    for invoked in (False, True):
        selected = [row for row in rows if bool(row["assessment"]["calls"]) == invoked]
        stages = sorted({key for row in selected for key in row["trace"]["durations"]})
        result["latency"][str(invoked)] = {
            stage: dict(
                n=sum(stage in row["trace"]["durations"] for row in selected),
                p50=percentile(
                    [
                        row["trace"]["durations"][stage]
                        for row in selected
                        if stage in row["trace"]["durations"]
                    ],
                    0.5,
                ),
                p95=percentile(
                    [
                        row["trace"]["durations"][stage]
                        for row in selected
                        if stage in row["trace"]["durations"]
                    ],
                    0.95,
                ),
            )
            for stage in stages
        }
        gates = [
            row["trace"]["gate_duration"]
            for row in selected
            if "gate_duration" in row["trace"]
        ]
        result["latency"][str(invoked)]["gate"] = dict(
            n=len(gates), p50=percentile(gates, 0.5), p95=percentile(gates, 0.95)
        )
    result["usage"] = {
        key: sum((row["trace"]["usage"] or {}).get(key, 0) or 0 for row in rows)
        for key in ("input", "output", "cached", "cache_write", "reasoning")
    }
    result["unknown_usage"] = sum(
        row["assessment"]["calls"] > 0 and row["trace"]["usage"] is None for row in rows
    )
    result["unknown_cost"] = sum(
        row["assessment"]["calls"] > 0 and row["trace"]["cost_usd"] is None
        for row in rows
    )
    costs = [
        row["trace"]["cost_usd"] for row in rows if row["trace"]["cost_usd"] is not None
    ]
    result["estimated_cost"] = (
        str(sum((Decimal(value) for value in costs), Decimal(0))) if costs else None
    )
    return result


def report(rows: list[dict]) -> dict:
    groups = {"all": summarize_rows(rows)}
    for field in ("split", "category", "style", "challenge_kind"):
        for value in sorted({row[field] for row in rows}):
            groups[f"{field}:{value}"] = summarize_rows(
                [row for row in rows if row[field] == value]
            )
    for split in sorted({row["split"] for row in rows}):
        for style in ("keyword", "natural"):
            groups[f"{split}/{style}"] = summarize_rows(
                [row for row in rows if row["split"] == split and row["style"] == style]
            )
        for category in sorted({row["category"] for row in rows}):
            for style in ("keyword", "natural"):
                groups[f"{split}/{category}/{style}"] = summarize_rows(
                    [
                        row
                        for row in rows
                        if row["split"] == split
                        and row["category"] == category
                        and row["style"] == style
                    ]
                )
    cases = {
        identifier: len([row for row in rows if row["case"] == identifier]) == 2
        and all(
            row["assessment"]["allowed"]
            and not row["hard_failures"]
            and (
                row["response"]["decision"] != "answered"
                or row["assessment"]["correct"]
            )
            for row in rows
            if row["case"] == identifier
        )
        for identifier in sorted({row["case"] for row in rows})
    }
    probes = [row["counterfactual"] for row in rows if "counterfactual" in row]
    return dict(groups=groups, cases=cases, counterfactuals=summarize_rows(probes))


def deterministic_metrics(metrics: dict) -> dict:
    if not isinstance(metrics, dict):
        return metrics
    return {
        key: deterministic_metrics(value) if isinstance(value, dict) else value
        for key, value in metrics.items()
        if key != "latency"
    }


def write_report(output: Path, payload: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )
    lines = [
        "# Evaluation results",
        "",
        "Synthetic, drafted labels; descriptive counts, not significance evidence.",
        f"Run status: {payload.get('status', 'unspecified')}; "
        f"coverage: {payload.get('coverage', {})}.",
        "",
        "| Group | n | Correct answer | False evidence | Hard failures |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for name, group in payload["metrics"]["groups"].items():
        correct = group["correct_answer"]
        false = group["false_evidence"]
        lines.append(
            f"| {name} | {group['requests']} | {correct['hits']}/{correct['total']} "
            f"| {false['hits']}/{false['total']} | {group['hard_failures']} |"
        )
    lines += [
        "",
        "All rate intervals and per-request details are in results.json. "
        "MRR, cost and latency intervals are N/A.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n")
