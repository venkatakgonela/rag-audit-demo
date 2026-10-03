# Sample audit report

Read the [PDF](report.pdf) or [Markdown](report.md). This is a builder's
self-assessment on synthetic data, not independent assurance or a production claim.

## Rebuild offline

Prerequisites: the locked Python environment, installed pandoc and headless Chrome,
and Poppler (`pdfinfo`, `pdftotext`), Node and an existing Puppeteer installation
(the Mermaid CLI's cached copy is supported). Set `AUDIT_PUPPETEER_MODULE` to its
ES module entry point if not in the local package cache. No automatic install or
download occurs.
Set `AUDIT_CHROME` only if the installed browser is not detected. Normal builds
never run package managers for browser tools. Run:

```sh
make audit-report
make audit-check
```

The build checks frozen semantic labels, source SHA-256 hashes, baseline metric
and configuration digests, finding references, and font hashes; then generates
Markdown, README and tables before rendering a self-contained HTML document.
Its content security policy permits only embedded image/font bytes and inline
styles. Browser background networking and DNS resolution are disabled. Nothing
in the report needs a remote resource. Links are citations, not fetched assets.
The browser's default URL/date header is disabled; the report has its own footer.

The target is 10–12 A4 pages; builds fail outside 9–14. Compare extracted text and
`tables.json`, not PDF bytes: browser timestamps can differ. Render every page
with `pdftoppm` and inspect at readable scale. The full PDF is committed so
reading it needs no build tools. CI does not build the PDF.

## Evidence and interpretation

The audited product revision is pinned separately from the later findings and
hosted-run attestation. Each generated table states its source revision; source
digests are in [the manifest](evidence-manifest.json). Report templates are
author-written judgements, not generated conclusions. The severity matrix
considers impact and likelihood in a synthetic local setting, with confidence
reported separately. No Critical/High finding is invented to fill a quota.

The small standard-library generator was preferred to manually transcribing
results (which drifts) or introducing a reporting framework (unneeded dependency).
It reuses existing read-only freeze and metric helpers, never evaluates new
requests. The [tests](../../tests/test_audit.py) exercise tampered hashes/tables,
missing findings, inventory omissions and review-status regeneration.

An AI reviewer's check of all 65 labels is recorded in [label-review.md](label-review.md); it is not human review and does not change any label status.

Owner review status is deliberately excluded from frozen semantic digests.
An authorised status-only update followed by `make audit-report` changes the
derived wording without rewriting the report; review never implies independence.
This documentation change itself does not edit any label or status.

Figures are rendered from the accompanying `.mmd` sources using the already
installed Mermaid CLI and Chrome, then committed. Normal report builds consume
the PNGs directly. Use `mmdc -i docs/audit/figures/components.mmd -o
docs/audit/figures/components.png` (and the sequence equivalent) only when
intentionally revising figures; no automatic package or browser provisioning.

See [notices](../third-party-notices.md), [publication checklist](../PUBLISHING.md)
and the [evidence tables](tables.json). Existing recorded replay is not live
monitoring and must never be counted as extra independent samples.
