# Synthetic extractive evaluation

Implemented: isolated CLI, dev calibration, independent hard checks and the calibrated local gate. CI quality gates, replay, regressive PRs and release audit remain Planned. All 65 labels are drafted, zero human-reviewed: 42 dev/23 test, each keyword/natural. The test set is visible to implementers, not a blind benchmark.

## Running

Clean checkout: `make setup`, `make up`, `make db-init`, then `make eval ARGS="--split dev --embedder fake --output /tmp/synthetic-eval"`. Real mode: `make eval ARGS="--split dev --embedder real --model-directory /path/to/cached/model --output /tmp/synthetic-real"`. Optional embedding dependencies and cached weights must already exist; the evaluator never downloads. Use a configured isolated database; every run creates/drops its own schema. Output directories must be new/empty.

`--split test` or `all` verifies accepted freeze digests and logs starts before dispatch to `datasets/evaluation/run-log.jsonl` or explicit `--run-log`. Duplicate configurations require meaningful `--rerun-reason`. Never rerun held-out data for formatting. Fresh-clone reproduction uses dev. Calibration is `--calibrate --split dev --embedder real`; it reads no test labels. Default policy uses the versioned profile; `--policy` may name experimental gate JSON.

Live additionally needs explicit environment provider configuration and `--generator live --embedder real --forecast-baseline /private/frozen-real/results.json`. Forecast input must match source commit, split, freeze, model, effective gate and relevant settings, with complete coverage/no hard failures. One run: dev then test, case ID, keyword then natural, paired probes immediately after primary. Medium reasoning, 2,048 output tokens, 60 seconds, USD 0.55/request, USD 3 total. No paid warmup/retry/second run. Reservations precede dispatch; unknown usage retains the full reservation. Prices are operator estimates, not billing.

## Metrics

- Retrieval: distinct documents ranked by first occurrence among the top 20 authorised chunks. Recall@5/@10 is covered/required documents; MRR is reciprocal rank of the first required document in that unique-document list. Section recall@5 uses distinct labelled document/section pairs in the first five chunks. No-support/rule bypass is N/A; hidden support is not positive retrieval quality.
- Evidence sufficiency: any selected chunk on single/multi extraction questions. False evidence: any selected chunk on unanswerable/unauthorised questions; separate off-domain, near-miss, ID and free-text. Related visible evidence can be false without a hidden-content leak. Injection exposure is separate.
- Fact coverage: exact required substrings in valid quotes from the labelled document and section. All-facts-covered requires every fact, including multi-source documents. Correct/wrong answered, false answer and missed answer are separate. Allowed injection abstention is successful. Case success requires both primary styles to meet their contracts.
- Hard failures: forbidden response/public-projection content, attack echoes, invalid sent/authorised citations/quotes, wrong/non-code rules, unequal unauthorised counterfactual bytes or changed hidden-removal signals/scores. Any forces nonzero exit. Rules use independent integer-pence/date arithmetic and zero provider calls.
- Rates: counts and Wilson 95% intervals. Small clustered synthetic support units are not independent real-world samples. MRR/cost/latency intervals are N/A. No significance/generalisation claims.
- Latency: nearest-rank p50/p95 per recorded stage, split by provider invoked/not. Baseline usage is UTF-8 bytes with synthetic zero prices, not model tokens. Live usage uses provider subsets: cached reads/writes are disjoint input subsets; reasoning is already in output. Unknown usage/cost counts remain explicit.
- Probes have separate rows/costs, outside primary denominators. Missing partial-run phrasings are not run, never abstentions. Stable metric digests exclude latency; raw timing remains private.

## Calibration and baseline limitations

The [114-row dev table](calibration-dev.md) follows the minimum-to-minimum+1 false-evidence band, natural then keyword sufficiency, fewer near misses, simpler variant and stricter thresholds. [local-calibrated-v1](decisions/0025-calibrated-local-gate.md) is cosine-only >=0.75. The [44-row reranker trial](reranker-dev.md) failed its gain condition. No test result chooses a threshold.

`sentence-overlap-v1` examines the first sent chunk only; splits at punctuation followed by whitespace or newline; picks a <=2,048-character span with greatest unique non-stopword ASCII-token overlap; ties use source position. Zero-overlap spans are allowed. No label/attack filtering; unchanged verifier may reject output. It cannot combine multi-chunk facts and is not an LLM quality measure.

## Canonical results

All three canonical baselines completed at frozen source `532ddea`, each with exactly one logged held-out pass: 130 primary phrasings, zero hard failures. [Results and intervals](evaluation-results.md) show every baseline separately. Correct answered on test: fake 7/46, real deterministic 10/46, informational live 12/46; these denominators include all primary controls, not just answerable questions. Live dispatched 35 requests and settled an operator estimate of USD 0.28712, below the USD 3 cap; zero unknown usage/cost. The conservative pre-run reservation forecast was USD 4.614675, but actual settlements released headroom. No paid retry or warmup. Raw live records stay private; public provider identity is neutral with a digest.

No test false evidence or hard failures occurred, but real test evidence sufficiency is only 6/20, and the live run still missed 14 answerable/rule phrasings on test. Correct safety controls do not imply useful answer coverage. The deterministic baseline answered some abstention-only dev injection challenges incorrectly without echoing attack text; live had one dev false answer. Exact verification rejected live outputs for quotation/schema/echo reasons. These are reported failures of utility/decision quality, not hidden by the zero-hard-failure result.

## Candidate audit findings

OR-based team/ownership access can intentionally cross tiers. Natural abstention improved on dev but remains high. Near-miss evidence can survive relevance gates. First-chunk generation limits multi-source accuracy. Injection verification may reject relevant sources. These are candidate findings, not a completed release audit.
