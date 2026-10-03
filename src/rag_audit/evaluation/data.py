import fcntl
import json
import os
from pathlib import Path

from rag_audit.evaluation_data import Golden, digest, read_json, semantic_cases


def load_split(root: Path, split: str):
    if split not in ("dev", "test"):
        raise ValueError("Unknown split")
    directory = root / "datasets/evaluation"
    freeze = read_json(directory / "freeze.json")
    if freeze["state"] != "accepted":
        raise ValueError("Accepted freeze required")
    data = read_json(directory / f"{split}.json")
    if digest(semantic_cases(data)) != freeze["digests"][split]:
        raise ValueError("Split digest mismatch")
    for key, path in (
        ("corpus", root / "datasets/corpus-v3/manifest.json"),
        ("access", directory / "access-intent.json"),
        ("chunks", directory / "chunk-references.json"),
    ):
        if digest(read_json(path)) != freeze["digests"][key]:
            raise ValueError("Configuration digest mismatch")
    cases = Golden.model_validate(data).cases
    if any(case.split != split for case in cases):
        raise ValueError("Cross-split label")
    return cases


def append_event(path: Path, event: dict) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(event, sort_keys=True) + "\n")
        output.flush()
        os.fsync(output.fileno())


def start_test_run(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as output:
        fcntl.flock(output.fileno(), fcntl.LOCK_EX)
        output.seek(0)
        if any(
            json.loads(line).get("key") == event["key"] for line in output
        ) and not event.get("rerun_reason"):
            raise ValueError("Test configuration already attempted; review required")
        output.write(json.dumps(event, sort_keys=True) + "\n")
        output.flush()
        os.fsync(output.fileno())
