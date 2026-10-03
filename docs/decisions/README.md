# Architecture decision records

Record significant product choices here. Preserve accepted decision text; dated additive clarifications may extend structure without changing the decision. Supersede substantive changes. Alternatives in retrospective records are current assessments, not invented historical trials. See the [evidence convention](../README.md#evidence-convention).

## Index

| Record | Status | Recorded |
| --- | --- | --- |
| [0001: Architecture records](0001-record-architecture-decisions.md) | Accepted | October 2, 2026; additive schema clarification same date |
| [0002: Python and uv](0002-python-uv-locking.md) | Accepted | October 2, 2026; retrospective |
| [0003: FastAPI](0003-fastapi.md) | Accepted | October 2, 2026; retrospective |
| [0004: PostgreSQL and pgvector](0004-postgresql-pgvector.md) | Accepted for foundation; retrieval unvalidated | October 2, 2026; retrospective |
| [0005: Settings and secrets](0005-settings-secrets.md) | Accepted | October 2, 2026; retrospective |
| [0006: psycopg without ORM](0006-psycopg-no-orm.md) | Accepted | October 2, 2026; retrospective |
| [0007: Make interface](0007-make-interface.md) | Accepted | October 2, 2026; retrospective |
| [0008: Local Compose](0008-local-compose.md) | Accepted | October 2, 2026; retrospective |
| [0009: CI jobs](0009-ci-jobs.md) | Accepted | October 2, 2026; retrospective |
| [0010: Test strategy](0010-test-strategy.md) | Accepted | October 2, 2026; retrospective |
| [0011: Liveness and version](0011-liveness-version.md) | Accepted | October 2, 2026; retrospective |
| [0012: Mermaid](0012-mermaid.md) | Accepted | October 2, 2026; new documentation decision |
| [0013: Synthetic original work](0013-synthetic-original-work.md) | Accepted | October 2, 2026; retrospective |
| [0014: Query access control](0014-query-access-control.md) | Accepted | October 2, 2026 |
| [0015: Section chunks and fusion](0015-section-chunks-and-fusion.md) | Accepted | October 2, 2026 |
| [0016: Local embedding runtime](0016-local-embedding-runtime.md) | Accepted | October 2, 2026 |
| [0017: Rules, routing and identity](0017-rules-routing-identity.md) | Accepted | October 2, 2026 |
| [0018: Extractive answer policy](0018-extractive-answer-policy.md) | Accepted | October 2, 2026 |
| [0019: Generation, tracing and accounting](0019-generation-tracing-accounting.md) | Accepted | October 2, 2026 |
| [0020: Opt-in Responses integration](0020-opt-in-responses-provider.md) | Accepted | October 3, 2026 |
| [0021: Versioned evaluation data](0021-versioned-evaluation-data.md) | Accepted; labels drafted | October 3, 2026 |
| [0022: Answer outcome presentation](0022-answer-outcome-presentation.md) | Accepted | October 3, 2026 |

## Pending decisions

All entries are **Planned**, not accepted choices. Milestones describe product work, not implementation commitments.

| Question | Options to weigh and constraints | Decision milestone |
| --- | --- | --- |
| Reranker | None versus local cross-encoder; quality/latency trade-off | Retrieval evaluation |
| Production provider deployment | Opt-in local Responses integration exists; deployment and production identity remain undecided | Production design |
| Extractive evaluation and calibration | Key-fact and citation checks, dev-only calibration; no LLM judge | Evaluation harness |
| CI gate thresholds | Zero-leak/citation/rule safety constraints plus evidence-based quality tolerance | Regression gate |
| Profile calibration | Per-embedder provisional constants exist; labelled precision/recall calibration remains planned | Retrieval evaluation |
| Billing and tighter token bounds | Versioned estimates and qualified byte bound exist; invoice reconciliation and verified tokenizer counter remain planned | Production accounting |
| Workflow supply chain | Action SHA pins, update automation and image digests | CI hardening |
| Runner image | Pin ubuntu-24.04 versus follow ubuntu-latest; migration compatibility | CI hardening |
| Repository licence | Candidate permissive terms versus retaining current restrictions pending an explicit choice | Publication policy |

## Template

```markdown
# NNNN: Decision title

Status: Proposed | Accepted | Superseded by NNNN

## Context

What problem and constraints require a decision?

## Decision drivers

Which quality attributes and constraints matter most?

## Options considered

At least two real alternatives with pros, cons, and reasons for not selecting them.

## Decision

What will the product do, and why?

## Consequences

What benefits, costs, risks, and follow-up work result?

## Revisit when

What evidence or changed constraint would reopen this choice?

## Sources

Link implementation/test evidence and official behaviour references; mark uncertainty.
```
