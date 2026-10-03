import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

from rag_audit.evaluation import live
from rag_audit.evaluation.__main__ import main as evaluation_main
from rag_audit.evaluation.replay import MODEL, fixture_entries
from rag_audit.evaluation_data import digest
from rag_audit.settings import Settings


def require_record_permission(opt_in: bool, reason: str | None, settings: Settings):
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        raise ValueError("record_forbidden: recording never runs in CI")
    if not opt_in or not reason or len(reason.strip()) < 20:
        raise ValueError("record_opt_in: explicit consent and written reason required")
    if not settings.generation_key_env or not os.environ.get(
        settings.generation_key_env
    ):
        raise ValueError("record_key: configured environment key required")


def sanitise(body: bytes, response: dict, status: int) -> dict:
    request = json.loads(body)
    request["model"] = MODEL
    output = []
    for item in response["output"]:
        if item["type"] == "reasoning":
            continue
        if item["type"] != "message":
            raise ValueError("record_schema: unrecognised output; review privately")
        output.append(
            dict(
                type="message",
                role=item["role"],
                status=item["status"],
                content=[
                    {
                        key: part[key]
                        for key in ("type", "text", "refusal")
                        if key in part
                    }
                    for part in item["content"]
                ],
            )
        )
    usage_keys = (
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cached_read_tokens",
        "cached_tokens",
        "cached_write_tokens",
        "cache_write_tokens",
    )
    usage = {
        key: response["usage"][key] for key in usage_keys if key in response["usage"]
    }
    for key, allowed in (
        ("input_tokens_details", usage_keys[3:]),
        ("output_tokens_details", ("reasoning_tokens",)),
    ):
        if key in response["usage"]:
            usage[key] = {
                name: value
                for name, value in response["usage"][key].items()
                if name in allowed
            }
    safe = dict(model=MODEL, status=response["status"], output=output, usage=usage)
    return dict(
        request_hash=digest(request),
        http_status=status,
        response=safe,
        response_digest=digest(safe),
    )


def write_candidates(directory: Path, entries: list[dict], commit: str):
    directory.mkdir()
    content = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
    (directory / "responses.json").write_text(content)
    manifest = dict(
        version="neutral-http-v1",
        source_commit=commit,
        recorded=str(date.today()),
        count=len(entries),
        sha256=hashlib.sha256(content.encode()).hexdigest(),
        request_hashes=[entry["request_hash"] for entry in entries],
        sanitisation="Neutral canonical request identity; allowlisted response fields. "
        "Candidate only: review every retained text and scan before promotion.",
    )
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    fixture_entries(directory)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-live-recording", action="store_true")
    parser.add_argument("--reason")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--forecast-baseline", type=Path, required=True)
    parser.add_argument("--model-directory", type=Path, default=Path("data/model"))
    args = parser.parse_args()
    require_record_permission(args.allow_live_recording, args.reason, Settings())
    if args.output.exists():
        raise ValueError("record_output: new version directory required")
    entries = []

    class CandidateTransport(live.RecordingTransport):
        async def handle_async_request(self, request):
            body = await request.aread()
            response = await super().handle_async_request(request)
            entries.append(sanitise(body, response.json(), response.status_code))
            return response

    arguments = [
        sys.argv[0],
        "--split",
        "all",
        "--embedder",
        "real",
        "--generator",
        "live",
        "--rerun-reason",
        args.reason,
        "--output",
        str(args.output),
        "--forecast-baseline",
        str(args.forecast_baseline),
        "--model-directory",
        str(args.model_directory),
    ]
    with (
        patch.object(sys, "argv", arguments),
        patch.object(live, "RecordingTransport", CandidateTransport),
    ):
        result = evaluation_main()
    if result:
        raise ValueError("record_failed: retain private evidence; no fixture promotion")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    write_candidates(args.output / "candidate-replay", entries, commit)
    print("Recording retained privately; review candidate-replay before promotion.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
