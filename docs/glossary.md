# Glossary

- **Eligible set:** rows authorised inside SQL before either ranking branch.
- **RRF:** reciprocal rank fusion; sums `1/(60+rank)` across available lists here.
- **Source offsets:** zero-based half-open Unicode positions reproducing chunk text.
- **CLS pooling:** selecting the first output token before L2 normalisation.
- **Snapshot ingestion:** atomic replacement of this demo's corpus and identities.

Definitions describe the design vocabulary; they do not imply implementation. Follow [architecture](ARCHITECTURE.md) for status and [technology choices](technology-choices.md) for official references.

| Term | Meaning here |
| --- | --- |
| ACL | Access-control list: candidate representation of which roles/owners may access a record; planned schema. |
| ADR | Architecture decision record: context, drivers, alternatives, choice, consequences and revisit trigger. |
| ANN | Approximate nearest-neighbour search; may trade retrieval completeness for performance. No ANN index exists here. |
| ASGI / WSGI | Python server/application interface families; this app uses an ASGI stack. |
| BM25 | Keyword relevance-ranking approach contemplated for hybrid retrieval; implementation undecided. |
| Chunk | Proposed bounded document segment with identity/section and access scope. |
| Citation validity | Proposed check that cited chunks were authorised and retrieved, and quotations match; not a full truth test. |
| Deterministic core | Planned code that computes business outcomes reproducibly rather than asking a model to decide. |
| Embedding | Numeric representation used for similarity search; model/dimensions undecided. |
| Fail closed | Reject a protected operation when required conditions are absent; currently applied to DB configuration, not general auth. |
| Faithfulness | Whether an answer is supported by evidence; planned evaluation distinct from citation syntax. |
| Golden set | Planned labelled cases with expected outcomes for regression evaluation. |
| Hybrid retrieval | Proposed combination of keyword and vector signals. |
| Liveness / readiness | Process responding versus being able to serve required dependencies/work; health is liveness only. |
| Lockfile | Committed dependency resolutions/hashes; not a lock on all operating-system or container bits. |
| ORM | Object-relational mapper; not currently used. |
| Ports and adapters | Planned boundary separating provider contracts from concrete generation/embedding implementations. |
| Pre-filter ACL | Authorisation restricts retrieval candidates inside the query; physical ANN execution still needs validation. |
| Prompt injection | Untrusted instructions influencing model behaviour, including instructions embedded in retrieved documents. |
| RAG | Retrieval-augmented generation: fetch evidence before generation; planned, not implemented by the health skeleton. |
| Reranker | Optional planned second-stage ranking of candidates; not selected. |
| SecretStr | Masking wrapper for ordinary representations; not encryption or permission enforcement. |
| Synthetic data | Fabricated, labelled demonstration material, not real customer records; realism is a limitation. |
| Mutation evidence | Temporarily break an invariant and show a test fails, then restore; not exhaustive correctness proof. |
| Trust boundary | Transition between components/actors with different assumptions about data or authority. |
| Release gate | A check that prevents promotion on failure; current CI checks the foundation, planned gates evaluate RAG safety/quality. |
| Judge calibration | Planned comparison of model judging with human labels to quantify error rather than assume reliability. |
| p50 / p95 | Median and 95th-percentile measurements, planned for latency reporting; no numbers measured for RAG yet. |
