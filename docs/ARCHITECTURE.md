# Architecture: synthetic RAG audit demonstration

The [evaluation harness](evaluation.md), three [canonical baselines](evaluation-results.md) and `local-calibrated-v1` default (V1 cosine >=0.75) are Implemented. Fake stays untuned. Reranker not adopted. [ADR 0025](decisions/0025-calibrated-local-gate.md) records the profile adoption. CI gates/replay remain Planned.

Dev calibration and an experimental pairwise CPU reranker are Implemented. The reranker sees only the existing top-20 authorised candidates; it does not expand retrieval or change rules/verification. The [trial](reranker-dev.md) did not meet adoption criteria ([ADR 0023](decisions/0023-cpu-reranker-trial.md)); it is not deployed by default.

Implemented: health, corpus v3, transactional ingestion, scoped retrieval/rules, extractive answering, signed fixture identity, durable tracing and calibrated evaluation. Labels remain outside ingestion/generation boundaries. Generation defaults to fake; Responses is opt-in local only, never exercised by CI. Release gating remains Planned. All domain records are synthetic.

Implemented data flow: `datasets/corpus-v3` → source/hash/structured-binding validation → unchanged chunker and ingestion. `datasets/evaluation` → offline label checks and independent SQL visibility comparison, never provider prompts. See [evaluation data](evaluation-data.md) and [ADR 0021](decisions/0021-versioned-evaluation-data.md). No database tables changed. Rule version v2 qualifies payout by status without changing arithmetic. Extractive verification rejection now presents as no-answer while its trace remains distinct; invalid rule rephrasing retains template fallback ([ADR 0022](decisions/0022-answer-outcome-presentation.md)).

## Key design ideas

1. Implemented: materialise eligible rows in SQL before exact vector and keyword ranking, never retrieve globally then discard forbidden hits.
2. Implemented: deterministic source slices with section paths and Unicode offsets; section paths enter embedding/full-text inputs without changing stored text.
3. Implemented: explicit CPU-only optional runtime, immutable model revision and no paid API in tests.
4. Implemented: code-owned rules, authorised extractive citations and a dev-calibrated real evidence gate; fake remains untuned.
5. Implemented: small synthetic real-model evaluation; regression gate Planned. Results are not broad retrieval-quality proof.

## System context

Caption: **System context** — offline default and opt-in local real provider.
Legend: solid links are Implemented; dashed links are Planned.

```mermaid
flowchart LR
    user["Synthetic fixture caller"] --> cli["Implemented retrieval CLI"]
    cli --> db[("PostgreSQL plus pgvector")]
    cli --> model["Local pinned ONNX model"]
    user --> answer["Signed-subject offline answering API"]
    answer --> cli
    answer --> real["Opt-in local Responses endpoint; not in CI"]
```

## Containers

Caption: **Containers** — logical processes, not an application Docker image.
Legend: all nodes and links are Implemented; real generation is opt-in and not in CI.

```mermaid
flowchart LR
    host["Host Python CLI, health and answering API"] --> database[("Loopback Compose PostgreSQL")]
    host --> cache["Local model cache"]
    host --> provider["Optional Responses endpoint"]
    tests["Unit and opt-in integration tests"] --> database
    ci["Existing CI configuration"] --> tests
```

## Components

Caption: **Components** — implemented retrieval pipeline.
Legend: all shown components and links are Implemented.

```mermaid
flowchart LR
    corpus["Tracked corpus v3"] --> files["Validated Markdown and ACL manifest"]
    labels["Drafted golden data and access intent"] --> checks["Offline facts and freeze checks"]
    files --> chunks["Section-aware exact source slices"]
    chunks --> embedding["Section path plus text embedding"]
    embedding --> ingest["Atomic single-corpus replacement"]
    ingest --> database[("Documents and chunks")]
    subject["Trusted fixture subject"] --> eligible["SQL eligible relation"]
    database --> eligible
    eligible --> ranking["Exact cosine plus full-text ranks"]
    ranking --> result["RRF and eligible-only raw signals"]
    eligible --> rules["Authorised structured Decimal rules"]
    result --> gate["Calibrated real cosine 0.75; fake demo gate; byte budgets"]
    labels --> evaluator["Isolated evaluator; dev calibration; logged test runs"]
    evaluator --> subject
    trace --> metrics["Independent facts, rules and counterfactual metrics"]
    gate --> fake["Offline fake evidence selector"]
    fake --> verify["Exact citation and echo verification"]
    gate --> real["Opt-in Responses: price and byte-bound preflight"]
    real --> verify
    rules --> template["Code-owned wording"]
    verify --> trace["Commit trace before release"]
    template --> trace
```

The [chunker](../src/rag_audit/chunking.py) targets 384 tokens, ceiling 480, overlap 48 only inside long sections, reserving space for section path and special tokens. The [adapter](../src/rag_audit/embeddings.py) uses the pinned ONNX export, CLS pooling and normalisation. The [retrieval statement](../src/rag_audit/retrieval.py) applies tier OR team OR owner/assigned-broker grants before both ranks. Claims must be restricted; customer/broker identities cannot join staff teams. [Decision 0014](decisions/0014-query-access-control.md) defines the trust boundary.

## Implemented answering flow

Caption: **Question-answering sequence** — offline answer decisions and durable traces.
Legend: messages are Implemented; real provider is opt-in local only; CI quality gates remain Planned.

```mermaid
sequenceDiagram
    actor Caller
    participant Policy as Answer policy
    participant Store as PostgreSQL snapshot and traces
    participant Rules as Decimal rules
    participant Model as Fake or opt-in Responses
    Caller->>Policy: Signed subject and bounded question
    Policy->>Store: Resolve identity and entity ACLs under locks
    Store-->>Policy: Authorised evidence or records, release locks
    alt Rule request
        Policy->>Rules: Compute authorised inputs
        Rules-->>Policy: Fixed result and template
    else Sufficient evidence
        Policy->>Model: Price preflight and bounded untrusted evidence
    Model-->>Policy: Structured extractive statements
        Policy->>Policy: Verify whole output
    else Missing or weak evidence
        Policy->>Policy: Fixed no-answer envelope
    end
    Policy->>Store: Commit one trace
    Store-->>Policy: Success or storage failure
    Policy-->>Caller: Verified response or generic storage error
```

Nearest neighbours can be irrelevant. Raw retrieval is unchanged; answering applies the calibrated real or untuned fake gate and extractive policy. Hidden/absent explicit entities return identical no-answer; arbitrary free text has inaccessible-row noninterference, not hidden-intent detection. Constant-time execution is not promised.

## Implemented data model

Caption: **Data model** — actual shared-init schema.
Legend: entities and relationships are Implemented; teams are validated arrays, not a separate table.

```mermaid
erDiagram
    DEMO_USERS ||--o{ DEMO_DOCUMENTS : owns_claim
    DEMO_USERS ||--o{ DEMO_BROKERS : assigns
    DEMO_DOCUMENTS ||--o{ DEMO_CHUNKS : contains
    DEMO_DOCUMENTS ||--o| DEMO_POLICIES : authorises
    DEMO_DOCUMENTS ||--o| DEMO_CLAIMS : authorises
    DEMO_POLICIES ||--o{ DEMO_CLAIMS : applies
    DEMO_POLICIES {
        string id PK
        string document_id FK
        jsonb record
    }
    DEMO_CLAIMS {
        string id PK
        string document_id FK
        string policy_id FK
        jsonb record
    }
    DEMO_TRACES {
        string request_id PK
        timestamp created_at
        jsonb payload
    }
    DEMO_USERS {
        string subject PK
        string role
        string_array teams
    }
    DEMO_BROKERS {
        string broker FK
        string customer FK
    }
    DEMO_DOCUMENTS {
        string id PK
        string source
        string kind
        string tier
        string team
        string owner FK
    }
    DEMO_CHUNKS {
        string id PK
        string document_id FK
        string text
        string section
        int ordinal
        int start_offset
        int end_offset
        string tier
        string team
        string owner FK
        vector embedding
        tsvector search
        string corpus_version
        string model_identity
    }
    DEMO_CONFIGURATION {
        boolean singleton PK
        string model_identity
        string corpus_version
    }
```

[Ingestion](../src/rag_audit/ingestion.py) validates the complete manifest and computes vectors before atomically replacing the single managed corpus. Shared/exclusive advisory locks prevent mixed identity/corpus snapshots. Changed input removes stale rows; repeated input preserves IDs/counts. This is not a multi-corpus migration system. Run the same [initial SQL](../docker/init/001-enable-vector.sql) through Compose or `make db-init`.

## Deployment

Caption: **Deployment** — local and CI configuration.
Legend: nodes and links are Implemented configuration; hosted execution is verified only for the historical foundation, not this increment.

```mermaid
flowchart TB
    subgraph Local
        make["Make on host"] --> cli["CLI and health API"]
        cli --> db[("Loopback database")]
        cli --> onnx["Optional CPU model cache"]
    end
    subgraph CI
        unit["Default checks without model"] --> checks["Lint, types, unit/docs tests"]
        integration["Fake-vector integration tests"] --> service[("Own pgvector service")]
        evaluation["Ubuntu 24.04 evaluation"] --> integrity["Verify model and replay manifests"]
        integrity --> replay["Real embeddings and HTTP replay"]
        replay --> evaldb[("Own evaluation pgvector service")]
        replay --> gate["Read-only gate and faulty-variant self-tests"]
    end
```

## Quality, evidence and limits

- [Unit tests](../tests/test_retrieval_core.py) check deterministic generation/chunks, metadata restrictions and source offsets.
- [Integration tests](../tests/integration/test_retrieval.py) check role sets, forbidden-content noninterference, raw signals, idempotence and ANN underfill versus exact search.
- [Explicit real-model smoke](../tests/test_embedding_adapter.py) checks shape, normalisation, query instruction and Unicode offsets. The separate evaluation job exercises real embeddings and [replay self-tests](../tests/integration/test_gate_selftest.py); hosted verification is pending.
- Exact search is linear in eligible rows; candidate bounds limit ranking output, not database work. No production identity provider or constant-time defence exists. Calibrated local and provisional CI gates do not establish production utility.
- [Answering tests](../tests/test_answering.py) and [database tests](../tests/integration/test_answer_database.py) cover trace failure, rules, role differentiation, absence equality and snapshot provenance. Table locks end before generation; trace commit is independent and requires an idle connection. Traces survive ingestion and contain no rejected provider payloads.
- Operator/database access is trusted. Corpus/model cache are ignored local state; CI checks model bytes against a publisher-derived committed manifest. HTTPS/publisher and repository review remain trust roots; metadata is not signed.
- Keep [technology choices](technology-choices.md), [patterns](patterns.md), [threat model](threat-model.md), [decisions](decisions/README.md) and [backlog](BACKLOG.md) aligned with actual evidence.
