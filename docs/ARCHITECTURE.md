# Design: audit-grade RAG with an evaluation harness

A retrieval-augmented question-answering service built so that its behaviour can be **audited and regression-tested**: who can see what, why an answer was given or refused, and whether a change made things worse.

> All data in this repository is synthetic. It models a fictional insurer.

## Domain

A fictional insurer's knowledge base: policy wordings, claims-handling guides, FAQs and per-customer claim records. Roles: `customer` (own claim data and public documents), `broker` (broker-tier documents and their clients' claims), `underwriter` (underwriting guidelines and internal documents), `admin`.

## Components

1. **Ingestion**: section-aware chunking; each chunk stores document id, section and an access-control list.
2. **Retrieval**: hybrid BM25 + vector search. The ACL filter is applied in the SQL query before ranking.
3. **Rules layer**: claim status, excess and limit calculations, eligibility checks. Pure code, unit-tested. The LLM only phrases results.
4. **Answer policy**: citations to chunk ids; every cited chunk must have been retrieved for that caller and quoted text must appear in the source. Weak or missing evidence gives "I don't know"; unauthorised requests are refused without confirming the document exists.
5. **Provider interface**: `generate()` and `embed()` behind an interface, with a deterministic fake provider for tests.
6. **Tracing**: per-query tokens, cost estimate, latency, retrieved chunk ids and decision.
7. **Evaluation harness**: ~60 hand-labelled cases (answerable, multi-document, unanswerable, unauthorised, rules, prompt injection in documents) with retrieval recall, citation validity, faithfulness, refusal precision/recall, leak rate, latency and cost.
8. **CI gate**: hard failures on any access leak, invalid citation or model-computed rule output; soft thresholds against a committed baseline.
9. **Audit report**: a sample report applying a reusable checklist to this system (`docs/audit/`).

## Non-goals

Multi-agent orchestration, fine-tuning, voice, production identity-provider integration (roles use stubbed tokens), UI polish beyond a minimal chat page/CLI, non-English support.
