import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ACTION_STEPS = {
    "checks": {0: "actions/checkout", 1: "astral-sh/setup-uv"},
    "integration": {0: "actions/checkout", 1: "astral-sh/setup-uv"},
    "evaluation": {
        0: "actions/checkout",
        1: "astral-sh/setup-uv",
        4: "actions/cache",
    },
}


def uses_references(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "uses":
                yield child
            else:
                yield from uses_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from uses_references(child)


def verify_workflow_actions(directory):
    references = []
    for path in directory.glob("*.y*ml"):
        text = path.read_text()
        workflow = yaml.safe_load(text)
        assert path.name == "ci.yml"
        assert set(workflow["jobs"]) == set(ACTION_STEPS)
        for name, job in workflow["jobs"].items():
            assert {
                index: step["uses"].split("@")[0]
                for index, step in enumerate(job["steps"])
                if "uses" in step
            } == ACTION_STEPS[name]
        for reference in uses_references(workflow):
            assert re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", reference), reference
            references.append(reference)
        assert len(
            re.findall(
                r"^\s*- uses: [^@\s]+@[0-9a-f]{40}[ \t]+# v\d+(?:\.\d+)*[ \t]*$",
                text,
                re.MULTILINE,
            )
        ) == len(list(uses_references(workflow)))
    assert len(references) == 7


def test_every_workflow_action_has_full_sha_and_version():
    verify_workflow_actions(ROOT / ".github/workflows")


@pytest.mark.parametrize("mutation", ["unpinned", "comment", "placement", "action"])
def test_workflow_action_guards_reject_deliberate_breaks(tmp_path, mutation):
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    match = re.search(r"actions/checkout@[0-9a-f]{40}", text)
    assert match is not None
    reference = match.group()
    if mutation == "unpinned":
        text = text.replace(reference, "actions/checkout@v7", 1)
    elif mutation == "comment":
        text = re.sub(re.escape(reference) + r"[^\n]*", reference, text, count=1)
    elif mutation == "placement":
        text = text.replace(
            "    steps:\n", "    steps:\n      - run: echo changed\n", 1
        )
    else:
        text = text.replace("actions/checkout@", "unexpected/action@", 1)
    (tmp_path / "ci.yml").write_text(text)
    with pytest.raises(AssertionError):
        verify_workflow_actions(tmp_path)


def test_workflow_action_guards_accept_another_full_sha(tmp_path):
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    text = re.sub(r"(?<=@)[0-9a-f]{40}", "a" * 40, text)
    (tmp_path / "ci.yml").write_text(text)
    verify_workflow_actions(tmp_path)


def test_dependabot_covers_actions_and_uv_weekly_with_bounded_prs():
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())
    assert config["version"] == 2
    updates = config["updates"]
    assert len(updates) == 2
    assert {entry["package-ecosystem"] for entry in updates} == {"github-actions", "uv"}
    for entry in updates:
        assert entry["directory"] == "/"
        assert entry["schedule"] == {"interval": "weekly"}
        assert entry["open-pull-requests-limit"] == 3


def test_readme_is_concise_and_keeps_disclosures_and_quickstart():
    text = (ROOT / "README.md").read_text()
    assert len(text.split()) <= 700
    for phrase in (
        "builder self-assessment",
        "not an independent audit or production service",
        "AI coding assistants",
        "not system-wide accuracy",
        "An AI reviewer checked all 65 labels",
        "not human review",
        "not independent",
        "every label remains `drafted`",
        "make generate-corpus",
        "Synthetic Hearth edition 1 drying diary reading",
        "broker reconciliation",
        "payout synthetic-claim-0",
        "CONTRIBUTING.md",
    ):
        assert phrase in text, phrase
    assert "No label has been reviewed" in text or re.search(
        r"\d+ of 65 labels reviewed by the project owner", text
    )


def test_community_files_and_owner_are_present():
    assert (ROOT / ".github/CODEOWNERS").read_text().strip() == "* @venkatakgonela"
    for name in (
        "CONTRIBUTING.md",
        ".github/pull_request_template.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/question.md",
    ):
        assert (ROOT / name).read_text().strip()
    assert "CONTRIBUTING.md" in (ROOT / "docs/README.md").read_text()
    assert not (ROOT / "launch.config.json").exists()


def test_owner_commands_are_not_in_public_provenance():
    text = (ROOT / "docs/PUBLISHING.md").read_text()
    assert "## Accepted historical exceptions" in text
    assert "## Read-only readiness checks (October 3, 2026)" in text
    for command in ("gh repo edit", "gh api", "gh release", "git tag", "git push"):
        assert command not in text
