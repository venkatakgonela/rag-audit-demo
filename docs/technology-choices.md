# Technology choices

## Audit publication tooling (implemented)

The report uses Python's standard library and existing read-only evaluation
helpers, installed pandoc, headless Chrome controlled by the existing Puppeteer
installation, and Poppler inspection. Committed Mermaid PNGs and OFL Noto Sans
fonts keep normal builds offline. This avoids manual result transcription and a
new reporting framework; external tools remain explicit prerequisites rather
than project dependencies. See [reproduction](audit/README.md),
[tests](../tests/test_audit.py) and [notices](third-party-notices.md).

CI increment: [actions/cache v4](https://github.com/actions/cache/blob/v4/README.md) avoids repeated public weight transfers, with revision/manifest keys and unconditional independent verification. All jobs use Ubuntu 24.04 OS labels (not immutable images). Alternatives, maintenance costs and revisit triggers: [ADR 0028](decisions/0028-runner-and-model-cache.md). HTTP replay uses existing httpx; manifest/digest/network guards use Python standard library. No runtime dependencies or versions changed.

**Implemented** unless marked otherwise. This catalogue covers direct runtime/dev/build requirements and project tools; [pyproject.toml](../pyproject.toml) and [uv.lock](../uv.lock) are version evidence and the complete transitive inventory. The assessments are project-specific, not benchmarks. Source links were consulted October 2, 2026. Each row's revisit condition states when to reconsider, not a promised change.

## Runtime dependencies

### httpx

Existing locked HTTP client promoted from development to runtime without a version change. Async bounded Responses requests use explicit timeouts, no redirects, no environment proxy inheritance and no retries. MockTransport exercises failures without network; standard-library worker threads were rejected because cancelling the await does not reliably stop underlying blocking I/O. See [adapter tests](../tests/test_responses.py). This is opt-in local integration, never a live CI dependency.

### Standard-library answering components

No new third-party dependency was added for answering. Decimal provides the chosen monetary arithmetic, HMAC-SHA256 signs the subject-only local stub, asyncio bounds cooperative fake generation, and dataclasses define the provider contract. These choices are covered by [rules](../tests/test_rules.py), [HTTP](../tests/test_answer_http.py) and [provider/accounting tests](../tests/test_answering.py). JSONB stores ingestion-validated facts and trace snapshots through existing psycopg; exact database keys link facts to authoritative document ACLs. Revisit with production identity, traffic or a real provider. See [rules decision](decisions/0017-rules-routing-identity.md) and [tracing decision](decisions/0019-generation-tracing-accounting.md). These are local tested design decisions, not newly researched external claims.

### onnxruntime

Optional CPU inference, pinned 1.30.0. Executes the immutable publisher ONNX export with CLS pooling and L2 normalisation; no remote Python model code. MIT licence; [upstream](https://github.com/microsoft/onnxruntime). [Measured alternatives](decisions/0016-local-embedding-runtime.md).

### tokenizers

Optional tokenizer, pinned 0.23.2. Uses the publisher tokenizer for budgets and Unicode source offsets. Apache-2.0; [upstream](https://github.com/huggingface/tokenizers). Revisit with the model.

### numpy

Optional arrays/normalisation, pinned 2.5.3. BSD-3-Clause plus bundled notices; [metadata](https://pypi.org/pypi/numpy/2.5.3/json). No optional runtime import on default unit-only paths.

### fastapi

Typed HTTP framework used by the [health app](../src/rag_audit/api/main.py). Chosen for a compact contract-oriented API; Flask offers a smaller WSGI core, Django a fuller app stack, and Litestar another typed ASGI option. Accepted trade-off: Pydantic/Starlette coupling; revisit for different product/deployment needs. [ADR 0003](decisions/0003-fastapi.md), [official features](https://fastapi.tiangolo.com/features/).

### uvicorn

ASGI server invoked by `make run`, rather than the application framework itself. Chosen to serve the current ASGI app; Hypercorn or other ASGI hosting are alternatives not benchmarked here. Accepted trade-off: server configuration remains local-development oriented; revisit for production serving requirements. [ADR 0003](decisions/0003-fastapi.md), [official documentation](https://www.uvicorn.org/).

### pydantic-settings

Typed environment/dotenv configuration with precedence and validation. Chosen over plain environment reads, dynaconf or environs to keep validation/masking consistent; accepted trade-off is dependency semantics and careful secret handling. Revisit for rotation/central secret storage. [ADR 0005](decisions/0005-settings-secrets.md), [official settings documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

### psycopg

PostgreSQL driver with the `binary` installation extra (`psycopg-binary` in the lockfile). Chosen for explicit small SQL operations over SQLAlchemy, asyncpg or psycopg2; accepted trade-off is synchronous per-operation connections and binary distribution dependence. Revisit for domain persistence, pooling or measured concurrency needs. [ADR 0006](decisions/0006-psycopg-no-orm.md), [official usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html).

## Supporting runtime components

| Component | What / why here | Alternatives and accepted trade-off | Revisit / ADR / source |
| --- | --- | --- | --- |
| Python 3.12 | Pinned interpreter minor for a repeatable baseline | Python 3.13 is not claimed incompatible; narrower tested platform accepted | Required compatibility/support changes; [0002](decisions/0002-python-uv-locking.md), [Python docs](https://docs.python.org/3.12/) |
| Pydantic / SecretStr | Validation and secret-wrapper component used through settings | Manual parsing/masking trades less dependency for more custom code; masking is not encryption | Expanded secret lifecycle; [0005](decisions/0005-settings-secrets.md), [types](https://docs.pydantic.dev/latest/api/types/) |
| Starlette | Transitive ASGI/TestClient integration beneath FastAPI | Switching framework changes this coupling; upstream compatibility work accepted | TestClient migration when safe; [0003](decisions/0003-fastapi.md), [official test-client source](https://github.com/Kludex/starlette/blob/main/docs/testclient.md) |

## Development and build dependencies

| Dependency | What / why here | Options and accepted trade-off | Revisit / ADR / official source |
| --- | --- | --- | --- |
| hatchling | Build backend for the installable src package | setuptools or another backend; small backend-specific configuration accepted | Packaging complexity changes; [0002](decisions/0002-python-uv-locking.md), [build config](https://hatch.pypa.io/latest/config/build/) |
| pytest | Test runner, fixtures, markers | unittest or another runner; external dependency accepted for expressive fixtures | Ecosystem/test constraints; [0010](decisions/0010-test-strategy.md), [markers](https://docs.pytest.org/en/stable/example/markers.html) |
| pytest-cov | Coverage reporting in unit runs | Direct coverage invocation/no report; measurement overhead accepted, no security proof | Reporting becomes misleading or slow; [0010](decisions/0010-test-strategy.md), [docs](https://pytest-cov.readthedocs.io/en/latest/) |
| ruff | Lint and formatting interface | Separate Black/Flake8/isort-style toolchain; chosen rule-set coupling accepted | Rules/format needs diverge; [0010](decisions/0010-test-strategy.md), [docs](https://docs.astral.sh/ruff/) |
| mypy | Basic static checking of source/tests | Pyright or no static checker; imperfect type coverage and stub maintenance accepted | Stronger contract coverage needed; [0010](decisions/0010-test-strategy.md), [docs](https://mypy.readthedocs.io/en/stable/getting_started.html) |
| httpx | Current TestClient HTTP dependency | Network-only tests or safe future client migration; upstream deprecation warning accepted temporarily | Compatible replacement validated; [0010](decisions/0010-test-strategy.md), [docs](https://www.python-httpx.org/), [backlog](BACKLOG.md) |
| PyYAML | Parse Compose/workflow in offline invariant tests | Hand-written YAML subset; dependency accepted to avoid fragile parsing | YAML usage changes; [0010](decisions/0010-test-strategy.md), [safe_load](https://pyyaml.org/wiki/PyYAMLDocumentation) |
| types-pyyaml | Type stubs for mypy's YAML imports | Ignored missing imports or custom annotations; extra dev artifact accepted | Upstream typing availability changes; [0010](decisions/0010-test-strategy.md), [typeshed stubs](https://github.com/python/typeshed/tree/main/stubs/PyYAML) |

## Tools, services and standards

| Tool / standard | What / why here | Options and accepted trade-off | Revisit / ADR / official source |
| --- | --- | --- | --- |
| uv | Lock, sync and run workflow | Poetry/pip-tools; tool-specific workflow accepted | Environment needs change; [0002](decisions/0002-python-uv-locking.md), [sync](https://docs.astral.sh/uv/concepts/projects/sync/) |
| Make | Common local/CI recipes | just, Task, nox, scripts; Make/shell availability required | Cross-platform complexity; [0007](decisions/0007-make-interface.md), [manual](https://www.gnu.org/software/make/manual/make.html) |
| PostgreSQL 16 | Relational candidate store for synthetic claims/evidence | Separate relational/vector stores; operational DB requirement accepted | Retrieval modelling proves mismatch; [0004](decisions/0004-postgresql-pgvector.md), [manual](https://www.postgresql.org/docs/16/intro-whatis.html) |
| pgvector/pgvector:pg16 | Database image with vector extension | Qdrant/Weaviate/Chroma/OpenSearch/managed services; mutable image tag and unvalidated ANN behaviour accepted only for foundation | Before retrieval adoption and image hardening; [0004](decisions/0004-postgresql-pgvector.md), [upstream](https://github.com/pgvector/pgvector) |
| Docker / Docker Compose | Local isolated database lifecycle | Testcontainers/local install; Docker runtime and volume lifecycle required | Deployment/isolation changes; [0008](decisions/0008-local-compose.md), [services](https://docs.docker.com/reference/compose-file/services/) |
| GitHub Actions | Hosted checks and database service job | Another CI or local-only checks; hosted environment dependence accepted | Availability/security policy changes; [0009](decisions/0009-ci-jobs.md), [services](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers) |
| actions/checkout and astral-sh/setup-uv | Checkout and Python/uv setup steps | Manual setup/other actions; major-tag mutability accepted pending hardening | SHA-pinning decision; [0009](decisions/0009-ci-jobs.md), [checkout](https://github.com/actions/checkout), [setup-uv](https://github.com/astral-sh/setup-uv) |
| ubuntu-latest | Current runner label | Pin a named image; migration uncertainty currently accepted, not a final policy | Before observed 19 October 2026 migration warning takes effect; [0009](decisions/0009-ci-jobs.md), [backlog](BACKLOG.md) |
| Mermaid | Text-source diagrams | draw.io/PlantUML/Structurizr; automatic layout and renderer variation accepted | Readability or shared-model need; [0012](decisions/0012-mermaid.md), [docs](https://mermaid.js.org/intro/) |
| Keep a Changelog | Reader-oriented Unreleased record | Raw commit history; manual curation accepted | Release process changes; [0001](decisions/0001-record-architecture-decisions.md), [standard](https://keepachangelog.com/en/1.1.0/) |
| ADRs | Context/options/decision/consequence records | Commit-only rationale or one growing overview; maintenance cost accepted | Decision discoverability worsens; [0001](decisions/0001-record-architecture-decisions.md), [original discussion](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) |

**Implemented evaluation tooling:** dev calibration, canonical baselines and one pinned `cross-encoder/ms-marco-MiniLM-L6-v2` trial use existing ONNX Runtime 1.30.0, tokenizers 0.23.2 and NumPy 2.5.3; no new package or judge. Experimental reranking uses two intra-op threads, one inter-op thread, CPU only, one pair per inference. It is not adopted; the real default is cosine-only 0.75. See [model notice](third-party-notices.md) and [evaluation method](decisions/0024-extractive-evaluation.md). Regression gating remains planned.
