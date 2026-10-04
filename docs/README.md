# Documentation reading guide

All domain data is synthetic. **Implemented** means present in the repository; **Planned** means a design intention, not a working feature. **Rejected** describes an option not selected for this scope, not an inferior product.

1. [Architecture](ARCHITECTURE.md) — clients and engineers: who does what, implemented request flow, design ideas, and deployment.
2. [Decision index](decisions/README.md) — anyone asking “why this rather than that?”; alternatives and unresolved decisions.
3. [Technology choices](technology-choices.md) and [patterns](patterns.md) — implementers and technical interviews: trade-offs, locations, and tests.
4. [Threat model](threat-model.md) — reviewers: trust boundaries, tested protections, known gaps, and planned mitigations.
5. [Glossary](glossary.md) — readers new to the terminology. [Why it matters](governance.md) — risk examples and framework mapping for governance, risk and compliance readers.
6. [Evaluation method](evaluation.md) and [canonical results](evaluation-results.md) — a worked example, definitions, limitations, counts/intervals and the historical and second live references.
7. [Sample audit](audit/README.md) — client-facing report, reproducible tables, findings and limitations.
8. [Developer reference](development.md), [contributing](../CONTRIBUTING.md), [third-party notices](third-party-notices.md), [publication provenance](PUBLISHING.md) and [release notes](release-notes-0.1.0.md).
9. [Release gate lifecycle](release-gate.md) — maintainers and reviewers: what blocks a change, what a pass means, and when human review is needed.
10. [Diagram sources and rendering](images/README.md) — editable presentation figures and offline reproduction instructions.

Use the [project README](../README.md) for runnable commands, the [changelog](../CHANGELOG.md) for changes, and the [backlog](BACKLOG.md) for deferred work.

## Evidence convention

Repository links identify implemented code, configuration, and tests. External links identify official behaviour references consulted on October 2, 2026; project trade-offs are assessments, not comparative benchmarks. The [audit verification record](audit/verification-evidence.json) and [hosted evidence summary](audit/report.md#10-regression-plan-and-existing-hosted-evidence) identify historical passing and deliberately failing runs by revision. Those observations do not certify subsequent revisions; implementation, a recorded test result and production assurance are different claims.

## Documentation checks

Community issue and pull-request templates are included in the local Markdown
link checks alongside the root and documentation files.

The [documentation tests](../tests/test_docs.py) run in `make test` without Docker. They cover root/docs Markdown inline links and explicit/collapsed reference links, local heading fragments, ADR index/sections, Mermaid fences/captions, and direct runtime catalogue entries. Literal code examples and external URLs are not link-checked. This small checker is not a complete CommonMark/HTML parser: use the supported link forms, not raw HTML links, shortcut references, or nested-parenthesis destinations. Mermaid syntax/rendering and factual accuracy require separate review; no external network is used by the tests.
