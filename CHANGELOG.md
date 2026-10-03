# Changelog

All notable user-visible changes are recorded here, following Keep a Changelog.

## [Unreleased]

### Added

- Tracked corpus v3: 72 original AI-assisted synthetic documents, structured source bindings, explicit access intent and 60 drafted golden cases with candidate split/freeze digests. Independent human label review pending.
- Offline schema/fact/profile-reference checks and independent rule oracles; SQL comparison covers every document and fixture subject. Evaluation harness and calibration are not implemented.

### Changed

- Candidate labels revised before acceptance to add six free-text hidden-answer traps, six in-domain near misses and four ordinary injection questions; still 60 cases, 40 dev/20 test, with unchanged corpus and subject allocation. Candidate semantic digests regenerated for the new coverage and explicit acceptable-decision/forbidden-fact labels; all labels remain drafted.
- Extractive verification traces now include a bounded `verification_reason` (`schema`, `citation`, `quotation`, `instruction_echo`, `duplicate`); this field never enters the public response and does not change verification criteria.
- Extractive verification rejection returns the standard HTTP 200 no-answer, with a distinct trace reason; infrastructure errors and deterministic rule rephrase fallback retain their prior handling.
- Payout rule v2 includes claim status and a calculation-only qualification without changing the amount or adding an eligibility decision.
- Static corpus export replaces seeded generation; v2 corpus ingestion is no longer supported. Initial v3 candidate labels have not been accepted or human-reviewed.

### Previously added

- Opt-in local OpenAI-compatible Responses adapter with strict schemas, environment-only key, exact model mapping, bounded async HTTP and no retries; real service is never exercised by CI.
- Real-token pricing with disjoint cache-read/write subsets, output reasoning accounting, qualified pre-dispatch byte bound and explicit unknown-price/input-tier rejection. Costs remain operator-supplied list estimates, not verified billing.
- Offline mocked transport/network-trap checks and an explicitly gated, no-spend live-configuration check. Access, rule, citation and abstention policies are unchanged.

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
