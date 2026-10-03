# 0023: Do not adopt the evaluated CPU reranker

Status: Accepted
Recorded: October 3, 2026, after the predeclared dev-only trial.

## Context

The original 114-configuration dev calibration selected cosine-only at 0.75 with natural evidence sufficiency 6/18. This triggered a conditional trial of one local cross-encoder. The fixed 44-configuration experiment is complete; no test-split results or paid generation informed this choice.

## Decision drivers

Keep access control and rules unchanged; avoid new false evidence; require at least a ten-percentage-point natural sufficiency gain; remain CPU-only below 500 MiB artifacts, 1 GiB additional peak RSS and two seconds warm p95 per 20 candidates. Use the predeclared anchored selection rule, not a post-hoc threshold.

## Options considered

- Retain the non-reranker cosine-only selection: simpler and no second model; only 6/18 natural sufficiency. Selected as the fallback for subsequent profile integration.
- Adopt the pinned MiniLM cross-encoder with relevance-only or a loose cosine floor: resources and safety pass for the selected row, but 7/18 natural sufficiency is below the required 8/18. Not adopted.
- Use a lower relevance threshold: can reach 12/18 natural sufficiency, but adds near-miss false evidence and falls outside the anchored selection band. Rejected under unchanged safety/selection criteria.
- Try another model or tune the grid: may improve results but exceeds this single-candidate, predeclared trial. Not pursued.

## Decision

Do not adopt this reranker. Combined selection over 158 configurations chooses V4a relevance >=0.95, natural 7/18 and keyword 10/18, with one near miss and no other false evidence. Its +5.56-point natural gain fails the >=10-point adoption condition. Keep the experimental adapter and reproducible dev trial separate from the runtime default. The fallback remains V1 cosine >=0.75; its final default integration is pending.

## Consequences

Avoid a second deployed model without sufficient demonstrated gain. The experiment establishes a measured result, not “not evaluated” or “zero benefit.” Resources passed: 87.49 MiB artifacts, 157.34 MiB additional RSS upper bound, exactly-20-candidate warm p95 0.0831 seconds. All 440 hidden-removal score/response comparisons pass, with no hard failure or operational error across the grid. These are drafted synthetic dev labels, not general-domain quality or security proof. Sufficiency means at least one selected chunk, not a correct answer. Wide intervals and near-miss trade-offs remain in the [full trial report](../reranker-dev.md).

## Revisit when

Human-reviewed, materially expanded dev evidence or changed resource/quality requirements justify a separately predeclared experiment. Do not reopen based on later held-out outcomes from the same evaluation.

## Sources

- [Full fixed grid, intervals and resource evidence](../reranker-dev.md).
- [Original dev calibration](../calibration-dev.md).
- [Pinned artifacts and publisher provenance](../third-party-notices.md).
- [Trial implementation](../../src/rag_audit/evaluation/reranker_trial.py), [adapter tests](../../tests/test_reranking.py) and [hidden-removal checks](../../tests/integration/test_evaluation_runner.py).
