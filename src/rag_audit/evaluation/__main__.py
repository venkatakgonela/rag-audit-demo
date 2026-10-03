import argparse
import gzip
import json
import subprocess
import uuid
from dataclasses import asdict
from pathlib import Path

import psycopg

from rag_audit.embeddings import FakeEmbedder, OnnxEmbedder
from rag_audit.evaluation.calibration import choose, grid, summarize
from rag_audit.evaluation.data import append_event, load_split, start_test_run
from rag_audit.evaluation.forecast import forecast
from rag_audit.evaluation.live import Ledger, live_provider
from rag_audit.evaluation.oracle import rule_failures
from rag_audit.evaluation.reporting import deterministic_metrics, report, write_report
from rag_audit.evaluation.runner import run_cases
from rag_audit.evaluation.validation import (
    outcome,
    policy_configuration,
    validate_forecast,
)
from rag_audit.evaluation_data import digest, freeze_digests, read_json
from rag_audit.gate import Gate
from rag_audit.ingestion import ingest
from rag_audit.settings import Settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test", "all"), default="dev")
    parser.add_argument("--embedder", choices=("fake", "real"), default="fake")
    parser.add_argument("--generator", choices=("baseline", "live"), default="baseline")
    parser.add_argument("--policy", default="default")
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--model-directory", type=Path)
    parser.add_argument("--run-log", type=Path)
    parser.add_argument("--forecast-baseline", type=Path)
    parser.add_argument("--rerun-reason")
    arguments = parser.parse_args()
    if arguments.rerun_reason and len(arguments.rerun_reason.strip()) < 20:
        parser.error("Bug-fix reruns require a meaningful recorded reason")
    if arguments.calibrate and (
        arguments.split != "dev"
        or arguments.embedder != "real"
        or arguments.generator != "baseline"
    ):
        parser.error("Calibration requires dev and real embeddings")
    root = arguments.root.resolve()
    if arguments.output.exists() and any(arguments.output.iterdir()):
        raise ValueError("Output exists; retain previous attempts")
    freeze = read_json(root / "datasets/evaluation/freeze.json")
    test_run = arguments.split in ("test", "all")
    if test_run and freeze["digests"] != freeze_digests(root):
        raise ValueError("Freeze mismatch")
    splits = ("dev", "test") if arguments.split == "all" else (arguments.split,)
    cases = [
        case
        for split in splits
        for case in sorted(load_split(root, split), key=lambda case: case.id)
    ]
    manifest = read_json(root / "datasets/corpus-v3/manifest.json")
    embedder = (
        FakeEmbedder()
        if arguments.embedder == "fake"
        else OnnxEmbedder(arguments.model_directory or root / "data/model")
    )
    gate = (
        None
        if arguments.policy == "default"
        else Gate(**read_json(Path(arguments.policy)))
    )
    config = dict(
        split=arguments.split,
        freeze=freeze,
        embedder=embedder.identity,
        generator="sentence-overlap-v1"
        if arguments.generator == "baseline"
        else "informational-live-v1",
        gate=asdict(gate) if gate else None,
        settings={
            key: value
            for key, value in Settings().model_dump(mode="json").items()
            if key
            in (
                "evidence_bytes",
                "question_characters",
                "prompt_bytes",
                "context_chunks",
                "output_units",
                "output_bytes",
                "provider_seconds",
                "cost_ceiling",
                "max_statements",
                "statement_characters",
                "generation_output_tokens",
                "generation_seconds",
                "generation_cost_ceiling",
                "generation_reasoning_effort",
            )
        },
    )
    config.update(policy_configuration(embedder.identity, gate))
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    log = arguments.run_log or root / "datasets/evaluation/run-log.jsonl"
    key = digest(config)
    settings = Settings()
    if settings.database_url is None:
        raise ValueError("Isolated database required")
    schema = "evaluation_" + uuid.uuid4().hex
    arguments.output.mkdir(parents=True, exist_ok=True)
    live = None
    test_started = False
    if arguments.generator == "live":
        if (
            arguments.embedder != "real"
            or arguments.calibrate
            or arguments.forecast_baseline is None
        ):
            raise ValueError(
                "Live run requires real embeddings and frozen-policy baseline forecast"
            )
        baseline = read_json(arguments.forecast_baseline)
        validate_forecast(baseline, config, commit, 2 * len(cases))
        prediction = forecast(baseline["rows"], settings)
        ledger = Ledger(arguments.output / "live-ledger.jsonl", prediction)
        live = live_provider(settings, ledger, arguments.output / "raw-output.jsonl")
    with psycopg.connect(
        settings.database_url.get_secret_value(), autocommit=True
    ) as connection:
        connection.execute(f"CREATE SCHEMA {schema}")
        connection.execute(f"SET search_path TO {schema},public")
        try:
            connection.execute((root / "docker/init/001-enable-vector.sql").read_text())
            ingest(connection, root / "datasets/corpus-v3", embedder)
            if test_run:
                start_test_run(
                    log,
                    dict(
                        event="started",
                        key=key,
                        commit=commit,
                        config=config,
                        rerun_reason=arguments.rerun_reason,
                        command=(
                            f"--split {arguments.split} "
                            f"--embedder {arguments.embedder} "
                            f"--generator {arguments.generator} "
                            "--policy <effective-config> --output <private-output>"
                        ),
                    ),
                )
                test_started = True

            def evaluate(policy):
                rows = run_cases(
                    connection,
                    embedder,
                    cases,
                    policy,
                    live=live,
                    checkpoint=lambda row: append_event(
                        arguments.output / "requests.jsonl", row
                    ),
                )
                lookup = {case.id: case for case in cases}
                for row in rows:
                    case = lookup[row["case"]]
                    if case.category == "rules":
                        failures = rule_failures(
                            case,
                            row["response"],
                            row["trace"],
                            row["assessment"]["calls"],
                            manifest,
                        )
                        row["hard_failures"].extend(failures)
                        row["assessment"]["correct"] = not failures
                        row["assessment"]["answered_wrong"] = bool(failures)
                return rows

            if arguments.calibrate:
                table = []
                for index, policy in enumerate(grid()):
                    rows = evaluate(policy)
                    with gzip.open(
                        arguments.output / f"configuration-{index:03}.json.gz", "wt"
                    ) as saved:
                        json.dump(rows, saved)
                    table.append(summarize(policy, cases, rows))
                    (arguments.output / "calibration.json").write_text(
                        json.dumps(table, indent=2) + "\n"
                    )
                    print(f"Configuration {index + 1}/114 complete", flush=True)
                chosen = choose(table)
                (arguments.output / "selected.json").write_text(
                    json.dumps(chosen["gate"], indent=2) + "\n"
                )
                return int(any(row["hard_failures"] or row["errors"] for row in table))
            rows = evaluate(gate)
            payload = dict(
                commit=commit,
                config=config,
                config_digest=digest(config),
                rows=rows,
                metrics=report(rows),
                **outcome(rows, cases, bool(live and live[2].ledger.stopped)),
            )
            payload["metrics_digest"] = digest(
                deterministic_metrics(payload["metrics"])
            )
            if live:
                payload["live"] = dict(
                    forecast=prediction,
                    retained_estimate=str(ledger.total),
                    cap=str(ledger.cap),
                    dispatched=live[2].calls,
                    stopped=ledger.stopped,
                )
            write_report(arguments.output, payload)
            failures = payload["failed"]
            if test_run:
                append_event(
                    log,
                    dict(
                        event="completed",
                        key=key,
                        requests=len(rows),
                        hard_failure=failures,
                        status=payload["status"],
                        coverage=payload["coverage"],
                    ),
                )
            return int(failures)
        except BaseException:
            if test_started:
                append_event(log, dict(event="interrupted", key=key))
            checkpoint = arguments.output / "requests.jsonl"
            if checkpoint.exists() and not (arguments.output / "results.json").exists():
                rows = [
                    json.loads(line) for line in checkpoint.read_text().splitlines()
                ]
                partial = dict(
                    commit=commit,
                    config=config,
                    rows=rows,
                    metrics=report(rows),
                    **outcome(rows, cases, True),
                )
                partial["interrupted"] = True
                write_report(arguments.output, partial)
            raise
        finally:
            connection.execute("SET search_path TO public")
            connection.execute(f"DROP SCHEMA {schema} CASCADE")


if __name__ == "__main__":
    raise SystemExit(main())
