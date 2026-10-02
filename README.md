# rag-audit-demo

A synthetic retrieval core for a planned audit-grade RAG service and evaluation harness. Today it provides a health API, deterministic corpus generation, PostgreSQL/pgvector ingestion, fixture-access-controlled hybrid retrieval and optional local CPU embeddings. Cited answers, deterministic business rules and regression gating remain planned.

> **All data is synthetic.** The generated corpus models a fictional insurer. Nothing here is real customer, policy or claims data. Database credentials and identifiers are synthetic, disposable and local-only.

## Status

Under active development. Nothing below is claimed as working until it ships with tests.

| Area | Status |
| --- | --- |
| Project skeleton, Docker Compose + pgvector, CI | foundation implemented; local checks verified; hosted CI verified (private repository run) |
| Synthetic corpus and ACL model | implemented, synthetic fixture identities only |
| Hybrid retrieval with pre-filter access control | implemented, exact CPU vectors + full-text RRF |
| Rules layer and answer policy (citations, refusal) | planned |
| Evaluation harness and golden set | planned |
| CI regression gate | planned |
| Cost and latency tracing | planned |
| Sample AI audit report | planned |

## Design

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for components and non-goals, and [AGENTS.md](AGENTS.md) for the engineering rules every change must respect.

Start with the [documentation reading guide](docs/README.md) for architecture, decisions, trade-offs, and security evidence.

## Quickstart

Prerequisites: Git, Make, uv (verified with 0.11.3), and Docker with the Compose v2 plugin for database commands. uv manages Python 3.12. Run these commands from the repository root after cloning:

```sh
make setup && make up && make test
make test-integration
make run
```

In another terminal, request `http://127.0.0.1:8000/health`. The response is `{"status":"ok","version":"0.1.0"}`. The version comes from installed package metadata. This endpoint is a liveness check, not a database readiness check, and works without database configuration.

`make setup` installs the committed lockfile and creates `.env` from `.env.example` only if absent; it never overwrites an existing `.env`. The database listens only on `127.0.0.1`, at port 5433 by default. `make up` waits for database readiness. Initialisation enables `vector` on a new database volume. `make down` stops the database but preserves its named volume. No API keys or hosted services are required.

For checks without Docker:

```sh
make setup && make lint && make typecheck && make test
```

## Configuration

### Synthetic retrieval quickstart

```sh
make setup && make up && make db-init
make generate-corpus
make setup-embeddings
make ingest
make query ARGS='--subject synthetic-customer-a --query "water damage evidence"'
make query ARGS='--subject synthetic-broker-a --query "water damage evidence"'
make query ARGS='--subject synthetic-underwriter-a --query "water damage evidence"'
make query ARGS='--subject synthetic-admin --query "water damage evidence"'
make test-embeddings
```

These commands retrieve evidence, not generated answers. Model setup explicitly downloads the pinned publisher tokenizer/ONNX export; ordinary tests do not. Source documents and model cache live in ignored `data/`. Ingestion atomically replaces the single managed synthetic corpus, including fixture identities; do not put unrelated data in the `demo_*` tables. Re-run `make db-init` for an existing foundation database without deleting its volume. Plain `make setup` may remove the optional environment; embedding commands explicitly request it again.

Customers/brokers cannot join staff teams, claims must be restricted, and broker/customer assignments are explicit. Scores, offsets and authorised returned chunk IDs support future answer-policy checks. Nearest neighbours may be irrelevant: semantic abstention is not implemented. This is not production authentication or constant-time execution. See the [access decision](docs/decisions/0014-query-access-control.md) and [measured runtime comparison](docs/decisions/0016-local-embedding-runtime.md).

For mechanics-only testing, `uv run --frozen python -m rag_audit.cli ingest --fake` and the corresponding `query --fake` need no model runtime. Fake and real model identities cannot be mixed; re-ingest when switching.

Settings read `.env` from the working directory, with environment variables taking precedence. Never commit `.env` or real credentials. The following is the complete application/Compose configuration surface:

| Variable | Default / example | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | unset in application; synthetic local URL in `.env.example` | Required only for database operations. Masked in settings representations. |
| `DATABASE_CONNECT_TIMEOUT` | `5` | Connection timeout in seconds, from 1 to 30. |
| `POSTGRES_USER` | `synthetic_demo` in example | Required Compose database user. |
| `POSTGRES_PASSWORD` | `synthetic_local_only` in example | Required disposable Compose password; not suitable for deployment. |
| `POSTGRES_DB` | `synthetic_demo` in example | Required Compose database name. |
| `POSTGRES_PORT` | `5433` | Published database port, always loopback-only. |
| `COMPOSE_PROJECT_NAME` | `rag-audit-demo` in example | Isolates Compose containers, networks, and named volumes. |

When changing a port or database credential, update `DATABASE_URL` as well. For an isolated verification database, set a unique `COMPOSE_PROJECT_NAME`, an unused `POSTGRES_PORT`, and a matching `DATABASE_URL`. Changing initialisation credentials does not modify an existing PostgreSQL volume; keep them consistent with the volume's original configuration. This is a local demo, not a deployment configuration.

`make db-init` executes `docker/init/001-enable-vector.sql` against `DATABASE_URL` and verifies the extension. It is idempotent and is also used for the CI service container. The integration test does not initialise the extension: it fails if configuration is missing, the connection fails, or vector is absent. Raw database errors and connection strings are not printed. Do not log raw settings input, structured validation error input, or explicitly unwrapped secret values.

## Development commands

| Command | Purpose |
| --- | --- |
| `make help` | List all targets. |
| `make setup` | Install locked dependencies and create local settings if absent. |
| `make up` / `make down` | Start and stop PostgreSQL, retaining its volume. |
| `make lint` / `make format` | Check lint and formatting / apply formatting. |
| `make typecheck` | Run basic mypy checks on source and tests. |
| `make test` | Unit tests and coverage, without Docker. |
| `make test-integration` | Explicit database test run. |
| `make db-init` | Initialise vector using the shared SQL file. |
| `make run` | Serve the API on `127.0.0.1:8000`. |
| `make clean` | Remove generated Python environments, caches, builds, and coverage artifacts; preserve `.env` and database volumes. |

Plain `uv run --frozen pytest` skips integration tests by default. The explicit integration target enables and selects them. Unit tests isolate settings from the developer's environment and `.env`.

The CI workflow runs lint, format checking, type checks, and unit tests in one Ubuntu job and real PostgreSQL/pgvector integration tests in another. All shell steps use Makefile targets. Foundation hosted CI is verified (private repository run) for commit `8e7a2a3`; both jobs passed on October 2, 2026. This does not certify subsequent revisions.

## Repository layout

```text
src/rag_audit/       API, settings, and database connectivity helpers
tests/              Unit tests and opt-in database integration tests
docker/init/        Shared vector extension initialisation SQL
docs/               Planned architecture, ADRs, and backlog
.github/workflows/   Foundation CI workflow
compose.yaml        Local-only PostgreSQL/pgvector service
Makefile            Setup, development, and verification commands
pyproject.toml      Package and tool configuration
uv.lock             Reproducible Python dependencies
```

See [CHANGELOG.md](CHANGELOG.md) for changes and [docs/decisions/](docs/decisions/README.md) for product architecture decisions.
