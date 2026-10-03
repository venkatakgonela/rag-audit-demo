# Developer reference

Historical configuration and command reference, retained from the audited revision. The current client overview and report are in the root README.

# rag-audit-demo

## Quickstart prerequisites and platforms

The README fake-answering path requires Git, Make, uv with Python3.12 and a running
Docker engine with Compose. It needs neither a provider key nor a model download.
macOS is locally tested; Linux and Windows quickstarts are not locally tested.
Hosted Linux CI is separate evidence, not a Windows or newcomer test.
Verify `docker compose version` and `docker info` before starting. If a fresh
user or temporary home cannot find Compose, configure the already installed
Compose plugin for that user; the Docker engine alone is not sufficient.
Initial locked-package/image setup may download; cached package operations can
use `UV_OFFLINE=1`. The repository requires access while private.

If port5433 is occupied, change both `POSTGRES_PORT` and the port inside
`DATABASE_URL` in the generated `.env` before `make up`. For parallel copies,
also give `COMPOSE_PROJECT_NAME` a distinct value so one copy does not operate
another's database. `make down` preserves the synthetic database volume.

## Recorded CI and optional embeddings

The frozen synthetic corpus, labels and versioned baselines preserve failed and
successful outcomes. Development data selects thresholds; test results do not.
Release checks replay recorded HTTP responses through the real adapter, enforce
hard constraints and compare quality without tolerances. This tests recorded
behaviour, not future model behaviour. Hosted reference/proof results are in the
[audit](audit/report.md); changing a baseline is an explicit logged local operation,
never a shortcut to make failures green.

Optional real embeddings require `make eval-runtime` and explicit one-time
`make eval-model ARGS="--provision"`. With cached weights, `make eval-model`
verifies them; `make eval-gate` and `make eval-selftest` use recorded responses
without a provider key. Real generation is separately opt-in, not needed for
the fake demonstration.

## Repository map

- `src/rag_audit/`: retrieval, rules, answering, traces and local API.
- `tests/`: unit, database integration and deliberate gate faults.
- `datasets/evaluation/`: immutable references, labels and exposure history.
- `docs/audit/`: sources, generated tables, evidence index, report and local assets.
- `docs/decisions/`: choices, alternatives and revisit triggers.
- `scripts/`: reproducible report and inventory checks.

A synthetic answering demonstration with PostgreSQL/pgvector retrieval, access-scoped Decimal rules, verified extractive citations, signed fixture identity and durable tracing. Offline fake generation is the default; live Responses generation is opt-in local only. [Evaluation](evaluation.md) includes explicit model abstention and a recorded-HTTP regression gate; the dev-selected real profile is `local-calibrated-v2`, cosine >=0.70. CI exercises the real adapter with recorded responses, not live generation; hosted validation of this revision is pending.

Regression commands: `make eval-runtime`, `make eval-model ARGS="--provision"` (first cache only), `make db-init`, `make eval-gate`, `make eval-selftest`. Configure an isolated `DATABASE_URL`; no provider key is needed. Read the [failure and re-baseline protocol](evaluation.md#failure-and-re-baseline-protocol) before explicit local `make eval-record` or `make eval-rebaseline`. Neither runs in CI.

> **All data is synthetic.** The generated corpus models a fictional insurer. Nothing here is real customer, policy or claims data. Database credentials and identifiers are synthetic, disposable and local-only.

## Status

Under active development. Nothing below is claimed as working until it ships with tests.

| Area | Status |
| --- | --- |
| Project skeleton, Docker Compose + pgvector, CI | foundation implemented; local checks verified; hosted CI verified (private repository run) |
| Synthetic corpus and ACL model | implemented, synthetic fixture identities only |
| Hybrid retrieval with pre-filter access control | implemented, exact CPU vectors + full-text RRF |
| Rules layer and extractive answer policy | implemented; fake default and opt-in local Responses generation |
| Evaluation harness and golden set | implemented; current derived review status in the audit report |
| CI regression gate | implemented; selected hosted outcomes recorded in the audit attestation |
| Cost and latency tracing | implemented; synthetic usage, unknown price is null |
| Sample AI audit report | builder self-assessment; source and reproduction in audit/ |

## Design

See [docs/ARCHITECTURE.md](ARCHITECTURE.md) for components and non-goals, and [AGENTS.md](../AGENTS.md) for the engineering rules every change must respect.

Start with the [documentation reading guide](README.md) for architecture, decisions, trade-offs, and security evidence.

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

### Opt-in local Responses provider

The real adapter is implemented for **opt-in local use only, not exercised in CI**. It sends strict structured output to an OpenAI-compatible Responses endpoint. Existing access, rule, quotation, abstention and trace-release policies do not change. See [integration decision](decisions/0020-opt-in-responses-provider.md).

Configure the following using neutral operator-selected values; no private endpoint/model or key is bundled:

```sh
export GENERATION_BACKEND=responses
export GENERATION_BASE_URL=https://your-endpoint.example/v1
export GENERATION_MODEL=your-requested-model
export GENERATION_REPORTED_MODEL=your-exact-reported-model
export GENERATION_KEY_ENV=YOUR_PROVIDER_KEY
export GENERATION_REASONING_EFFORT=medium
export GENERATION_PRICE_VERSION=your-versioned-price-table
export GENERATION_PRICE_SOURCE='Operator-supplied dated list estimate; not verified billing'
```

Set `YOUR_PROVIDER_KEY` securely in the process environment, never in a file, command-line argument, log or pasted terminal transcript. Set `GENERATION_INPUT_PRICE`, `GENERATION_CACHED_PRICE`, `GENERATION_WRITE_PRICE`, `GENERATION_OUTPUT_PRICE` to your verified nonnegative decimal **USD per million token** configuration. Missing pricing/key/model configuration fails closed. All displayed costs are operator-supplied list-price estimates, not verified billing. Cache reads/writes are disjoint input subsets; unknown or conflicting fields are rejected. The supported usage mapping requires cache-write counters, including explicit zero, and reasoning reported inside output totals.

With the existing model already cached and optional embedding dependencies installed:

```sh
uv run --frozen --extra embeddings python -m rag_audit.cli ingest
uv run --frozen --extra embeddings python -m rag_audit.cli ask --subject synthetic-customer-a --query 'public procedure'
make test-live-config
```

No model download occurs in these commands; missing model artifacts fail. `test-live-config` only checks configuration, makes no paid call, and skips without both explicit opt-in and the environment key. Private live-smoke harnesses and task-spend ledgers are deliberately not shipped. A configured CLI ask may incur charges; callers must enforce their own aggregate budget. The HTTP API selects real cached embeddings when the operator configures Responses; body fields cannot select providers or permissions.

Real defaults: `GENERATION_OUTPUT_TOKENS=2048`, `GENERATION_SECONDS=60`, `GENERATION_COST_CEILING=0.55` USD per call. Configured maxima are 4,096 and USD 0.65; no adaptive raising or retries. Input bound is actual serialized UTF-8 request bytes plus 1,024 tokens, with a 32 KiB request cap. This is a qualified assumption, not a verified tokenizer counter. Exceeding the reported-input bound or 272,000-token supported-price limit fails closed. Incomplete and rejected generations retain valid usage/cost; timeouts may still be billable and are not retried. Exact expected reported model mapping rejects substitutions. A deployment using different usage semantics needs separate validation.

The first small local smoke found substantial natural-question abstention and rejected exact instruction quotations. It is not proof of general injection resistance. Subsequent frozen evaluation and calibration are implemented, the reranker was not adopted, and the replay gate awaits hosted confirmation. No LLM judge is used for extractive evaluation data.

### Offline answering quickstart

With locked dependencies and the PostgreSQL image already cached, this sequence needs no downloads or API keys:

```sh
UV_OFFLINE=1 make setup
docker compose up -d --wait --pull never
UV_OFFLINE=1 make db-init
UV_OFFLINE=1 make generate-corpus
UV_OFFLINE=1 make ingest ARGS='--fake'
UV_OFFLINE=1 make ask ARGS='--fake --subject synthetic-customer-a --query "public procedure"'
UV_OFFLINE=1 make ask ARGS='--fake --subject synthetic-broker-a --query "broker reconciliation"'
UV_OFFLINE=1 make ask ARGS='--fake --subject synthetic-underwriter-a --query "underwriting inspection"'
UV_OFFLINE=1 make ask ARGS='--fake --subject synthetic-admin --query "status synthetic-claim-1"'
UV_OFFLINE=1 make ask ARGS='--fake --subject synthetic-customer-b --query "status synthetic-claim-1"'
UV_OFFLINE=1 make ask ARGS='--fake --subject synthetic-broker-b --query "payout synthetic-claim-1"'
UV_OFFLINE=1 make ask ARGS='--fake --subject synthetic-underwriter-b --query "eligibility synthetic-claim-1"'
UV_OFFLINE=1 make ask ARGS='--fake --query "payout synthetic-claim-0"'
UV_OFFLINE=1 make ask ARGS='--fake --query "status synthetic-claim-1"'
UV_OFFLINE=1 make ask ARGS='--fake --query "status synthetic-claim-999"'
UV_OFFLINE=1 make test-integration
```

The last two asks have byte-identical no-answer bodies. Customer A cannot answer `broker reconciliation` or `underwriting inspection`; broker A can answer only the former; underwriter A can answer both through tier/team grants. Integration tests demonstrate this and run the deliberately malicious fake provider against the injection fixture. Adversarial modes are test-only, not HTTP request options.

Corpus **v3 only**: 72 tracked synthetic documents, twelve structured policies and sixteen claims. `make generate-corpus` exports the static source from `datasets/corpus-v3` to ignored `data/corpus`; alternate seeds are unsupported. Re-run `db-init`, export and ingest over an older database; additive schema initialization preserves existing traces. Ingestion replaces the managed corpus atomically. Never use these tables for unrelated records. Source hashes and structured prose bindings must agree before ingestion. These commands require a repository checkout, not only an installed wheel.

The [evaluation data guide](evaluation-data.md) inventories all documents and their intended access, and describes 60 drafted cases (120 phrasings, 40 dev/20 test). Sources are original synthetic AI-assisted drafts, edited and mechanically checked; independent human review is pending. Test semantic labels/questions have a candidate freeze digest. Checks never refresh it automatically; after acceptance, changes require a changelog reason. Evaluation data is never ingested or supplied to generation. `make test` validates it offline without Docker or model downloads.

`answer_mode=extractive` is the default and only supported mode. The model mainly selects evidence, not general synthesis: each statement equals its exact quote, with no whitespace/Unicode normalization. The gate uses per-embedder provisional profiles, not calibrated confidence: fake cosine >= 0.15, cached local model >= 0.55, both plus a positive keyword match. Longer natural-language questions can abstain. See [answer policy](decisions/0018-extractive-answer-policy.md).

Rules recognise status, payout/payable, eligibility/eligible with one synthetic claim ID and optional matching policy ID. Default wording is code-owned; no provider calculation. Payout rule version `synthetic-rules-v2` includes the claim status and “calculation only”; the formula is unchanged and is not a settlement or eligibility decision. A rejected optional rule rephrase still falls back to an answered deterministic template. Explicit hidden/absent entity references never fall back to public neighbours. No-answer equality is not a constant-time guarantee or a promise to infer hidden intent from arbitrary free text.

Python entry point is async `rag_audit.answering.ask(store, subject, question, embedder, ...)`. CLI subjects are trusted local administration. By default the minimal HTTP API uses fake embeddings and fake generation; ingest with `--fake` first. The opt-in Responses configuration instead selects cached real embeddings. Copy the synthetic `STUB_SIGNING_KEY` from `.env.example` into an existing local `.env` if needed; there is no runtime default key. Start `make run`, issue a local token, then:

```sh
TOKEN=$(UV_OFFLINE=1 make --silent stub-token ARGS='--subject synthetic-customer-a')
curl -s http://127.0.0.1:8000/ask -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"question":"payout synthetic-claim-0"}'
```

The token contains only subject; roles/teams come from PostgreSQL. Extra body fields are rejected. This stub has no expiry/replay protection and is not production authentication. Missing/forged tokens return generic 401, invalid bodies 400/413 and infrastructure failures 503. Extractive verification rejection and absent/inaccessible evidence return the same HTTP 200 no-answer bytes; traces retain `verification_failed` separately and a bounded `verification_reason` (schema, citation, quotation, instruction_echo, duplicate). This subreason is trace-only and null on other paths. Future evaluation must count those reasons separately. Every response requires committed trace storage, otherwise a generic error replaces it.

Answer settings (environment names): `ANSWER_MODE=extractive`, `QUESTION_CHARACTERS=4000`, `HTTP_BODY_BYTES=16384`, `EVIDENCE_BYTES=12288`, `PROMPT_BYTES=32768`, `CONTEXT_CHUNKS=5`, `OUTPUT_UNITS=512`, `OUTPUT_BYTES=16384`, `MAX_STATEMENTS=5`, `STATEMENT_CHARACTERS=2048`, `PROVIDER_SECONDS=10`, `COST_CEILING=0.01`, and `STUB_SIGNING_KEY` (required for HTTP, at least 32 UTF-8 bytes). Evidence uses whole UTF-8 chunks: oversize chunks are skipped and ranking continues, never truncated. Fake usage is **synthetic UTF-8 bytes**, not vendor tokens. Unknown fake price stays null; real calls require configured prices and use the separate real limits described above. There are no default real prices, per-user rate limits or verified billing guarantees.

`instruction-echo-v1` blocks configured attack phrases/delimiters, including exact in-set quotations; benign discussions can be overblocked. Delimiters alone are not security. [Calibrated evaluation and three canonical baselines](evaluation-results.md) are complete; the evaluated reranker is not adopted. General injection resistance remains unproven. Replay regression configuration is implemented, hosted validation remains pending, and the release audit remains **Planned**. No judge or abstractive answering is implemented.

### Synthetic retrieval quickstart

```sh
make setup && make up && make db-init
make generate-corpus
make setup-embeddings
uv run --frozen --extra embeddings python -m rag_audit.cli ingest
uv run --frozen --extra embeddings python -m rag_audit.cli query --subject synthetic-customer-a --query "water damage evidence"
uv run --frozen --extra embeddings python -m rag_audit.cli query --subject synthetic-broker-a --query "water damage evidence"
uv run --frozen --extra embeddings python -m rag_audit.cli query --subject synthetic-underwriter-a --query "water damage evidence"
uv run --frozen --extra embeddings python -m rag_audit.cli query --subject synthetic-admin --query "water damage evidence"
make test-embeddings
```

These commands retrieve evidence, not generated answers. Model setup explicitly downloads the pinned publisher tokenizer/ONNX export; ordinary tests do not. Source documents and model cache live in ignored `data/`. Ingestion atomically replaces the managed synthetic corpus. Plain `make setup` may remove optional packages; use `uv run --frozen --extra embeddings python -m rag_audit.cli ingest` (or `query`) for real embeddings after setup. Fake `ingest`, `query` and `ask` never implicitly install embeddings.

Customers/brokers cannot join staff teams, claims must be restricted, and broker/customer assignments are explicit. Raw retrieval can return irrelevant neighbours; `ask` applies the calibrated real or untuned fake gate and citation policy. This is not production authentication or constant-time execution. See the [access decision](decisions/0014-query-access-control.md) and [measured runtime comparison](decisions/0016-local-embedding-runtime.md).

For mechanics-only testing, `uv run --frozen python -m rag_audit.cli ingest --fake` and the corresponding `query --fake` need no model runtime. Fake and real model identities cannot be mixed; re-ingest when switching.

Settings read `.env` from the working directory, with environment variables taking precedence. Never commit `.env` or real credentials. The following database/Compose settings complement the answering settings above:

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
src/rag_audit/       Retrieval, rules, answering, tracing, API and configuration
tests/              Unit tests and opt-in database integration tests
docker/init/        Shared vector extension initialisation SQL
docs/               Implemented/planned architecture, ADRs, and backlog
.github/workflows/   Foundation CI workflow
compose.yaml        Local-only PostgreSQL/pgvector service
Makefile            Setup, development, and verification commands
pyproject.toml      Package and tool configuration
uv.lock             Reproducible Python dependencies
```

See [CHANGELOG.md](../CHANGELOG.md) for changes and [docs/decisions/](decisions/README.md) for product architecture decisions.
