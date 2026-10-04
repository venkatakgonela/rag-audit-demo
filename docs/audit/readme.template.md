# rag-audit-demo

**Prove your AI assistant is safe to release.** Access control that cannot be talked around, answers you can trace to a source, and a release gate that fails when quality drops. A working example with an audit report that states its own weaknesses.

**[Read the sample audit report](../../docs/audit/report.pdf)** · [Why it matters](../../docs/governance.md) · [Evaluation method](../../docs/evaluation.md) · [Architecture](../../docs/ARCHITECTURE.md)

![Request ownership: code controls access, rules, verification and tracing; CI and people review changes](../../docs/images/ownership-flow.png)

[Diagram source and legend](../../docs/ARCHITECTURE.md#who-does-what).

## Why it matters

Assistants over internal documents fail three costly ways: they show someone a document they must not see, state things no source supports, and a harmless-looking change quietly makes both likelier. Spot-checks miss all three; each surfaces later as an audit finding. This project makes each failure testable before release. [Examples and framework mapping](../../docs/governance.md).

## What you get

- **Confidentiality by design:** the assistant only searches documents the asker may see; tests prove it (`uv run pytest tests/integration/test_retrieval.py --run-integration`).
- **Answers you can defend:** each statement carries the exact source quote; no evidence, no answer (`uv run pytest tests/test_answer_policy.py`).
- **Numbers from code:** amounts come from ordinary, testable calculations, not the AI.
- **A release gate that can fail:** fixed questions replay on every change and the build stops if safety breaks or quality drops (`make eval-selftest`). Two deliberately failing changes show it: [gate regression #7](https://github.com/venkatakgonela/rag-audit-demo/pull/7) and [access regression #8](https://github.com/venkatakgonela/rag-audit-demo/pull/8).
- **Audit-ready evidence:** a severity-rated report with reproduction steps and honest limits.

## Frameworks it supports

Indicative mapping, not a compliance claim; see [the governance note](../../docs/governance.md).

| Framework | What this project exercises |
| --- | --- |
| NIST AI RMF | Measure and Manage: tested reliability, risk response |
| ISO/IEC 42001 | Monitoring and evaluation of an AI system |
| OWASP Top 10 for LLM Applications | Disclosure, prompt injection, misinformation |
| UK GDPR, EU AI Act | Access limitation, records, human oversight, accuracy |

## Results at a glance

{{comparison}}

The brackets are 95% ranges (Wilson intervals): with only 10 to 18 questions per row, read ranges, not single percentages. These are not system-wide accuracy; two other test phrasings regressed. **{{review}}** An AI reviewer checked all 65 labels against their sources and found no factual, outcome or visibility disagreement and three wording notes ([record](../../docs/audit/label-review.md)); that is not human review and not independent of the AI-assisted build, and every label remains `drafted`.

## Try it locally

Needs Git, Make, uv, Python 3.12 and Docker Compose; tested on macOS. No model key needed.

```sh
git clone https://github.com/venkatakgonela/rag-audit-demo.git
cd rag-audit-demo
make setup
make up
make generate-corpus
make ingest ARGS="--fake"
make ask ARGS='--fake --subject synthetic-customer-a --query "Synthetic Hearth edition 1 drying diary reading"'
```

The answer includes “The drying diary must show a reading every 24 hours.” Now contrast a restricted-topic request with a code-calculated payout:

```sh
make ask ARGS='--fake --subject synthetic-customer-a --query "broker reconciliation"'
make ask ARGS='--fake --subject synthetic-customer-a --query "payout synthetic-claim-0"'
```

The first returns “I cannot answer from the available evidence.” The second returns “Payout in GBP: 400.00 (calculation only; claim status: pending).”

Port 5433 busy? See [developer setup](../../docs/development.md); no-Docker checks: `make lint typecheck test`.

## Stage and reuse

A v0.1 reference implementation, not a library: the patterns and evaluation gate transfer, the insurance-style rules and data do not. [Reuse, and how this can help your project](../../docs/reuse.md).

## Limits

All data is synthetic. This is a builder self-assessment, not an independent audit or production service; prompt-injection checks cover a small fixture set. CI tests recorded behaviour, not future model behaviour. Written by Venkata K Gonela with AI coding assistants.

MIT © 2026 Venkata K Gonela. See [LICENSE](../../LICENSE), [notices](../../docs/third-party-notices.md), [security](../../SECURITY.md), [contributing](../../CONTRIBUTING.md), [publication provenance](../../docs/PUBLISHING.md) and [docs index](../../docs/README.md).
