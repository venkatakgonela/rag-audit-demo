# rag-audit-demo

A synthetic demonstration of how to **test and audit a retrieval-augmented answering system**, including the results that did not improve. It is a builder self-assessment, not an independent audit or production service. Built with AI coding assistants under Venkata K Gonela's direction.

**[Read the sample audit report](../../docs/audit/report.pdf)** · [Markdown report](../../docs/audit/report.md) · [Evaluation method](../../docs/evaluation.md)

## Three tested promises

- **Access inside the query:** authorised documents are selected before ranking. Proof: `uv run pytest tests/integration/test_retrieval.py --run-integration` with a disposable database.
- **Verifiable quotes:** every accepted statement references authorised retrieved evidence and exact source text. Proof: `uv run pytest tests/test_answer_policy.py` (no database/key).
- **A gate that can fail:** immutable recorded requests, safety constraints and quality checks stop regression. Proof: `make eval-selftest` with cached model/database; [deliberate gate regression #7](https://github.com/venkatakgonela/rag-audit-demo/pull/7) and [access regression #8](https://github.com/venkatakgonela/rag-audit-demo/pull/8). Links require access while private.

## Results at a glance

{{comparison}}

These are correct answerable single/multi phrasings, not system-wide accuracy. Explicit refusal plus dev-selected calibration improved this single recorded comparison; two other test phrasings regressed. Small authored samples, repeated test exposure and cached dev responses limit inference. **{{review}}**

## Try it locally

Prerequisites: Git, Make, uv/Python 3.12 and Docker Compose. Initial dependency/image setup may download; fake answering needs no model or provider key. Once dependencies and the database image are cached, use `UV_OFFLINE=1` for dependency operations.

```sh
make setup
make up
make ingest ARGS="--fake"
make ask ARGS='--fake --subject synthetic-customer-a --query "What does the drying diary need?"'
```

The default database binds to loopback. `make down` stops it without deleting its volume. For checks without Docker: `make lint typecheck test`. See [developer setup and configuration](../../docs/development.md) for explicit ports, isolated databases and commands.

Optional real embeddings: provision the documented pinned model once with `make eval-model ARGS="--provision"` after `make eval-runtime`. For already cached weights, `make eval-model` verifies them, then `make eval-gate` and `make eval-selftest` use the real adapter with recorded responses and no provider key. Model downloads are explicit; real generation is separately opt-in and is not needed for this demo.

## Architecture

![Implemented retrieval, rules, verification and trace components](../../docs/audit/figures/components.png)

Access-scoped retrieval selects evidence, deterministic code computes rules, and the model proposes quotes or abstains. The service verifies the complete answer and stores its trace before release. [Architecture and trust boundaries](../../docs/ARCHITECTURE.md).

## Evaluation and CI

The frozen synthetic corpus, labels and versioned baselines preserve failed and successful outcomes. Development data selects thresholds; test results do not. Current release checks replay recorded HTTP responses through the actual adapter, enforce hard constraints and compare quality without tolerances. They test **recorded behaviour**, not future model behaviour.

The hosted reference and red proof runs are documented in the [report](../../docs/audit/report.md) with run provenance. Rebaselining is an explicit, logged local operation, never a shortcut to make failures green. See the [protocol](../../docs/evaluation.md#failure-and-re-baseline-protocol) and [publication checklist](../../docs/PUBLISHING.md).

## Limits

All insurance-like data and identities are fabricated. Exact quotation is not semantic completeness. The identity stub, timing/resource bounds, retained questions and mutable supply-chain references are not production controls. Prompt-injection checks cover a small fixture set; no general resistance, compliance, billing or availability guarantee is made. Read the findings and the two lost test successes, not only the improvements.

## Repository map

- `src/rag_audit/`: retrieval, rules, answering, traces and local API.
- `tests/`: unit, database integration and deliberate gate faults.
- `datasets/evaluation/`: immutable references, labels and exposure history.
- `docs/audit/`: source, generated tables, evidence index, report and local assets.
- `docs/decisions/`: choices, alternatives and revisit triggers.
- `scripts/`: reproducible report and inventory checks.

## Licence and author

MIT © 2026 Venkata K Gonela. See [LICENSE](../../LICENSE), [third-party notices](../../docs/third-party-notices.md) and [security policy](../../SECURITY.md). Dependencies retain their own licences; model weights are not redistributed. A prepared release is not an announcement of production readiness.
