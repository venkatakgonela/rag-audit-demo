# rag-audit-demo

An audit-grade RAG service with an evaluation harness: access-controlled retrieval, cited answers, an explicit "I don't know" path, deterministic business rules kept separate from the LLM, and a CI gate that blocks regressions.

> **All data in this repository is synthetic.** It models a fictional insurer. Nothing here is real customer, policy or claims data.

## Status

Under active development. Nothing below is claimed as working until it ships with tests.

| Area | Status |
| --- | --- |
| Project skeleton, Docker Compose + pgvector, CI | planned |
| Synthetic corpus and ACL model | planned |
| Hybrid retrieval with pre-filter access control | planned |
| Rules layer and answer policy (citations, refusal) | planned |
| Evaluation harness and golden set | planned |
| CI regression gate | planned |
| Cost and latency tracing | planned |
| Sample AI audit report | planned |

## Design

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for components and non-goals, and [AGENTS.md](AGENTS.md) for the engineering rules every change must respect.
