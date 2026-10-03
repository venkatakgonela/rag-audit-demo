import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from rag_audit.embeddings import OnnxEmbedder
from rag_audit.evaluation.data import load_split
from rag_audit.evaluation.gate_checks import check_rows, measures
from rag_audit.evaluation.regression import evaluate
from rag_audit.evaluation.validation import policy_configuration
from rag_audit.evaluation_data import digest, read_json
from rag_audit.settings import Settings


def configuration(root: Path) -> dict:
    directory = root / "datasets/evaluation"
    return dict(
        freeze=read_json(directory / "freeze.json"),
        model=read_json(directory / "model-manifest.json"),
        fixtures=read_json(directory / "replay/manifest.json"),
        policy=read_json(directory / "gate-policy.json"),
        profile=policy_configuration(OnnxEmbedder.identity, None),
        settings={
            key: value
            for key, value in Settings().model_dump(mode="json").items()
            if key
            not in (
                "database_url",
                "database_connect_timeout",
                "stub_signing_key",
                "generation_base_url",
                "generation_model",
                "generation_reported_model",
                "generation_key_env",
                "generation_backend",
                "generation_price_source",
                "generation_price_version",
                "generation_input_price",
                "generation_cached_price",
                "generation_write_price",
                "generation_output_price",
            )
        },
        replay_contract="neutral-http-v1",
    )


def integrity(root: Path, baseline: dict) -> None:
    directory = root / "datasets/evaluation"
    config = configuration(root)
    if baseline["config"] != config or baseline["config_digest"] != digest(config):
        raise ValueError("baseline_config: current frozen configuration differs")
    events = [
        json.loads(line)
        for line in (directory / "gate-baseline-log.jsonl").read_text().splitlines()
    ]
    if not events or events[-1]["baseline_digest"] != digest(baseline):
        raise ValueError("baseline_log: baseline changed without matching log")
    previous = None
    for event in events:
        if event["previous_digest"] != previous:
            raise ValueError("baseline_log: broken baseline history chain")
        if (
            not event["reason"].strip()
            or not event["marker"]
            or event["marker"] not in (root / "CHANGELOG.md").read_text()
        ):
            raise ValueError(
                "baseline_reason: log requires reason and changelog marker"
            )
        previous = event["baseline_digest"]


def protected(root: Path) -> dict:
    directory = root / "datasets/evaluation"
    paths = [
        directory / "run-log.jsonl",
        directory / "freeze.json",
        directory / "dev.json",
        directory / "test.json",
        *sorted((directory / "baselines").glob("*.json")),
        *sorted((root / "datasets/corpus-v3").rglob("*.md")),
        root / "datasets/corpus-v3/manifest.json",
    ]
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def expected_rows(root):
    return {
        (case.id, phrasing.style)
        for split in ("dev", "test")
        for case in load_split(root, split)
        for phrasing in case.phrasings
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--model-directory", type=Path, default=Path("data/model"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--rebaseline", action="store_true")
    parser.add_argument("--reason")
    parser.add_argument("--marker")
    args = parser.parse_args()
    directory = args.root / "datasets/evaluation"
    if args.rebaseline and (
        os.environ.get("CI")
        or os.environ.get("GITHUB_ACTIONS")
        or not args.reason
        or len(args.reason.strip()) < 20
        or not args.marker
        or args.marker not in (args.root / "CHANGELOG.md").read_text()
    ):
        raise ValueError(
            "rebaseline_opt_in: local written reason and changelog marker required"
        )
    before = protected(args.root)
    baseline = (
        None if args.rebaseline else read_json(directory / "baselines/ci-v1.json")
    )
    if baseline is not None:
        integrity(args.root, baseline)
    result = evaluate(args.root, args.model_directory)
    if args.rebaseline:
        if result["failed"] or result["replay_failures"]:
            raise ValueError(
                "rebaseline_failed: cannot baseline safety/incomplete/replay failures"
            )
        config = configuration(args.root)
        baseline = dict(
            version="ci-v1",
            config=config,
            config_digest=digest(config),
            measures=measures(result["rows"]),
            metrics=result["metrics"],
            counterfactuals=sum("counterfactual" in row for row in result["rows"]),
        )
        path = directory / "baselines/ci-v1.json"
        old_digest = digest(read_json(path)) if path.exists() else None
        path.write_text(json.dumps(baseline, indent=2) + "\n")
        event = dict(
            baseline_digest=digest(baseline),
            previous_digest=old_digest,
            reason=args.reason,
            marker=args.marker,
            commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=args.root, text=True
            ).strip(),
        )
        with (directory / "gate-baseline-log.jsonl").open("a") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    assert baseline is not None
    checks = check_rows(
        result["rows"],
        baseline,
        configuration(args.root)["policy"],
        expected_rows(args.root),
        result["replay_failures"],
    )
    if not args.rebaseline and protected(args.root) != before:
        raise ValueError("protected_inputs: regression changed baseline/exposure files")
    output = (
        args.output or Path(tempfile.mkdtemp(prefix="synthetic-gate-")) / "checks.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            dict(
                checks=checks,
                platform=result["platform"],
                elapsed_seconds=result["elapsed_seconds"],
            ),
            indent=2,
        )
        + "\n"
    )
    for check in checks:
        print(
            f"{check['check']} | {check['baseline']} | {check['current']} | "
            f"{'PASS' if check['passed'] else 'FAIL'}"
        )
    passed = all(check["passed"] for check in checks)
    print("Evaluation gate: " + ("PASS" if passed else "FAIL"))
    return int(not passed)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, FileNotFoundError) as error:
        print("Evaluation gate: FAIL (integrity/configuration); " + str(error))
        raise SystemExit(1) from None
