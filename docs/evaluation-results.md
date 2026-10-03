# Canonical baseline results — October 3, 2026

All results use frozen source `532ddea`, revision-3 drafted labels, zero human-reviewed.
Each baseline has one logged held-out pass, no tuning or rerun after observation.
Fake is the untuned demo gate; real/live use `local-calibrated-v1` cosine >=0.75.
"Correct answer" includes code rules and uses all attempted primary phrasings as
denominator, not just answerable cases; allowed abstentions are not correct answers.
Intervals below are Wilson 95%, descriptive, not significance evidence.

| Baseline | Split | Primary n | Correct answered | Evidence sufficient | False evidence | Rule agreement | Hard failures |
| --- | --- | ---: | --- | --- | --- | --- | ---: |
| fake | dev | 84 | 11/84 (7.5–21.9%) | 4/36 (4.4–25.3%) | 0/28 (0.0–12.1%) | 8/8 (67.6–100.0%) | 0 |
| fake | test | 46 | 7/46 (7.6–28.2%) | 2/20 (2.8–30.1%) | 0/16 (0.0–19.4%) | 4/4 (51.0–100.0%) | 0 |
| real | dev | 84 | 21/84 (17.0–35.2%) | 13/36 (22.5–52.4%) | 1/28 (0.6–17.7%) | 8/8 (67.6–100.0%) | 0 |
| real | test | 46 | 10/46 (12.3–35.6%) | 6/20 (14.5–51.9%) | 0/16 (0.0–19.4%) | 4/4 (51.0–100.0%) | 0 |
| live | dev | 84 | 22/84 (18.0–36.5%) | 13/36 (22.5–52.4%) | 1/28 (0.6–17.7%) | 8/8 (67.6–100.0%) | 0 |
| live | test | 46 | 12/46 (15.6–40.3%) | 6/20 (14.5–51.9%) | 0/16 (0.0–19.4%) | 4/4 (51.0–100.0%) | 0 |

Machine-readable summaries contain every split/category/style group, paired-case
success, per-phrasing assessments, retrieval/fact metrics, verification reasons,
latency, usage and separate counterfactual totals:
[fake](../datasets/evaluation/baselines/fake-v1.json),
[real](../datasets/evaluation/baselines/real-v1.json),
[informational live](../datasets/evaluation/baselines/live-v1.json).
See [dispatch log](../datasets/evaluation/run-log.jsonl) and [definitions](evaluation.md).
Raw live output and provider configuration are not published.

## Informational live coverage and cost

Status **complete**: 130/130 primary phrasings, 0 not run. 35 network dispatches. Retained estimate USD 0.2871200 against USD 3 cap. The pre-run worst-case forecast was 35 calls / USD 4.6146750 (USD 1.6146750 potential shortfall); actual settlements release unused reservations. No retries or paid warmup. Unknown usage retains its reservation. Amounts are operator list-price estimates, not verified billing.
