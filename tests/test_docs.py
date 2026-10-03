import re
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ADR_DIRECTORY = DOCS / "decisions"
EXPECTED_CAPTIONS = {
    "System context",
    "Containers",
    "Components",
    "Question-answering sequence",
    "Data model",
    "Deployment",
}


def markdown_parts(text: str) -> tuple[str, list[str]]:
    prose: list[str] = []
    diagrams: list[str] = []
    fence = ""
    language = ""
    content: list[str] = []
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if marker and not fence:
            fence, language = marker.groups()
            language = language.strip().lower()
            content = []
        elif marker and fence:
            closing, suffix = marker.groups()
            if closing[0] == fence[0] and len(closing) >= len(fence):
                assert not suffix.strip(), "Nested or malformed code fence"
                if language == "mermaid":
                    diagram = "\n".join(content).strip()
                    assert diagram, "Empty Mermaid block"
                    diagrams.append(diagram)
                fence = ""
            else:
                content.append(line)
        elif fence:
            content.append(line)
        else:
            assert not re.match(r"^\s*(flowchart|sequenceDiagram|erDiagram)\b", line), (
                "Unfenced Mermaid source"
            )
            prose.append(line)
    assert not fence, "Unclosed code fence"
    return "\n".join(prose), diagrams


def link_targets(prose: str) -> list[str]:
    prose = re.sub(r"`+[^`\n]*`+", "", prose)
    definitions = {
        label.strip().casefold(): target.strip("<>")
        for label, target in re.findall(
            r"^\s{0,3}\[([^\]]+)\]:\s*(<[^>]+>|\S+)", prose, re.M
        )
    }
    inline = re.findall(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", prose)
    targets = [target.strip("<>") for target in inline]
    for label, reference in re.findall(r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]", prose):
        key = (reference or label).strip().casefold()
        assert key in definitions, f"Undefined link reference: {key}"
        targets.append(definitions[key])
    return targets + list(definitions.values())


def heading_anchors(text: str) -> set[str]:
    prose, _ = markdown_parts(text)
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", prose, re.M):
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(f"{slug}-{count}" if count else slug)
    return anchors


def assert_link_resolves(source: Path, target: str) -> None:
    address = urlsplit(target)
    if address.scheme or address.netloc:
        return
    destination = (
        (source.parent / unquote(address.path)).resolve() if address.path else source
    )
    assert destination.exists(), f"{source.name}: missing link target {target}"
    if address.fragment and destination.suffix == ".md":
        assert unquote(address.fragment) in heading_anchors(destination.read_text()), (
            f"{source.name}: missing heading in {target}"
        )


def assert_adr_index(directory: Path) -> None:
    prose, _ = markdown_parts((directory / "README.md").read_text())
    indexed = [
        target for target in link_targets(prose) if re.match(r"^\d{4}-.+\.md$", target)
    ]
    assert len(indexed) == len(set(indexed)), "Duplicate ADR index entry"
    actual = {path.name for path in directory.glob("[0-9][0-9][0-9][0-9]-*.md")}
    assert actual == set(indexed), (
        f"ADR index mismatch: unlisted={actual - set(indexed)}, "
        f"missing={set(indexed) - actual}"
    )


def test_adr_index_is_complete_both_ways():
    assert_adr_index(ADR_DIRECTORY)


@pytest.mark.parametrize(
    "path", sorted(ADR_DIRECTORY.glob("[0-9][0-9][0-9][0-9]-*.md"))
)
def test_adr_required_sections(path):
    prose, _ = markdown_parts(path.read_text())
    headings = set(re.findall(r"^#{2,6}\s+(.+)$", prose, re.M))
    required = {
        "Context",
        "Decision drivers",
        "Decision",
        "Consequences",
        "Revisit when",
    }
    assert required <= headings, f"{path.name}: missing sections {required - headings}"
    assert headings & {"Options considered", "Alternatives"}, path.name
    assert re.search(
        r"^Status: (Accepted|Proposed|Rejected|Superseded by \d{4})$", prose, re.M
    ), f"{path.name}: missing or invalid Status field"


def test_public_markdown_links_resolve():
    paths = (
        sorted(DOCS.rglob("*.md"))
        + sorted(ROOT.glob("*.md"))
        + sorted((ROOT / ".github").rglob("*.md"))
    )
    for source in paths:
        prose, _ = markdown_parts(source.read_text())
        for target in link_targets(prose):
            assert_link_resolves(source, target)


def test_architecture_mermaid_blocks_and_captions():
    prose, diagrams = markdown_parts((DOCS / "ARCHITECTURE.md").read_text())
    assert len(diagrams) >= 6, "Expected at least six architecture diagrams"
    captions = set(re.findall(r"^Caption: \*\*(.+?)\*\*", prose, re.M))
    assert EXPECTED_CAPTIONS <= captions, (
        f"Missing captions: {EXPECTED_CAPTIONS - captions}"
    )
    assert len(re.findall(r"^Legend:", prose, re.M)) >= len(diagrams)


def test_runtime_dependencies_have_catalogue_entries():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    catalogue, _ = markdown_parts((DOCS / "technology-choices.md").read_text())
    entries = {
        re.sub(r"[-_.]+", "-", name.lower())
        for name in re.findall(r"^### (\S+)$", catalogue, re.M)
    }
    requirements = list(project["project"]["dependencies"])
    for extra in project["project"].get("optional-dependencies", {}).values():
        requirements.extend(extra)
    for requirement in requirements:
        match = re.match(r"[A-Za-z0-9][A-Za-z0-9_.-]*", requirement)
        assert match, f"Unrecognised requirement: {requirement}"
        name = re.sub(r"[-_.]+", "-", match.group().lower())
        assert name in entries, f"Runtime dependency missing from catalogue: {name}"


@pytest.mark.parametrize(
    "text",
    ["```mermaid\n```", "```mermaid\nflowchart LR", "flowchart LR\nA --> B"],
)
def test_invalid_mermaid_fences_are_rejected(text):
    with pytest.raises(AssertionError):
        markdown_parts(text)


def test_fences_ignore_literal_links_and_accept_tildes():
    prose, diagrams = markdown_parts(
        "```text\n[example](missing.md)\n```\n~~~mermaid\nflowchart LR\nA --> B\n~~~"
    )
    assert link_targets(prose) == []
    assert diagrams == ["flowchart LR\nA --> B"]


def test_reference_links_and_missing_references():
    assert link_targets("[guide][intro]\n[intro]: guide.md") == ["guide.md", "guide.md"]
    with pytest.raises(AssertionError, match="Undefined link reference"):
        link_targets("[guide][absent]")


def test_relative_links_and_heading_failures(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("# Source")
    target = tmp_path / "target.md"
    target.write_text("# Target\n## Repeated\n## Repeated")
    assert_link_resolves(source, "target.md#repeated-1")
    assert_link_resolves(source, "#source")
    assert_link_resolves(source, "https://example.invalid/not-fetched")
    with pytest.raises(AssertionError, match="missing link target"):
        assert_link_resolves(source, "absent.md")
    with pytest.raises(AssertionError, match="missing heading"):
        assert_link_resolves(source, "target.md#absent")


@pytest.mark.parametrize("indexed, actual", [(True, False), (False, True)])
def test_adr_index_rejects_both_mismatch_directions(tmp_path, indexed, actual):
    (tmp_path / "README.md").write_text(
        "[ADR](0001-example.md)" if indexed else "# Index"
    )
    if actual:
        (tmp_path / "0001-example.md").write_text("# Example")
    with pytest.raises(AssertionError, match="ADR index mismatch"):
        assert_adr_index(tmp_path)
