# rag-audit-demo

A synthetic demonstration of how to **test and audit a retrieval-augmented answering system**, including the results that did not improve. It is a builder self-assessment, not an independent audit or production service. Built with AI coding assistants under Venkata K Gonela's direction.

**[Read the sample audit report](docs/audit/report.pdf)** · [Markdown report](docs/audit/report.md) · [Evaluation method](docs/evaluation.md)

## Three tested promises

- **Access inside the query:** authorised documents are selected before ranking. Proof: `uv run pytest tests/integration/test_retrieval.py --run-integration` with a disposable database.
- **Verifiable quotes:** every accepted statement references authorised retrieved evidence and exact source text. Proof: `uv run pytest tests/test_answer_policy.py` (no database/key).
- **A gate that can fail:** immutable recorded requests, safety constraints and quality checks stop regression. Proof: `make eval-selftest` with cached model/database; [deliberate gate regression #7](https://github.com/venkatakgonela/rag-audit-demo/pull/7) and [access regression #8](https://github.com/venkatakgonela/rag-audit-demo/pull/8). Links require access while private.

## Results at a glance

| Split | Style | Before correct; Wilson 95% | After correct; Wilson 95% |
| --- | --- | --- | --- |
| dev | keyword | 5/18 (12.5-50.9%) | 9/18 (29.0-71.0%) |
| dev | natural | 5/18 (12.5-50.9%) | 9/18 (29.0-71.0%) |
| test | keyword | 3/10 (10.8-60.3%) | 5/10 (23.7-76.3%) |
| test | natural | 2/10 (5.7-51.0%) | 5/10 (23.7-76.3%) |

Source: `datasets/evaluation/baselines/live-v1.json` at `cfd53ff`, `datasets/evaluation/baselines/live-v2.json` at `cfd53ff`. Full hashes: docs/audit/evidence-manifest.json.

These are correct answerable single/multi phrasings, not system-wide accuracy. Explicit refusal plus dev-selected calibration improved this single recorded comparison; two other test phrasings regressed. Small authored samples, repeated test exposure and cached dev responses limit inference. **No label has been reviewed by anyone other than the author (65 labels).** An AI reviewer checked all 65 labels against their sources and found no factual, outcome or visibility disagreement and three wording notes ([record](docs/audit/label-review.md)); that is not human review and not independent of the AI-assisted build, and every label remains `drafted`.

## Try it locally

Prerequisites: Git, Make, uv/Python 3.12 and running Docker Compose. Tested on macOS; Linux and Windows are untested locally. Setup may download locked dependencies/database image; fake answering needs no model or provider key. Cached dependencies support `UV_OFFLINE=1`.

```sh
git clone https://github.com/venkatakgonela/rag-audit-demo.git
cd rag-audit-demo
make setup
make up
make generate-corpus
make ingest ARGS="--fake"
make ask ARGS='--fake --subject synthetic-customer-a --query "Synthetic Hearth edition 1 drying diary reading"'
```

The answer includes: “The drying diary must show a reading every 24 hours.”
For the same customer, contrast a restricted-topic request with a code-calculated payout:

```sh
make ask ARGS='--fake --subject synthetic-customer-a --query "broker reconciliation"'
make ask ARGS='--fake --subject synthetic-customer-a --query "payout synthetic-claim-0"'
```

The first returns “I cannot answer from the available evidence.” The second returns
“Payout in GBP: 400.00 (calculation only; claim status: pending).” These are synthetic
demonstration outputs, not insurance advice or an eligibility decision.

While private, cloning requires repository access. The database binds to loopback port5433; if occupied, change both `POSTGRES_PORT` and the port in `DATABASE_URL` in `.env` before starting. `make down` stops it without deleting its volume. Checks without Docker: `make lint typecheck test`. See [developer setup](docs/development.md) for isolation and optional real embeddings.

## Architecture

![Implemented retrieval, rules, verification and trace components](docs/audit/figures/components.png)

Access-scoped retrieval selects evidence, deterministic code computes rules, and the model proposes quotes or abstains. The service verifies the complete answer and stores its trace before release. [Architecture and trust boundaries](docs/ARCHITECTURE.md).

## Evaluation and CI

CI tests **recorded behaviour**, not future model behaviour. See [developer reference and repository map](docs/development.md), [rebaseline protocol](docs/evaluation.md#failure-and-re-baseline-protocol) and [publication provenance](docs/PUBLISHING.md).

## Limits

All insurance-like data and identities are fabricated. Exact quotation is not semantic completeness. The identity stub, timing/resource bounds, retained questions and mutable supply-chain references are not production controls. Prompt-injection checks cover a small fixture set; no general resistance, compliance, billing or availability guarantee is made. Read the findings and the two lost test successes, not only the improvements.

## Licence and author

MIT © 2026 Venkata K Gonela. See [LICENSE](LICENSE), [notices](docs/third-party-notices.md), [security](SECURITY.md), [contributing](CONTRIBUTING.md) and [docs index](docs/README.md). Dependencies retain their licences; model weights are not redistributed. A prepared release is not production readiness.
