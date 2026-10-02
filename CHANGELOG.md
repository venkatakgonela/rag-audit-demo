# Changelog

All notable user-visible changes are recorded here, following Keep a Changelog.

## [Unreleased]

### Added

- Python 3.12 package with locked dependencies and environment-based, secret-masked settings.
- FastAPI liveness endpoint at `/health`, reporting the package version without requiring a database.
- Loopback-only PostgreSQL 16/pgvector development service with persistent storage and shared extension initialisation.
- Sanitised database connectivity checks and explicit integration tests, separate from Docker-free unit tests.
- Make targets for setup, development, lint/format, type checking, tests, and cleanup.
- Foundation CI workflow for unit checks and PostgreSQL integration tests; hosted CI verified (private repository run) for commit `8e7a2a3` on October 2, 2026.
- Synthetic-only setup documentation, product decision records, and a small hardening backlog.
- Architecture reading guide, six status-labelled diagrams, retrospective decisions, technology/pattern catalogues, glossary, and threat-to-test mapping.
- Documentation regression checks for ADR indexing/structure, relative links, Mermaid fences, and runtime dependency coverage.
