import argparse
import gzip
import json
import os
import resource
import subprocess
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path

import psycopg

from rag_audit.embeddings import OnnxEmbedder
from rag_audit.evaluation.calibration import choose, summarize
from rag_audit.evaluation.data import load_split
from rag_audit.evaluation.metrics import percentile
from rag_audit.evaluation.oracle import rule_failures
from rag_audit.evaluation.runner import run_cases
from rag_audit.evaluation_data import read_json
from rag_audit.gate import Gate
from rag_audit.ingestion import ingest
from rag_audit.reranking import REVISION, OnnxReranker
from rag_audit.settings import Settings


def grid() -> list[Gate]:
    probabilities = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99)
    return [Gate("V4a", value) for value in probabilities] + [
        Gate("V4b", value, floor)
        for value in probabilities
        for floor in (0.40, 0.50, 0.60)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixed, dev-only CPU reranker trial")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--model-directory", type=Path)
    parser.add_argument("--reranker-directory", type=Path)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError("Trial output exists; retain previous attempts")
    args.output.mkdir(parents=True, exist_ok=True)
    cases = load_split(args.root, "dev")
    baseline_rows = read_json(args.calibration)
    if len(baseline_rows) != 114:
        raise ValueError("Complete original dev calibration required")
    baseline = choose(baseline_rows)
    manifest = read_json(args.root / "datasets/corpus-v3/manifest.json")
    embedder = OnnxEmbedder(args.model_directory or args.root / "data/model")
    settings = Settings()
    if settings.database_url is None:
        raise ValueError("Isolated database required")
    schema = "reranker_trial_" + uuid.uuid4().hex
    unit = 1 if sys.platform == "darwin" else 1024
    with psycopg.connect(
        settings.database_url.get_secret_value(), autocommit=True
    ) as connection:
        connection.execute(f"CREATE SCHEMA {schema}")
        connection.execute(f"SET search_path TO {schema},public")
        try:
            connection.execute(
                (args.root / "docker/init/001-enable-vector.sql").read_text()
            )
            ingest(connection, args.root / "datasets/corpus-v3", embedder)
            before_rss = (
                int(
                    subprocess.check_output(
                        ["ps", "-o", "rss=", "-p", str(os.getpid())], text=True
                    ).strip()
                )
                * 1024
            )
            started = time.monotonic()
            directory = (
                args.reranker_directory or args.root / "data/reranker" / REVISION
            )
            model = OnnxReranker(directory)
            cold_seconds = time.monotonic() - started
            graph = {
                "inputs": [
                    {"name": item.name, "type": item.type, "shape": item.shape}
                    for item in model.session.get_inputs()
                ],
                "outputs": [
                    {"name": item.name, "type": item.type, "shape": item.shape}
                    for item in model.session.get_outputs()
                ],
                "providers": model.session.get_providers(),
            }
            lookup = {case.id: case for case in cases}
            table = []
            durations = []
            unscorable = 0
            comparisons = 0
            first_scoring_seconds = None
            for index, gate in enumerate(grid()):
                rows = run_cases(connection, embedder, cases, gate, reranker=model)
                for row in rows:
                    case = lookup[row["case"]]
                    row["hard_failures"].extend(
                        rule_failures(
                            case,
                            row["response"],
                            row["trace"],
                            row["assessment"]["calls"],
                            manifest,
                        )
                    )
                    if case.challenge_kind == "free_text":
                        comparisons += 1
                    for observation in (row, row.get("counterfactual")):
                        if observation is None:
                            continue
                        trace = observation["trace"]
                        if trace.get("reranker_scores"):
                            if first_scoring_seconds is None:
                                first_scoring_seconds = trace["reranker_duration"]
                            else:
                                durations.append(trace["reranker_duration"])
                            unscorable += sum(
                                item["score"] is None
                                for item in trace["reranker_scores"]
                            )
                table.append(summarize(gate, cases, rows))
                with gzip.open(
                    args.output / f"configuration-{index:03}.json.gz", "wt"
                ) as output:
                    json.dump(rows, output)
                (args.output / "calibration.json").write_text(
                    json.dumps(table, indent=2) + "\n"
                )
                print(f"Reranker configuration {index + 1}/44 complete", flush=True)
            selected = choose(baseline_rows + table)
            peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * unit
            model_bytes = sum(
                path.stat().st_size for path in directory.rglob("*") if path.is_file()
            )
            latency = percentile(durations, 0.95)
            resources_ok = (
                model_bytes <= 500 * 1024**2
                and max(0, peak_rss - before_rss) <= 1024**3
                and latency is not None
                and latency <= 2
            )
            gain = (
                selected["sufficient"]["natural"] / selected["denominators"]["natural"]
                - baseline["sufficient"]["natural"]
                / baseline["denominators"]["natural"]
            )
            safety_ok = (
                selected["eligible"]
                and not selected["hard_failures"]
                and all(
                    selected["counts"][key] <= baseline["counts"][key]
                    for key in baseline["counts"]
                )
            )
            adopted = (
                selected["gate"]["variant"].startswith("V4")
                and gain >= 0.10
                and safety_ok
                and resources_ok
            )
            result = dict(
                baseline=baseline,
                selected=selected,
                adopt=adopted,
                natural_gain=gain,
                safety_ok=safety_ok,
                resources_ok=resources_ok,
                model_bytes=model_bytes,
                rss_before_model_bytes=before_rss,
                process_peak_rss_bytes=peak_rss,
                additional_rss_upper_bound_bytes=max(0, peak_rss - before_rss),
                rss_method=(
                    "Process high-water minus current RSS before reranker load; "
                    "includes trial/report allocations, not model-exclusive."
                ),
                cold_load_seconds=cold_seconds,
                first_scoring_seconds=first_scoring_seconds,
                warm_p50_seconds=percentile(durations, 0.5),
                warm_p95_seconds=latency,
                timed_queries=len(durations),
                unscorable_pairs=unscorable,
                hidden_removal_comparisons=comparisons,
                graph=graph,
                identity=model.identity,
                freeze=read_json(args.root / "datasets/evaluation/freeze.json"),
                commit=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=args.root, text=True
                ).strip(),
                configurations=[asdict(gate) for gate in grid()],
                test_runs=0,
                live_calls=0,
            )
            (args.output / "decision.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            print(json.dumps(result, indent=2), flush=True)
            return int(any(row["errors"] or row["hard_failures"] for row in table))
        finally:
            connection.execute("SET search_path TO public")
            connection.execute(f"DROP SCHEMA {schema} CASCADE")


if __name__ == "__main__":
    raise SystemExit(main())
