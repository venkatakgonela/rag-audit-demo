# Changelog

All notable user-visible changes are recorded here, following Keep a Changelog.

## [Unreleased]

### Added

- Corpus v2 with 50 synthetic documents, structured policies/claims and visible role differentiation; v1 is no longer supported.
- Access-scoped Decimal status, payout and eligibility rules; deterministic entity routing and code-owned wording.
- Offline fake generation, extractive citation verification, versioned provisional evidence profiles and identical absent/inaccessible no-answer envelopes.
- Durable trace-before-release, synthetic usage and nullable versioned Decimal accounting, bounded prompts/output and cooperative provider deadlines.
- Signed subject-only local stub, minimal `POST /ask`, Python `ask`, and offline `make ask`/`stub-token` commands. Real generation and calibrated evaluation remain planned.

- Deterministic labelled synthetic corpus, transactional ingestion, fixture access control and exact pre-filtered hybrid retrieval with source offsets and eligible-only raw ranking signals.
- Optional pinned CPU ONNX embeddings, explicit model setup and smoke commands; default tests remain model-download-free.
- Cross-platform runtime comparison and access/chunking/runtime decisions. Real-model CI evaluation remains planned.

- Python 3.12 package with locked dependencies and environment-based, secret-masked settings.
- FastAPI liveness endpoint at `/health`, reporting the package version without requiring a database.
- Loopback-only PostgreSQL 16/pgvector development service with persistent storage and shared extension initialisation.
- Sanitised database connectivity checks and explicit integration tests, separate from Docker-free unit tests.
- Make targets for setup, development, lint/format, type checking, tests, and cleanup.
- Foundation CI workflow for unit checks and PostgreSQL integration tests; hosted CI verified (private repository run) for commit `8e7a2a3` on October 2, 2026.
- Synthetic-only setup documentation, product decision records, and a small hardening backlog.
- Architecture reading guide, six status-labelled diagrams, retrospective decisions, technology/pattern catalogues, glossary, and threat-to-test mapping.
- Documentation regression checks for ADR indexing/structure, relative links, Mermaid fences, and runtime dependency coverage.
