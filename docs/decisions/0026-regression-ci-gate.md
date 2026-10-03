# 0026: Read-only regression gate with measured tolerances

Status: Accepted

Recorded: October 3, 2026; hosted numerical validation pending.

## Context

The frozen synthetic evaluation has a real-model recording but unit tests do not guard its quality. Repeated CI observations must not become unlogged calibration exposures. All 65 labels remain drafted, zero human-reviewed.

## Decision drivers

Non-negotiable safety; interpretable counts on tiny sets; no live calls, automatic baseline updates or test-driven threshold tuning. Changed requests must fail rather than hide within tolerances.

## Options considered

- Safety-only CI is cheap, but misses declining retrieval and answer coverage.
- Live generation exercises new behaviour but needs credentials, spend and a reachable provider, and introduces nondeterminism. Keep it explicit and local.
- Recorded HTTP replay plus real embeddings tests adapter, retrieval, verification and accounting with fixed provider behaviour. Adopt with staleness checks and clear limits.
- Percentage/statistical thresholds imply unwarranted precision on tiny dependent samples. Use absolute counts and observed numerical evidence instead.

## Decision

Use a separate read-only evaluator and committed `ci-v1` baseline. Hard checks cover forbidden content, citations/quotes, rules, counterfactual bytes/signals, injection echoes, operational errors, coverage and replay integrity. Soft checks compare sufficiency and correct-answer counts by split/style, recall hits with fixed denominators, MRR sum/count, verification sub-reasons and Decimal estimated cost/call. False evidence by subtype and unknown cost may never increase. Latency is informational.

Two macOS ARM64 and two emulated Linux AMD64 runs reproduced live metrics exactly, excluding latency, consuming the same 35 requests. Across 2,368 candidate cosines, absolute delta median was 6.584513678742354e-8, p95 1.979421115905211e-7, p99 2.591297710852203e-7 and maximum 3.241387346308855e-7. No ranking/selection flips or missing candidates occurred. Both used the same ARM64 PostgreSQL service: this isolates Python/ONNX differences, not an entirely x86 stack.

Therefore count, MRR and cost allowances are zero in the [policy](../../datasets/evaluation/gate-policy.json), **provisional until the first hosted CPU run**. Emulation is not the hosted processor; ONNX has hardware-specific kernels. Native Linux ARM64 was not measured. No change to cosine 0.75 is authorised by these observations.

Regression checks never write historical baselines or the exposure log. Intentional changes require a meaningful reason, CHANGELOG marker and local `make eval-rebaseline`; baseline/config digests and previous-digest chain enter a committed log. CI refuses that command. An edited baseline without its corresponding log/config fails. Review is the trust root: coordinated changes to checks, manifests and log are not cryptographically prevented.

First hosted run: compare every gate value, request/selection identities, metric deltas and cold/warm time. Retain any differences and distinguish hardware numerics from code changes. At most one phrasing allowance may be proposed with evidence and logged rebaseline; greater drift, any safety/integrity problem, or changed requests stops for a decision. Never silently increase tolerance or regenerate fixtures to turn CI green.

## Consequences

Repeatable no-spend regression evidence, not new model validation or statistical generalisation. Faulty-variant tests require passing controls; deliberate mutations demonstrate those tests can fail. Baseline utility remains low. Hosted execution is unverified until run separately.

## Revisit when

First hosted run, model/runtime/runner/corpus changes, human label review, or intentional policy changes. Changes to the original freeze need their own exposure protocol.

## Sources

- [Gate](../../src/rag_audit/evaluation/ci_gate.py), [checks](../../src/rag_audit/evaluation/gate_checks.py), [self-tests](../../tests/integration/test_gate_selftest.py).
- [ONNX Runtime](https://onnxruntime.ai/docs/) and [evaluation protocol](../evaluation.md#ci-regression-gate).
