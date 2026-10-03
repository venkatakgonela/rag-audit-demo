import json
from pathlib import Path

from rag_audit.corpus import generate


def revised_corpus(directory: Path, suffix: str) -> dict:
    manifest = generate(directory)
    manifest["version"] += "-" + suffix
    (directory / "manifest.json").write_text(json.dumps(manifest))
    return manifest
