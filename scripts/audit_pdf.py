import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from scripts.audit_evidence import ROOT, render


def asset_uri(path):
    types = {".ttf": "font/ttf", ".png": "image/png"}
    return (
        "data:"
        + types[path.suffix]
        + ";base64,"
        + base64.b64encode(path.read_bytes()).decode()
    )


def html_document(root=ROOT):
    directory = root / "docs/audit"
    provenance = json.loads((directory / "assets/fonts/provenance.json").read_text())
    for entry in provenance["files"]:
        if (
            hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest()
            != entry["sha256"]
        ):
            raise ValueError("audit_font_digest")
    result = subprocess.run(
        [
            "pandoc",
            "--standalone",
            "--from=markdown",
            "--to=html5",
            str(directory / "report.md"),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    result = re.sub(r"<style>.*?</style>", "", result, flags=re.S)
    css = (directory / "print.css").read_text()
    css = re.sub(
        r'url\("([^"]+)"\)',
        lambda match: 'url("' + asset_uri(directory / match[1]) + '")',
        css,
    )
    result = re.sub(
        r'src="(figures/[^"]+\.png)"',
        lambda match: 'src="' + asset_uri(directory / match[1]) + '"',
        result,
    )
    if re.search(r'(?:src|href)="(?:file:|/)', result):
        raise ValueError("audit_absolute_resource")
    policy = (
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; img-src data:; "
        "font-src data:; style-src 'unsafe-inline'\">"
    )
    return result.replace("</head>", policy + "<style>" + css + "</style></head>")


def build(root=ROOT):
    render(root)
    chrome = (
        os.environ.get("AUDIT_CHROME")
        or shutil.which("google-chrome")
        or shutil.which("chromium")
    )
    if not chrome:
        candidate = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        chrome = str(candidate) if candidate.is_file() else None
    if not chrome:
        raise ValueError(
            "Installed Chrome required; set AUDIT_CHROME. No automatic download."
        )
    module = os.environ.get("AUDIT_PUPPETEER_MODULE")
    if not module:
        cached = sorted(
            Path.home().glob(
                ".npm/_npx/*/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js"
            )
        )
        module = str(cached[0]) if cached else None
    if not module:
        raise ValueError("Existing Puppeteer required; set AUDIT_PUPPETEER_MODULE.")
    with tempfile.TemporaryDirectory(prefix="synthetic-audit-") as temporary:
        directory = Path(temporary)
        source = directory / "report.html"
        source.write_text(html_document(root))
        output = directory / "report.pdf"
        subprocess.run(
            [
                "node",
                str(root / "scripts/audit_chrome.mjs"),
                module,
                chrome,
                str(source),
                str(output),
            ],
            check=True,
            timeout=90,
        )
        info = subprocess.run(
            ["pdfinfo", str(output)], check=True, capture_output=True, text=True
        ).stdout
        pages = int(re.search(r"Pages:\s+(\d+)", info)[1])
        if not 9 <= pages <= 14:
            raise ValueError(f"audit_pages: {pages}; required 9-14")
        text = subprocess.run(
            ["pdftotext", str(output), "-"], check=True, capture_output=True, text=True
        ).stdout
        if "file:///" in text + info or str(directory) in text + info:
            raise ValueError("audit_local_path")
        shutil.copyfile(output, root / "docs/audit/report.pdf")
        print(
            f"Audit report: {pages} pages; text SHA256 "
            f"{hashlib.sha256(text.encode()).hexdigest()}"
        )


if __name__ == "__main__":
    build()
