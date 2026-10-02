import shlex
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_compose_published_ports_are_loopback_only():
    configuration = yaml.safe_load(
        (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")
    )
    mappings = [
        mapping
        for service in configuration["services"].values()
        for mapping in service.get("ports", [])
    ]
    assert mappings, "Expected at least one published port to check"
    for mapping in mappings:
        if isinstance(mapping, dict):
            host_ip = mapping.get("host_ip")
        else:
            host_ip = str(mapping).split(":", maxsplit=1)[0]
        assert host_ip == "127.0.0.1", f"Non-loopback port mapping: {mapping!r}"


def test_ci_run_steps_begin_with_make():
    workflow = yaml.safe_load(
        (REPOSITORY_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    )
    commands = [
        step["run"]
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "run" in step
    ]
    assert commands, "Expected at least one CI run step to check"
    for command in commands:
        tokens = shlex.split(command)
        assert tokens and tokens[0] == "make", f"Non-Makefile CI step: {command!r}"
