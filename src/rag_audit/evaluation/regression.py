import argparse
import json
import platform
import subprocess
import time
import uuid
from pathlib import Path

import psycopg
from psycopg import sql

from rag_audit.embeddings import OnnxEmbedder
from rag_audit.evaluation.data import load_split
from rag_audit.evaluation.model_integrity import verify
from rag_audit.evaluation.oracle import rule_failures
from rag_audit.evaluation.replay import (
    ReplayTransport,
    fixture_entries,
    no_network,
    provider,
)
from rag_audit.evaluation.reporting import deterministic_metrics, report
from rag_audit.evaluation.runner import run_cases
from rag_audit.evaluation.validation import outcome, policy_configuration
from rag_audit.evaluation_data import digest, freeze_digests, read_json
from rag_audit.ingestion import ingest
from rag_audit.settings import Settings


def active_live_baseline(root: Path) -> dict:
    directory = root / "datasets/evaluation"
    manifest = read_json(directory / "replay/manifest.json")
    version = manifest.get("live_baseline", "live-v1.json")
    if version not in ("live-v1.json", "live-v2.json"):
        raise ValueError("live_baseline: unsupported version")
    return read_json(directory / "baselines" / version)


def evaluate(root: Path, model_directory: Path) -> dict:
    started = time.monotonic()
    directory = root / "datasets/evaluation"
    freeze = read_json(directory / "freeze.json")
    if freeze["state"] != "accepted" or freeze["digests"] != freeze_digests(root):
        raise ValueError("freeze_digest: frozen data mismatch")
    verify(model_directory, read_json(directory / "model-manifest.json"))
    embedder = OnnxEmbedder(model_directory)
    cases = [
        case
        for split in ("dev", "test")
        for case in sorted(load_split(root, split), key=lambda case: case.id)
    ]
    transport = ReplayTransport(fixture_entries(directory / "replay"))
    settings = Settings()
    if settings.database_url is None:
        raise ValueError("Configured local database required")
    schema = "regression_" + uuid.uuid4().hex
    with psycopg.connect(
        settings.database_url.get_secret_value(), autocommit=True
    ) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        connection.execute(
            sql.SQL("SET search_path TO {},public").format(sql.Identifier(schema))
        )
        try:
            connection.execute((root / "docker/init/001-enable-vector.sql").read_text())
            with no_network():
                ingest(connection, root / "datasets/corpus-v3", embedder)
                rows = run_cases(
                    connection, embedder, cases, None, live=provider(transport)
                )
            manifest = read_json(root / "datasets/corpus-v3/manifest.json")
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
            try:
                transport.complete()
            except ValueError:
                pass
            metrics = report(rows)
            return dict(
                rows=rows,
                metrics=metrics,
                metrics_digest=digest(deterministic_metrics(metrics)),
                replay_failures=transport.failures,
                consumed=transport.used,
                platform=dict(
                    system=platform.system(),
                    machine=platform.machine(),
                    python=platform.python_version(),
                ),
                elapsed_seconds=time.monotonic() - started,
                config=dict(
                    freeze=freeze,
                    embedder=embedder.identity,
                    **policy_configuration(embedder.identity, None),
                ),
                **outcome(rows, cases),
            )
        finally:
            connection.execute("SET search_path TO public")
            connection.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema))
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--model-directory", type=Path, default=Path("data/model"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists; preserve regression evidence")
    result = evaluate(args.root, args.model_directory)
    result["source_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=args.root, text=True
    ).strip()
    baseline = active_live_baseline(args.root)
    result["live_metrics_equal"] = deterministic_metrics(
        result["metrics"]
    ) == deterministic_metrics(baseline["metrics"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "coverage",
                    "replay_failures",
                    "live_metrics_equal",
                    "elapsed_seconds",
                )
            }
        )
    )
    return int(
        result["failed"]
        or bool(result["replay_failures"])
        or not result["live_metrics_equal"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
