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
from rag_audit.evaluation.data import append_event, load_split
from rag_audit.evaluation.oracle import rule_failures
from rag_audit.evaluation.reporting import report, write_report
from rag_audit.evaluation.runner import run_cases
from rag_audit.evaluation_data import digest, freeze_digests, read_json
from rag_audit.gate import Gate
from rag_audit.ingestion import ingest
from rag_audit.settings import Settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test", "all"), default="dev")
    parser.add_argument("--embedder", choices=("fake", "real"), default="fake")
    parser.add_argument("--generator", choices=("baseline",), default="baseline")
    parser.add_argument("--policy", default="default")
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--model-directory", type=Path)
    parser.add_argument("--run-log", type=Path)
    arguments = parser.parse_args()
    if arguments.calibrate and (
        arguments.split != "dev" or arguments.embedder != "real"
    ):
        parser.error("Calibration requires dev and real embeddings")
    root = arguments.root.resolve()
    freeze = read_json(root / "datasets/evaluation/freeze.json")
    test_run = arguments.split in ("test", "all")
    if test_run and freeze["digests"] != freeze_digests(root):
        raise ValueError("Freeze mismatch")
    splits = ("dev", "test") if arguments.split == "all" else (arguments.split,)
    cases = [case for split in splits for case in load_split(root, split)]
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
        freeze=freeze,
        embedder=embedder.identity,
        generator="sentence-overlap-v1",
        gate=asdict(gate) if gate else None,
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    log = arguments.run_log or root / "datasets/evaluation/run-log.jsonl"
    key = digest(config)
    if test_run:
        if log.exists() and any(
            json.loads(line).get("key") == key for line in log.read_text().splitlines()
        ):
            raise ValueError(
                "Test configuration already attempted; explicit bug-fix review required"
            )
        append_event(
            log,
            dict(
                event="started",
                key=key,
                commit=commit,
                config=config,
                command=(
                    f"--split {arguments.split} --embedder {arguments.embedder} "
                    "--generator baseline --policy <configuration>"
                ),
            ),
        )
    settings = Settings()
    if settings.database_url is None:
        raise ValueError("Isolated database required")
    schema = "evaluation_" + uuid.uuid4().hex
    arguments.output.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(
        settings.database_url.get_secret_value(), autocommit=True
    ) as connection:
        connection.execute(f"CREATE SCHEMA {schema}")
        connection.execute(f"SET search_path TO {schema},public")
        try:
            connection.execute((root / "docker/init/001-enable-vector.sql").read_text())
            ingest(connection, root / "datasets/corpus-v3", embedder)

            def evaluate(policy):
                rows = run_cases(connection, embedder, cases, policy)
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
                return 0
            rows = evaluate(gate)
            payload = dict(
                commit=commit, config=config, rows=rows, metrics=report(rows)
            )
            write_report(arguments.output, payload)
            failures = any(
                row["hard_failures"] or row["response"]["decision"] == "error"
                for row in rows
            )
            if test_run:
                append_event(
                    log,
                    dict(
                        event="completed",
                        key=key,
                        requests=len(rows),
                        hard_failure=failures,
                    ),
                )
            return int(failures)
        finally:
            connection.execute("SET search_path TO public")
            connection.execute(f"DROP SCHEMA {schema} CASCADE")


if __name__ == "__main__":
    raise SystemExit(main())
