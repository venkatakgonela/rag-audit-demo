import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


def verify(directory: Path, manifest: dict) -> None:
    metadata = json.loads((directory / "identity.json").read_text())
    if any(metadata.get(key) != manifest[key] for key in ("model", "revision")):
        raise ValueError("model_identity: metadata mismatch")
    for name, expected in manifest["files"].items():
        content = (directory / name).read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        if (
            len(content) != expected["bytes"]
            or actual != expected["sha256"]
            or metadata["hashes"].get(name) != actual
        ):
            raise ValueError(
                "model_digest: cached file failed trusted manifest verification"
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("data/model"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("datasets/evaluation/model-manifest.json")
    )
    parser.add_argument("--provision", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if not args.directory.exists() and args.provision:
        args.directory.mkdir(parents=True)
        hashes = {}
        for name, expected in manifest["files"].items():
            url = f"https://huggingface.co/{manifest['model']}/resolve/{manifest['revision']}/{name}"
            with urlopen(url, timeout=180) as response:
                content = response.read(expected["bytes"] + 1)
            if (
                len(content) != expected["bytes"]
                or hashlib.sha256(content).hexdigest() != expected["sha256"]
            ):
                raise ValueError(
                    "model_digest: publisher download mismatched trusted manifest"
                )
            target = args.directory / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            hashes[name] = expected["sha256"]
        (args.directory / "identity.json").write_text(
            json.dumps(
                dict(
                    model=manifest["model"],
                    revision=manifest["revision"],
                    hashes=hashes,
                )
            )
        )
    verify(args.directory, manifest)
    print("model_integrity: PASS")


if __name__ == "__main__":
    main()
