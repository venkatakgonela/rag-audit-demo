import argparse
import hashlib
import json
import re
from pathlib import Path

from rag_audit.evaluation.metrics import rate
from rag_audit.evaluation.reporting import deterministic_metrics
from rag_audit.evaluation_data import check_dataset, digest, read_json

ROOT = Path(__file__).resolve().parents[1]
BASE = "cfd53ff1cf8028dba24e44008f1c910f31de8132"
ATTESTATION = "e33d5806bd659eb7cbe39eb0b954461e2cdd1416"
DATE = "2026-10-03"
BASELINES = ("fake-v1", "real-v1", "live-v1", "live-v2")


def review_wording(reviewed, total):
    if reviewed == 0:
        return (
            "No label has been reviewed by anyone other than the author "
            f"({total} labels)."
        )
    return (
        f"{reviewed} of {total} labels reviewed by the project owner, "
        "who is not independent of the project."
    )


def markdown_table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]
        + ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    )


def interval(hits, total):
    measure = rate(hits, total)
    if not total:
        return "not applicable"
    lower, upper = measure["interval"]
    return f"{hits}/{total} ({lower * 100:.1f}-{upper * 100:.1f}%)"


def source_note(paths):
    return (
        "\n\nSource: "
        + ", ".join(f"`{path}` at `{source_commit(path)}`" for path in paths)
        + ". Full hashes: docs/audit/evidence-manifest.json."
    )


def source_commit(path):
    return ATTESTATION[:7] if path.startswith("docs/audit/") else BASE[:7]


def collect(root=ROOT):
    check_dataset(root)
    directory = root / "datasets/evaluation"
    manifest = read_json(root / "docs/audit/evidence-manifest.json")
    required = {
        *(f"datasets/evaluation/baselines/{name}.json" for name in BASELINES),
        "datasets/evaluation/freeze.json",
        "datasets/evaluation/run-log.jsonl",
        "docs/decisions/0030-abstention-recalibration.md",
        "docs/audit/findings.json",
        "docs/audit/verification-evidence.json",
    }
    if manifest["audited_commit"] != BASE or not required <= manifest["sources"].keys():
        raise ValueError("audit_manifest: missing source or wrong revision")
    for path, expected in manifest["sources"].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
            raise ValueError("audit_digest: " + path)
    labels = [
        case
        for split in ("dev", "test")
        for case in read_json(directory / f"{split}.json")["cases"]
    ]
    reviewed = sum(case["label_status"] == "reviewed" for case in labels)
    baselines = {}
    for name in BASELINES:
        baseline = read_json(directory / "baselines" / f"{name}.json")
        if (
            digest(deterministic_metrics(baseline["metrics"]))
            != baseline["metrics_digest"]
        ):
            raise ValueError("audit_metrics: " + name)
        if digest(baseline["config"]) != baseline["config_digest"]:
            raise ValueError("audit_configuration: " + name)
        rows = baseline.get("rows", baseline.get("phrasing_outcomes"))
        if rows is None or len(rows) != baseline["coverage"]["expected"]:
            raise ValueError("audit_coverage: " + name)
        baselines[name] = baseline
    before = baselines["live-v1"]["phrasing_outcomes"]
    after = baselines["live-v2"]["rows"]
    safety = []
    for name, baseline in baselines.items():
        for split in ("dev", "test"):
            group = baseline["metrics"]["groups"]["split:" + split]
            safety.append(
                [
                    name,
                    split,
                    group["requests"],
                    group["hard_failures"],
                    group["errors"],
                    group["false_answer"]["hits"],
                ]
            )
    comparison = []
    for split in ("dev", "test"):
        for style in ("keyword", "natural"):
            cells = []
            for rows in (before, after):
                chosen = [
                    row
                    for row in rows
                    if row["split"] == split
                    and row["style"] == style
                    and row["category"] in ("single", "multi")
                ]
                cells.append(
                    interval(
                        sum(row["assessment"]["correct"] for row in chosen), len(chosen)
                    )
                )
            comparison.append([split, style, *cells])
    categories = []
    for split in ("dev", "test"):
        for category in sorted({row["category"] for row in after}):
            values = []
            for rows in (before, after):
                chosen = [
                    row
                    for row in rows
                    if row["split"] == split and row["category"] == category
                ]
                values.append(
                    f"{sum(row['assessment']['correct'] for row in chosen)}"
                    f"/{len(chosen)}"
                )
            categories.append([split, category, *values])
    outcomes = []
    for split in ("dev", "test"):
        group = baselines["live-v2"]["metrics"]["groups"]["split:" + split]
        outcomes.append(
            [
                split,
                *[
                    group[key]["hits"]
                    for key in (
                        "model_abstention",
                        "gate_abstention",
                        "verification_rejection",
                        "false_answer",
                        "false_evidence",
                    )
                ],
            ]
        )
    costs = []
    for name in ("live-v1", "live-v2"):
        for split in ("dev", "test"):
            group = baselines[name]["metrics"]["groups"]["split:" + split]
            latency = group["latency"].get("True", {}).get("generate", {})
            costs.append(
                [
                    name,
                    split,
                    group["provider_calls"],
                    group["estimated_cost"],
                    group["unknown_cost"],
                    f"{latency['p50']:.4f}",
                    f"{latency['p95']:.4f}",
                ]
            )
    events = [
        json.loads(line)
        for line in (directory / "run-log.jsonl").read_text().splitlines()
    ]
    starts = [event for event in events if event["event"] == "started"]
    findings = read_json(root / "docs/audit/findings.json")
    identifiers = set()
    for finding in findings:
        if set(finding) != {
            "id",
            "title",
            "severity",
            "status",
            "confidence",
            "description",
            "evidence",
            "recommendation",
            "effort",
        }:
            raise ValueError("audit_finding: incomplete fields")
        if finding["id"] in identifiers or not re.fullmatch(r"F-\d{2}", finding["id"]):
            raise ValueError("audit_finding: duplicate or invalid ID")
        identifiers.add(finding["id"])
        if (
            finding["severity"]
            not in {"Critical", "High", "Medium", "Low", "Informational"}
            or finding["status"] not in {"open", "mitigated", "accepted"}
            or finding["confidence"] not in {"high", "medium", "low"}
        ):
            raise ValueError("audit_finding: invalid classification")
        if not finding["evidence"] or not finding["recommendation"]:
            raise ValueError("audit_finding: missing support")
        for path in finding["evidence"]:
            if not (root / path).is_file():
                raise ValueError("audit_reference: " + path)
    verification = read_json(root / "docs/audit/verification-evidence.json")
    runs = [
        [
            entry["run_id"],
            ", ".join(job["name"] + ": " + job["conclusion"] for job in entry["jobs"]),
        ]
        for entry in verification["observations"]
        if entry["kind"] == "verified-from-run-log"
    ]
    candidate_text = (
        root / "docs/decisions/0030-abstention-recalibration.md"
    ).read_text()
    candidate_rows = [
        line for line in candidate_text.splitlines() if re.match(r"\| 0\.\d+ \|", line)
    ]
    if len(candidate_rows) != 4:
        raise ValueError("audit_candidates: incomplete committed grid")
    denominator = sum(
        case["category"] in ("single", "multi")
        for case in read_json(directory / "dev.json")["cases"]
    )
    candidate_headers = [
        "Gate",
        f"Natural /{denominator}",
        f"Keyword /{denominator}",
        "Free-text false",
        "Eligible",
    ]
    proof_rows = [
        [entry["run_id"], check["name"], check["baseline"], check["current"]]
        for entry in verification["observations"]
        if entry["kind"] == "verified-from-run-log"
        for check in entry["gate_checks"]
        if check["result"] == "FAIL"
    ]
    selftests = [
        [
            entry["run_id"],
            ", ".join(map(str, entry["selftest_pass_counts"]))
            or "No passing result recorded",
        ]
        for entry in verification["observations"]
        if entry["kind"] == "verified-from-run-log"
    ]
    sources = [f"datasets/evaluation/baselines/{name}.json" for name in BASELINES]
    tables = dict(
        safety=markdown_table(
            ["Reference", "Split", "Primary n", "Hard", "Errors", "False answers"],
            safety,
        )
        + source_note(sources),
        comparison=markdown_table(
            [
                "Split",
                "Style",
                "Before correct; Wilson 95%",
                "After correct; Wilson 95%",
            ],
            comparison,
        )
        + source_note(sources[2:]),
        categories=markdown_table(
            ["Split", "Category", "Before correct", "After correct"], categories
        )
        + source_note(sources[2:]),
        outcomes=markdown_table(
            [
                "Split",
                "Model refusal",
                "Gate refusal",
                "Rejected",
                "False answers",
                "False evidence",
            ],
            outcomes,
        )
        + source_note([sources[-1]]),
        costs=markdown_table(
            [
                "Reference",
                "Split",
                "Logical calls",
                "USD estimate",
                "Unknown",
                "Generate p50 s",
                "p95 s",
            ],
            costs,
        )
        + source_note(sources[2:]),
        candidates=markdown_table(
            candidate_headers,
            [
                [cell.strip() for cell in row.strip("|").split("|")]
                for row in candidate_rows
            ],
        )
        + source_note(["docs/decisions/0030-abstention-recalibration.md"]),
        runs=markdown_table(["Hosted run", "Job conclusions"], runs)
        + source_note(["docs/audit/verification-evidence.json"]),
        proof=markdown_table(
            ["Proof run", "Failed gate check", "Reference", "Observed"], proof_rows
        )
        + source_note(["docs/audit/verification-evidence.json"]),
        selftests=markdown_table(["Hosted run", "Passing self-tests"], selftests)
        + source_note(["docs/audit/verification-evidence.json"]),
        severities=markdown_table(
            ["Severity", "Findings"],
            [
                [level, sum(item["severity"] == level for item in findings)]
                for level in ("Critical", "High", "Medium", "Low", "Informational")
            ],
        )
        + source_note(["docs/audit/findings.json"]),
    )
    return dict(
        tables=tables,
        review=review_wording(reviewed, len(labels)),
        label_count=len(labels),
        reviewed=reviewed,
        starts=len(starts),
        live_starts=sum("live" in event["config"]["generator"] for event in starts),
        injection_cases=sum(case["category"] == "injection" for case in labels),
        retained_estimate=baselines["live-v2"]["live"]["retained_estimate"],
        final_spend=baselines["live-v2"]["live"]["phase_spend"]["final"],
        findings=findings,
    )


def render(root=ROOT, check=False):
    data = collect(root)
    replacements = {
        **data["tables"],
        "review": data["review"],
        "commit": BASE,
        "date": DATE,
        "exposures": str(data["starts"]),
        "live_exposures": str(data["live_starts"]),
        "injection_cases": str(data["injection_cases"]),
        "retained_estimate": data["retained_estimate"],
        "final_spend": data["final_spend"],
    }
    for start, stop, name in (
        (0, 4, "findings_a"),
        (4, 9, "findings_b"),
        (9, 13, "findings_c"),
    ):
        sections = []
        for finding in data["findings"][start:stop]:
            sections.append(
                f"### {finding['id']}: {finding['title']}\n\n"
                f"**{finding['severity']} | {finding['status']} | "
                f"confidence: {finding['confidence']}**\n\n"
                f"{finding['description']}\n\nEvidence: "
                + "; ".join(
                    f"`{path}` at `{source_commit(path)}`"
                    for path in finding["evidence"]
                )
                + f".\n\nRecommendation ({finding['effort']}): "
                + f"{finding['recommendation']}\n"
            )
        replacements[name] = "\n".join(sections)
    replacements["roadmap"] = markdown_table(
        ["Finding", "Status", "Effort", "Area to address (details in findings)"],
        [
            [item["id"], item["status"], item["effort"], item["title"]]
            for item in data["findings"]
        ],
    )
    for template, destination in (
        ("docs/audit/report.template.md", "docs/audit/report.md"),
        ("docs/audit/readme.template.md", "README.md"),
    ):
        text = (root / template).read_text()
        for key, value in replacements.items():
            text = text.replace("{{" + key + "}}", value)
        if re.search(r"\{\{[^}]+\}\}", text):
            raise ValueError("audit_template: unresolved variable")
        if destination == "README.md":
            text = text.replace("](../../", "](")
        path = root / destination
        if check:
            if path.read_text() != text:
                raise ValueError("audit_stale: " + destination)
        else:
            path.write_text(text)
    text = json.dumps(data, indent=2) + "\n"
    path = root / "docs/audit/tables.json"
    if check:
        if path.read_text() != text:
            raise ValueError("audit_stale: tables")
    else:
        path.write_text(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    render(check=arguments.check)
