# Changelog

All notable user-visible changes are recorded here, following Keep a Changelog.

## [Unreleased]

- Explain request ownership, evaluation uncertainty and release checks in plain
  English; add editable risk/control/evidence and release-gate diagrams, and
  reconcile documentation status with the retained implementation evidence.

- Allow reviewed action SHA updates while checking immutable pins, version
  comments and unchanged action placement in CI; retain workflow security checks.
- Update the development type checker to mypy 2.3.1 without loosening typing
  settings; refresh the locked dependency inventory and retained notices.

## [0.1.0] - 2026-10-04

First public release. Entries describe the implementation as audited, including
their original limits.

#### Changed

- Pin workflow actions and configure bounded weekly action/uv dependency updates.
- Add contribution and issue guidance; shorten the quickstart and retain public
  provenance while separating owner-only release instructions.
- Compose temporary evaluation schema identifiers safely and retain constant,
  parameter-bound retrieval queries without changing evaluation or access policy.

#### Added

- Record of an AI reviewer's check of all 65 labels (`docs/audit/label-review.md`): no disagreement found, three wording notes; labels stay `drafted` and no human review is claimed.

#### Fixed

- Audit category tables now distinguish correct answers from permitted refusals
  and injection outcomes; hosted results label deliberate proof runs explicitly.
- Fake-mode quickstart demonstrates an answer, a refusal and a calculated payout.

- Added a reproducible synthetic builder self-assessment, source-derived findings
  and tables, client README, MIT licence, third-party inventory and security policy.
- Added offline report checks and publication preparation; no product behaviour,
  labels, corpus, fixtures, baselines or workflows changed for the report.
- Existing remediation/main hosted runs passed; see the committed audit
  attestation for exact revisions and run outcomes, not a claim about later code.

### Added

- `ci-abstention-v2`: explicit model abstention with strict local outcome validation, unchanged no-answer bytes, separate reason metrics and context-bound replay. Rejected-only paced evaluation retries retain unknown holds; production requests do not retry.

- Read-only real-embedding HTTP replay regression checks, fault-injection self-tests, trusted model verification and explicitly guarded local recording/rebaseline commands. All CI jobs pin Ubuntu 24.04; hosted validation remains pending.

- `ci-baseline-v1`: initial replay regression baseline from frozen recorded behaviour, with zero measured-drift tolerances provisional until the first hosted CPU run. Historical baseline exposures are unchanged.
- `ci-config-settings-v1`: gate configuration now fingerprints all non-secret behavioural settings; initial development baseline regenerated with an explicit log reason, without changing historical evaluation exposures.
- Three versioned canonical evaluation summaries and a durable test-dispatch log: fake, cached-real deterministic and informational live, each held-out configuration evaluated once. Live completed within the USD 3 estimate cap. Results retain low coverage and wrong/false answers; zero hard failures is not a quality guarantee.
- Dev-only evaluation and fixed calibration now exercise the actual pipeline. An opt-in, hash-checked CPU cross-encoder trial compares 44 replacement-gate configurations without changing the runtime default, reading test labels or calling a paid provider.
- Evaluation data revision 3 accepts the prior candidate and adds five drafted cases before test evaluation: three same-chunk factual injection questions, one hidden free-text trap and one near miss. Three unique descriptive sentences augment existing attack sections without changing original labelled facts, attack strings or structured claims. Corpus/profile/forbidden-reference digests are refreshed; dev/test labels now have separate files. Human review remains pending.
- Tracked corpus v3: 72 original AI-assisted synthetic documents, structured source bindings, explicit access intent and 60 drafted golden cases with candidate split/freeze digests. Independent human label review pending.
- Offline schema/fact/profile-reference checks and independent rule oracles; SQL comparison covers every document and fixture subject. Canonical test baselines and release gating remain pending.

### Changed

- Adopted `local-calibrated-v2`: complete dev-only comparison selects V1 cosine >=0.70 with explicit abstention (9/18 natural correct versus historical 5/18; zero dev false answers). Lower candidates are rejected for hidden-intent free-text false answers. Final and hosted verification are separate evidence, not implied by selection.

- Adopted `local-calibrated-v1`: pinned real embeddings use cosine >=0.75 without the lexical conjunction; fake profile, retrieval ACLs, rules and verification remain unchanged. Added isolated held-out exposure logging, explicit partial coverage, forecast matching and private live recording safeguards. CPU reranker remains not adopted.
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
