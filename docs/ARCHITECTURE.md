# Architecture: synthetic RAG audit demonstration

Implemented: health foundation, synthetic corpus generation, transactional ingestion, fixture access control and local hybrid retrieval. Planned: answering, business rules, citation enforcement, tracing, evaluation and release gating. All domain records are fictional and labelled synthetic.

## Key design ideas

1. Implemented: materialise eligible rows in SQL before exact vector and keyword ranking, never retrieve globally then discard forbidden hits.
2. Implemented: deterministic source slices with section paths and Unicode offsets; section paths enter embedding/full-text inputs without changing stored text.
3. Implemented: explicit CPU-only optional runtime, immutable model revision and no paid API in tests.
4. Planned: deterministic rules with an LLM phrasing shell, authorised citations and evidence-sensitive abstention.
5. Planned: real-model quality evaluation and a regression gate. Current local tests are security/mechanics checks, not broad retrieval-quality proof.

## System context

Caption: **System context** — current retrieval and planned answering.
Legend: solid links are Implemented; dashed links are Planned.

```mermaid
flowchart LR
    user["Synthetic fixture caller"] --> cli["Implemented retrieval CLI"]
    cli --> db[("PostgreSQL plus pgvector")]
    cli --> model["Local pinned ONNX model"]
    user -.-> answer["Planned answering service"]
    answer -.-> cli
```

## Containers

Caption: **Containers** — logical processes, not an application Docker image.
Legend: all nodes and links are Implemented; external generation is absent.

```mermaid
flowchart LR
    host["Host Python CLI and health API"] --> database[("Loopback Compose PostgreSQL")]
    host --> cache["Local model cache"]
    tests["Unit and opt-in integration tests"] --> database
    ci["Existing CI configuration"] --> tests
```

## Components

Caption: **Components** — implemented retrieval pipeline.
Legend: all shown components and links are Implemented.

```mermaid
flowchart LR
    corpus["Seeded corpus generator"] --> files["Markdown and ACL manifest"]
    files --> chunks["Section-aware exact source slices"]
    chunks --> embedding["Section path plus text embedding"]
    embedding --> ingest["Atomic single-corpus replacement"]
    ingest --> database[("Documents and chunks")]
    subject["Trusted fixture subject"] --> eligible["SQL eligible relation"]
    database --> eligible
    eligible --> ranking["Exact cosine plus full-text ranks"]
    ranking --> result["RRF and eligible-only raw signals"]
```

The [chunker](../src/rag_audit/chunking.py) targets 384 tokens, ceiling 480, overlap 48 only inside long sections, reserving space for section path and special tokens. The [adapter](../src/rag_audit/embeddings.py) uses the pinned ONNX export, CLS pooling and normalisation. The [retrieval statement](../src/rag_audit/retrieval.py) applies tier OR team OR owner/assigned-broker grants before both ranks. Claims must be restricted; customer/broker identities cannot join staff teams. [Decision 0014](decisions/0014-query-access-control.md) defines the trust boundary.

## Planned answering flow

Caption: **Question-answering sequence** — answering is Planned; retrieval exists independently.
Legend: all messages are Planned integration, not implemented answer-policy behaviour.

```mermaid
sequenceDiagram
    actor Caller
    participant Policy as Planned answer policy
    participant Retrieval as Implemented retrieval
    participant Rules as Planned deterministic rules
    participant Model as Planned generation adapter
    Caller->>Policy: Question
    Policy->>Retrieval: Trusted subject and query
    Retrieval-->>Policy: Authorised slices and raw signals
    alt Inadequate evidence
        Policy-->>Caller: I do not know
    else Sufficient evidence
        Policy->>Rules: Compute fixed outcomes
        Rules-->>Policy: Results
        Policy->>Model: Evidence and fixed results
        Model-->>Policy: Draft with citations
        Policy->>Policy: Validate citations and fixed outcomes
        Policy-->>Caller: Checked answer or safe fallback
    end
```

Nearest neighbours can be irrelevant. Retrieval does not implement semantic “no match”, refusal wording or citation enforcement. Inaccessible content must not influence returned results/scores, but constant-time execution is not promised.

## Implemented data model

Caption: **Data model** — actual shared-init schema.
Legend: entities and relationships are Implemented; teams are validated arrays, not a separate table.

```mermaid
erDiagram
    DEMO_USERS ||--o{ DEMO_DOCUMENTS : owns_claim
    DEMO_USERS ||--o{ DEMO_BROKERS : assigns
    DEMO_DOCUMENTS ||--o{ DEMO_CHUNKS : contains
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
    end
```

## Quality, evidence and limits

- [Unit tests](../tests/test_retrieval_core.py) check deterministic generation/chunks, metadata restrictions and source offsets.
- [Integration tests](../tests/integration/test_retrieval.py) check role sets, forbidden-content noninterference, raw signals, idempotence and ANN underfill versus exact search.
- [Explicit real-model smoke](../tests/test_embedding_adapter.py) checks shape, normalisation, query instruction and Unicode offsets. Default CI does not execute it; a cache-backed real-model evaluation remains required.
- Exact search is linear in eligible rows; candidate bounds limit ranking output, not database work. No production identity provider, constant-time defence, semantic abstention or quality gate exists.
- Operator/database access is trusted. Corpus and model cache are ignored local state; initial model download trusts HTTPS/publisher, and local hash metadata is not signed.
- Keep [technology choices](technology-choices.md), [patterns](patterns.md), [threat model](threat-model.md), [decisions](decisions/README.md) and [backlog](BACKLOG.md) aligned with actual evidence.
