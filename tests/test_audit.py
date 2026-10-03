import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest

from scripts import audit_evidence, audit_notices, audit_pdf

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def audit_copy(tmp_path):
    for name in ("datasets", "docs", "src", "tests", ".github"):
        shutil.copytree(ROOT / name, tmp_path / name)
    for name in ("uv.lock", "README.md"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    return tmp_path


def update_manifest(root, path):
    manifest_path = root / "docs/audit/evidence-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["sources"][path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))


def test_audit_generated_files_match_sources():
    audit_evidence.render(check=True)
    audit_notices.render(check=True)


def test_audit_counts_match_raw_rows():
    data = audit_evidence.collect()
    baseline = json.loads(
        (ROOT / "datasets/evaluation/baselines/live-v2.json").read_text()
    )
    for split in ("dev", "test"):
        for style in ("keyword", "natural"):
            rows = [
                row
                for row in baseline["rows"]
                if row["split"] == split
                and row["style"] == style
                and row["category"] in ("single", "multi")
            ]
            hits = sum(row["assessment"]["correct"] for row in rows)
            assert f"{hits}/{len(rows)} (" in data["tables"]["comparison"]
    assert data["label_count"] == sum(
        len(
            json.loads((ROOT / f"datasets/evaluation/{split}.json").read_text())[
                "cases"
            ]
        )
        for split in ("dev", "test")
    )


def test_audit_source_tamper_fails(audit_copy):
    path = audit_copy / "datasets/evaluation/baselines/live-v2.json"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="audit_digest"):
        audit_evidence.collect(audit_copy)


def test_audit_missing_manifest_entry_fails(audit_copy):
    path = audit_copy / "docs/audit/evidence-manifest.json"
    data = json.loads(path.read_text())
    del data["sources"]["datasets/evaluation/baselines/live-v2.json"]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="audit_manifest"):
        audit_evidence.collect(audit_copy)


def test_audit_missing_source_fails(audit_copy):
    (audit_copy / "datasets/evaluation/baselines/live-v2.json").unlink()
    with pytest.raises(FileNotFoundError):
        audit_evidence.collect(audit_copy)


def test_audit_stale_table_fails(audit_copy):
    path = audit_copy / "docs/audit/report.md"
    path.write_text(path.read_text().replace("9/18", "18/18"))
    with pytest.raises(ValueError, match="audit_stale"):
        audit_evidence.render(audit_copy, check=True)


@pytest.mark.parametrize(
    "field,value", [("severity", "Perfect"), ("evidence", ["missing.py"])]
)
def test_audit_invalid_finding_fails(audit_copy, field, value):
    relative = "docs/audit/findings.json"
    path = audit_copy / relative
    findings = json.loads(path.read_text())
    findings[0][field] = value
    path.write_text(json.dumps(findings))
    update_manifest(audit_copy, relative)
    with pytest.raises(ValueError, match="audit_finding|audit_reference"):
        audit_evidence.collect(audit_copy)


def test_audit_review_count_rebuilds_without_semantic_label_edits(audit_copy):
    initial = audit_evidence.collect(audit_copy)
    path = audit_copy / "datasets/evaluation/dev.json"
    dataset = json.loads(path.read_text())
    original = dataset["cases"][0]["label_status"]
    dataset["cases"][0]["label_status"] = "reviewed"
    path.write_text(json.dumps(dataset))
    audit_evidence.render(audit_copy)
    expected = initial["reviewed"] + (original != "reviewed")
    assert audit_evidence.collect(audit_copy)["reviewed"] == expected
    assert (
        f"{expected} of {initial['label_count']} labels reviewed"
        in (audit_copy / "README.md").read_text()
    )
    assert "not independent" in (audit_copy / "docs/audit/report.md").read_text()


def test_audit_zero_review_wording():
    assert "No label" in audit_evidence.review_wording(0, 65)
    assert "3 of 65" in audit_evidence.review_wording(3, 65)


def test_audit_cited_paths_exist():
    report = (ROOT / "docs/audit/report.md").read_text()
    paths = re.findall(r"`((?:src|tests|docs|datasets|\.github)/[^`]+)`", report)
    assert paths
    for path in paths:
        assert (ROOT / path).exists(), path


def test_notice_lock_tamper_fails(audit_copy):
    path = audit_copy / "uv.lock"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="notice_lock_digest"):
        audit_notices.inventory(audit_copy)


def test_notice_missing_package_fails(audit_copy):
    path = audit_copy / "docs/audit/dependency-inventory.json"
    data = json.loads(path.read_text())
    data["packages"].pop()
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="notice_lock_coverage"):
        audit_notices.inventory(audit_copy)


def test_notice_empty_licence_fails(audit_copy):
    path = audit_copy / "docs/audit/dependency-licences.json"
    data = json.loads(path.read_text())
    data["flatbuffers"][0]["text"] = ""
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="notice_empty_licence"):
        audit_notices.inventory(audit_copy)


def test_pdf_html_embeds_assets_and_blocks_external_resources(monkeypatch):
    class Result:
        stdout = (
            "<html><head><style>default styles</style></head><body>"
            '<img src="figures/components.png"></body></html>'
        )

    monkeypatch.setattr(audit_pdf.subprocess, "run", lambda *args, **kwargs: Result())
    html = audit_pdf.html_document()
    assert "default styles" not in html
    assert 'src="data:image/png;base64,' in html
    assert "data:font/ttf;base64," in html
    assert "default-src 'none'" in html
    assert "file:///" not in html


def test_pdf_font_tamper_fails(audit_copy):
    font = audit_copy / "docs/audit/assets/fonts/NotoSans.ttf"
    font.write_bytes(b"incorrect font")
    with pytest.raises(ValueError, match="audit_font_digest"):
        audit_pdf.html_document(audit_copy)
