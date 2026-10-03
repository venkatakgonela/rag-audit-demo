import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "actions/checkout": "d23441a48e516b6c34aea4fa41551a30e30af803",
    "astral-sh/setup-uv": "37802adc94f370d6bfd71619e3f0bf239e1f3b78",
    "actions/cache": "0057852bfaa89a56745cba8c7296529d2fc39830",
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


def test_every_workflow_action_has_exact_full_sha():
    references = []
    for path in (ROOT / ".github/workflows").glob("*.y*ml"):
        text = path.read_text()
        for reference in uses_references(yaml.safe_load(text)):
            assert re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", reference), reference
            name, revision = reference.split("@")
            assert PINS.get(name) == revision, reference
            assert re.search(re.escape(reference) + r"\s+# v\d+\b", text)
            references.append(reference)
    assert len(references) == 7
    assert {reference.split("@")[0] for reference in references} == set(PINS)


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
