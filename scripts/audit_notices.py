import argparse
import hashlib
import importlib.metadata
import json
import tomllib

from scripts.audit_evidence import ROOT, markdown_table


def inventory(root=ROOT, installed=False):
    lock = root / "uv.lock"
    record = json.loads((root / "docs/audit/dependency-inventory.json").read_text())
    licences = json.loads((root / "docs/audit/dependency-licences.json").read_text())
    if hashlib.sha256(lock.read_bytes()).hexdigest() != record["lock_sha256"]:
        raise ValueError("notice_lock_digest")
    expected = {
        package["name"]: package["version"]
        for package in tomllib.loads(lock.read_text())["package"]
        if package["name"] != "rag-audit"
    }
    actual = {package["name"]: package["version"] for package in record["packages"]}
    if actual != expected or set(licences) != set(expected):
        raise ValueError("notice_lock_coverage")
    if len(actual) != len(record["packages"]):
        raise ValueError("notice_duplicate")
    for package in record["packages"]:
        name = package["name"]
        if not package["licence"] or not package["source"].startswith("https://"):
            raise ValueError("notice_metadata: " + name)
        texts = licences[name]
        if not texts or len(texts) != package["licence_file_count"]:
            raise ValueError("notice_licence_coverage: " + name)
        if any(not entry["text"].strip() for entry in texts):
            raise ValueError("notice_empty_licence: " + name)
        if installed:
            try:
                version = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                if name not in {"colorama", "tzdata"}:
                    raise ValueError("notice_metadata_missing: " + name) from None
            else:
                if version != package["version"]:
                    raise ValueError("notice_installed_version: " + name)
    return record, licences


def render(root=ROOT, check=False, installed=False):
    record, licences = inventory(root, installed)
    rows = [
        [
            package["name"],
            package["version"],
            package["licence"],
            "Review obligations"
            if package["review_required"]
            else "Retain attribution",
            f"[Publisher]({package['source']})",
        ]
        for package in record["packages"]
    ]
    sections = []
    for package in record["packages"]:
        name = package["name"]
        sections.append(f"## {name} {package['version']}\n")
        for entry in licences[name]:
            sections.append(
                f"Source file: `{entry['path']}`\n\n```text\n"
                f"{entry['text'].rstrip()}\n```\n"
            )
    text = (
        (root / "docs/audit/notices.template.md")
        .read_text()
        .replace(
            "{{inventory}}",
            markdown_table(
                ["Package", "Locked version", "Licence", "Obligation", "Source"], rows
            ),
        )
        .replace("{{count}}", str(len(rows)))
    )
    outputs = {
        "docs/third-party-notices.md": text.replace(
            "](dependency-", "](audit/dependency-"
        )
        .replace("](licence-texts.md)", "](audit/licence-texts.md)")
        .replace("](assets/", "](audit/assets/")
        .replace("](../../datasets/", "](../datasets/"),
        "docs/audit/licence-texts.md": "# Retained third-party licence texts\n\n"
        "Verbatim distribution notices; third-party authors retain their rights.\n\n"
        + "\n".join(sections),
    }
    for name, content in outputs.items():
        path = root / name
        if check:
            if path.read_text() != content:
                raise ValueError("notice_stale: " + name)
        else:
            path.write_text(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--installed", action="store_true")
    arguments = parser.parse_args()
    render(check=arguments.check, installed=arguments.installed)
