# 0025: Adopt the dev-calibrated cosine-only local gate

Status: Accepted
Recorded: October 3, 2026, before canonical held-out evaluation.

## Context

The former real gate required cosine >=0.55 and an all-terms lexical hit. Natural questions often failed that conjunction. Fixed dev calibration and one conditional reranker trial are complete.

## Decision drivers

Preserve ACLs and verification, improve evidence selection without new off-domain/unauthorised false evidence, and follow the predeclared selection without test tuning.

## Options considered

- Original conjunction: historical behaviour but natural sufficiency 0/18, keyword 5/18 on dev.
- Cosine-only >=0.75: natural 6/18, keyword 7/18, one near miss and zero other false evidence; wins the original anchored selection.
- Lexical-coverage conjunction/bonus: tested on the fixed grid, none wins the declared order.
- Local reranker: 7/18 natural is below the required 8/18; not adopted under [ADR 0023](0023-cpu-reranker-trial.md).

## Decision

Adopt `local-calibrated-v1`, V1 cosine >=0.75 for the pinned real embedder, without requiring positive keyword score/rank. Preserve finite-signal checks, whole-chunk/context limits, retrieval order, ACLs, rules and verification. Fake embeddings keep `fake-demo-v1`, V0 >=0.15 and the lexical conjunction. No default reranker. Explicit experimental gates are recorded separately from profile identity.

## Consequences

Default dev reproduces 6/18 natural and 7/18 keyword sufficiency. Sufficiency is not correctness; one near miss remains. Held-out results will be measured once after implementation freeze, not used for tuning. Model/corpus changes invalidate this limited calibration evidence.

## Revisit when

A new model/corpus or expanded human-reviewed dev set justifies new calibration and a profile version; never tune to the current held-out result.

## Sources

- [114 original rows](../calibration-dev.md), [44 reranker rows](../reranker-dev.md).
- [Runtime profile](../../src/rag_audit/policy.py), [profile boundary tests](../../tests/test_answer_policy.py).
