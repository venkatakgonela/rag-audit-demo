import hashlib
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "datasets/corpus-v3"


def validate_sources(directory: Path, manifest: dict) -> None:
    if not manifest["version"].startswith("synthetic-v3-"):
        raise ValueError("Corpus v3 required")
    records = {
        record["id"]: record for record in manifest["policies"] + manifest["claims"]
    }
    sources = {}
    for document in manifest["documents"]:
        path = (directory / document["path"]).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError("Source path escapes corpus")
        text = path.read_text(encoding="utf-8")
        if (
            "SYNTHETIC" not in text
            or hashlib.sha256(text.encode()).hexdigest() != document["sha256"]
        ):
            raise ValueError("Source label or hash mismatch")
        sources[document["id"]] = text
    seen = set()
    for binding in manifest["bindings"]:
        identifier, field, quote = (
            binding["record"],
            binding["field"],
            binding["quote"],
        )
        value = records[identifier][field]
        rendered = ", ".join(value) if isinstance(value, list) else str(value)
        labels = {
            "currency": f"Currency: {rendered}.",
            "excess": f"Excess: GBP {rendered}.",
            "limit": f"Limit: GBP {rendered}.",
            "covered": f"Covered perils: {rendered}.",
            "window": f"Notification window: {rendered} days.",
        }
        expected = labels.get(field, f"{field.title()}: {rendered}.")
        if quote != expected or quote not in sources[identifier]:
            raise ValueError("Structured prose mismatch")
        if (identifier, field) in seen:
            raise ValueError("Duplicate source binding")
        seen.add((identifier, field))
    required = {
        (identifier, field)
        for identifier, record in records.items()
        for field in record
        if field not in ("id", "document_id")
    }
    if seen != required:
        raise ValueError("Missing source binding")


def generate(directory: Path, seed: int = 42) -> dict:
    if seed != 42:
        raise ValueError("Static corpus does not support alternate seeds")
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    validate_sources(SOURCE, manifest)
    directory.mkdir(parents=True, exist_ok=True)
    for document in manifest["documents"]:
        target = directory / document["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((SOURCE / document["path"]).read_bytes())
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
