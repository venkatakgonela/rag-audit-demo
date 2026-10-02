# 0004: Start with PostgreSQL 16 and pgvector

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work. Accepted for the foundation; **to be validated against retrieval needs** during retrieval design.

## Context

[Compose](../../compose.yaml) runs `pgvector/pgvector:pg16`; [SQL](../../docker/init/001-enable-vector.sql) enables vector and the [integration test](../../tests/integration/test_database.py) checks its presence. No vector search or corpus schema exists.

## Decision drivers

Explore relational ownership/claims alongside vector evidence without operating two stores prematurely. The query-enforced ACL requirement is mandatory, not something the database choice has already proved.

## Options considered

| Option | Benefit for consideration | Cost / reason not selected now |
| --- | --- | --- |
| PostgreSQL plus pgvector | Relational data and vectors in one candidate store | Search/index tuning and ACL execution still need validation. |
| Qdrant | Dedicated vector retrieval interface | Adds a separate service/data-authorisation integration to evaluate. |
| Weaviate | Vector-oriented database platform | Broader platform decisions than needed for extension-connectivity proof. |
| Chroma | Embedding-oriented development workflow | Relational claims/ACL integration would need separate design. |
| OpenSearch | Candidate keyword/vector consolidation | Additional search infrastructure to evaluate; detailed current behaviour unverified here because official docs redirected repeatedly. |
| Managed vector service, e.g. Pinecone | Outsourced store operations | External account, network, data-boundary and cost considerations. |

These are architectural trade-offs, not claims that alternatives lack filtering, transactions, or other capabilities. None was benchmarked for this workload.

## Decision

Keep PostgreSQL 16/pgvector for the foundation and defer indexes, keyword implementation, reranker, and final access-control query design.

## Consequences

One local service is convenient, but not proof of retrieval suitability. pgvector documents filtering after approximate-index scanning: a SQL predicate alone does not prove physical pre-filtering or adequate filtered recall. Evaluate an authorised candidate-set/exact-search baseline, inspect query plans, and test adversarial access and recall before adopting any approximate path. Do not implement application-side post-filtering as an ACL substitute. The image's major tag is mutable; exact database/vector build reproducibility is not guaranteed by the Python lockfile.

## Revisit when

The retrieval experiment cannot meet authorisation, recall, latency, dataset-scale or operational requirements with a defensible query strategy.

## Sources

[PostgreSQL 16](https://www.postgresql.org/docs/16/intro-whatis.html), [pgvector filtering and image tags](https://github.com/pgvector/pgvector), [Qdrant](https://qdrant.tech/documentation/overview/), [Weaviate](https://docs.weaviate.io/weaviate), [Chroma](https://docs.trychroma.com/docs/overview/introduction), [Pinecone](https://docs.pinecone.io/guides/get-started/overview), [OpenSearch reference — unverified retrieval](https://docs.opensearch.org/latest/vector-search/). Consulted October 2, 2026.
