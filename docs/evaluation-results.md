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

## Explicit abstention: second live reference — October 3, 2026

The historical tables above remain unchanged. The current profile is `local-calibrated-v2` (V1 0.70), selected using dev only. Final dev reuses the original candidate samples; test contains 21 new unique requests. This is one live draw per request, not an estimated reliability rate. Both references use the same author-written labels, with **zero human review**. The historical test set now has a second live exposure and is no longer pristine. Wilson 95% intervals below are descriptive, not a significance test.

### Complete dev candidate grid

| Threshold | Natural correct /18 | Keyword correct /18 | Free-text false answers | Near-miss false answers | Hard/errors | Eligible |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 0.75 | 5 | 5 | 0 | 0 | 0/0 | True |
| 0.70 | 9 | 9 | 0 | 0 | 0/0 | True |
| 0.65 | 14 | 12 | 1 | 0 | 0/0 | False |
| 0.60 | 14 | 14 | 1 | 0 | 0/0 | False |

All candidates completed 84 primaries. Off-domain and ID-style false answers were zero throughout. The declared rule selected 0.70: natural correct increased by four (5 to 9), above the required three; near-miss false answers fell from one to zero. Lower gates are ineligible, despite better coverage. [Decision and limits](decisions/0030-abstention-recalibration.md).

### Answerable single/multi phrasings

| Split/style | Before correct (95% interval) | After correct (95% interval) |
| --- | --- | --- |
| dev/keyword | 5/18 (12.5–50.9%) | 9/18 (29.0–71.0%) |
| dev/natural | 5/18 (12.5–50.9%) | 9/18 (29.0–71.0%) |
| test/keyword | 3/10 (10.8–60.3%) | 5/10 (23.7–76.3%) |
| test/natural | 2/10 (5.7–51.0%) | 5/10 (23.7–76.3%) |

### Every category and style

Correct-answer denominators here include every primary in the category; allowed no-answers are counted separately, not as correct answers. Gate/model/reject are before→after counts; errors are zero in every group.

| Split/category/style | Before correct (95% interval) | After correct (95% interval) | False before→after | Gate before→after | Model before→after | Reject before→after | Correct abstention before→after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev/injection/keyword | 2/6 (9.7–70.0%) | 2/6 (9.7–70.0%) | 0→0 | 1→0 | 0→1 | 2→3 | 3→4 |
| dev/injection/natural | 2/6 (9.7–70.0%) | 3/6 (18.8–81.2%) | 0→0 | 0→0 | 0→1 | 4→2 | 4→3 |
| dev/multi/keyword | 0/5 (0.0–43.4%) | 0/5 (0.0–43.4%) | 0→0 | 4→2 | 0→2 | 0→0 | 0→0 |
| dev/multi/natural | 0/5 (0.0–43.4%) | 0/5 (0.0–43.4%) | 0→0 | 5→2 | 0→2 | 0→0 | 0→0 |
| dev/rules/keyword | 4/4 (51.0–100.0%) | 4/4 (51.0–100.0%) | 0→0 | 0→0 | 0→0 | 0→0 | 0→0 |
| dev/rules/natural | 4/4 (51.0–100.0%) | 4/4 (51.0–100.0%) | 0→0 | 0→0 | 0→0 | 0→0 | 0→0 |
| dev/single/keyword | 5/13 (17.7–64.5%) | 9/13 (42.4–87.3%) | 0→0 | 7→2 | 0→2 | 0→0 | 0→0 |
| dev/single/natural | 5/13 (17.7–64.5%) | 9/13 (42.4–87.3%) | 0→0 | 7→4 | 0→0 | 0→0 | 0→0 |
| dev/unanswerable/keyword | 0/7 (0.0–35.4%) | 0/7 (0.0–35.4%) | 0→0 | 7→4 | 0→3 | 0→0 | 7→7 |
| dev/unanswerable/natural | 0/7 (0.0–35.4%) | 0/7 (0.0–35.4%) | 1→0 | 6→5 | 0→2 | 0→0 | 6→7 |
| dev/unauthorised/keyword | 0/7 (0.0–35.4%) | 0/7 (0.0–35.4%) | 0→0 | 7→6 | 0→1 | 0→0 | 7→7 |
| dev/unauthorised/natural | 0/7 (0.0–35.4%) | 0/7 (0.0–35.4%) | 0→0 | 7→6 | 0→1 | 0→0 | 7→7 |
| test/injection/keyword | 2/3 (20.8–93.9%) | 2/3 (20.8–93.9%) | 0→0 | 1→0 | 0→0 | 0→1 | 1→1 |
| test/injection/natural | 1/3 (6.1–79.2%) | 1/3 (6.1–79.2%) | 0→0 | 1→0 | 0→0 | 1→2 | 2→2 |
| test/multi/keyword | 0/3 (0.0–56.1%) | 0/3 (0.0–56.1%) | 0→0 | 3→3 | 0→0 | 0→0 | 0→0 |
| test/multi/natural | 0/3 (0.0–56.1%) | 0/3 (0.0–56.1%) | 0→0 | 3→2 | 0→1 | 0→0 | 0→0 |
| test/rules/keyword | 2/2 (34.2–100.0%) | 2/2 (34.2–100.0%) | 0→0 | 0→0 | 0→0 | 0→0 | 0→0 |
| test/rules/natural | 2/2 (34.2–100.0%) | 2/2 (34.2–100.0%) | 0→0 | 0→0 | 0→0 | 0→0 | 0→0 |
| test/single/keyword | 3/7 (15.8–75.0%) | 5/7 (35.9–91.8%) | 0→0 | 3→0 | 0→2 | 0→0 | 0→0 |
| test/single/natural | 2/7 (8.2–64.1%) | 5/7 (35.9–91.8%) | 0→0 | 5→1 | 0→0 | 0→1 | 0→0 |
| test/unanswerable/keyword | 0/4 (0.0–49.0%) | 0/4 (0.0–49.0%) | 0→0 | 4→4 | 0→0 | 0→0 | 4→4 |
| test/unanswerable/natural | 0/4 (0.0–49.0%) | 0/4 (0.0–49.0%) | 0→0 | 4→3 | 0→1 | 0→0 | 4→4 |
| test/unauthorised/keyword | 0/4 (0.0–49.0%) | 0/4 (0.0–49.0%) | 0→0 | 4→4 | 0→0 | 0→0 | 4→4 |
| test/unauthorised/natural | 0/4 (0.0–49.0%) | 0/4 (0.0–49.0%) | 0→0 | 4→4 | 0→0 | 0→0 | 4→4 |

### False answers versus false evidence

| Split/subtype | False answers before→after | Selected false evidence before→after |
| --- | --- | --- |
| dev/off_domain | 0→0 | 0→0 |
| dev/id_lookup | 0→0 | 0→0 |
| dev/free_text | 0→0 | 0→2 |
| dev/near_miss | 1→0 | 1→5 |
| test/off_domain | 0→0 | 0→0 |
| test/id_lookup | 0→0 | 0→0 |
| test/free_text | 0→0 | 0→0 |
| test/near_miss | 0→0 | 0→1 |

Final primary false answers and hard failures are zero on both splits. More false evidence can be selected even when the model declines: abstention does not erase an evidence-selection error. Rejected outputs (including echoed attack text and non-extractive wording) remain in the replay fixtures unchanged.

### Paired per-phrasing transitions

| Split | Correct→correct | Incorrect/not answered→correct | Correct→not correct | Other unchanged correctness |
| --- | ---: | ---: | ---: | ---: |
| dev | 22 | 9 | 0 | 53 |
| test | 10 | 7 | 2 | 27 |

The two lost test successes are both phrasings of case-058: the model returned text shorter than its quoted passage, so unchanged quotation verification correctly rejected it. The overall test gain does not erase these regressions, and no test-based retuning or resampling was performed.

The complete unchanged historical [live-v1](../datasets/evaluation/baselines/live-v1.json) and new [live-v2](../datasets/evaluation/baselines/live-v2.json) retain per-phrasing outcomes and split/category/style metrics. The [exposure log](../datasets/evaluation/run-log.jsonl) appends one start/completion. macOS ARM64 and emulated Linux AMD64 replay match all non-latency live-v2 metrics; the database runs on the same local ARM host, not an independent native Linux deployment. Hosted verification remains pending.

Total known operator estimates USD 1.64388 plus retained unknown 429 hold USD 0.1460375 = USD 1.7899175; final phase USD 0.18831. The 429-only policy amendment occurred after the observed interruption, not before the original experiment. Historical-average forecasts are scenarios, not guaranteed bills; total worst-case reservations are not concurrent holds.
