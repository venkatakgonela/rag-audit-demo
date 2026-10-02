# 0015: Section chunks and reciprocal-rank fusion

Status: Accepted

## Context

Retrieval needs exact source references and both lexical and semantic signals.

## Decision drivers

Deterministic slices, traceable offsets, simple same-database ranking and no hidden relevance threshold.

## Options considered

Fixed character windows ignore model budgets. Semantic splitting introduces model-dependent boundaries. Heading/clause splitting with bounded token windows retains structure. Raw score addition depends on incompatible scales; rank fusion avoids that coupling. A separate keyword engine would add a service.

## Decision

Use section-aware contiguous source slices, target 384 tokens, ceiling 480, overlap 48 only within long sections; reduce the budget for section-path tokens and special tokens. Offsets are half-open Unicode character positions. Prefix section path only in embedding/full-text inputs, never in stored chunk text. Short sections remain short. Current long-section windows split at token boundaries, not sentence boundaries.

Use English PostgreSQL full-text ranking, not BM25, and exact cosine ranking over the eligible relation. Equal-weight reciprocal rank fusion uses one-based ranks and constant 60. Return raw cosine similarity, keyword rank/absence and keyword score alongside fused score. Candidate lists are bounded but exact scanning is not sublinear. No reranker or abstention threshold is implemented.

## Consequences

Heading-only chunks and token-boundary cuts are possible. Tokenizer/config changes can change boundaries. Ranking parameters are fixed baseline choices, not claimed optimal. Stored text and offsets remain directly checkable.

## Revisit when

A labelled retrieval evaluation demonstrates boundary or ranking failures.

## Sources

[Chunker](../../src/rag_audit/chunking.py), [retrieval](../../src/rag_audit/retrieval.py), [tests](../../tests/test_retrieval_core.py), [PostgreSQL full-text controls](https://www.postgresql.org/docs/16/textsearch-controls.html).
