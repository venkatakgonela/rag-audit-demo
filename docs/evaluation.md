# Synthetic extractive evaluation

Implemented: isolated CLI, dev calibration, hard checks, calibrated local gate and recorded-HTTP regression configuration. Hosted execution, regressive PRs and release audit remain unverified/planned. All 65 labels are drafted, zero human-reviewed: 42 dev/23 test, each keyword/natural. The test set is visible to implementers, not a blind benchmark.

## CI regression gate

After `make setup`, run `make eval-runtime`, then `make eval-model ARGS="--provision"` for first-time trusted model provisioning. Subsequent `make eval-model` verifies bytes, including cache hits; existing corrupt/incomplete directories fail without automatic repair. With isolated `DATABASE_URL`, run `make db-init`, `make eval-gate` and `make eval-selftest`. No provider key is needed. Bootstrap may download dependencies/model; replay traps Python networking except the database connection opened beforehand. Default unit/lint/type checks need neither model nor Docker. Integration skips expensive self-tests unless `SYNTHETIC_MODEL_DIRECTORY` is explicit; `eval-selftest` supplies it.

The current 66 neutral responses pass through the real Responses adapter across 130 primary phrasings and 22 probes (68 provider consumptions, including two identical paired requests). Replay matches `live-v2.json` metrics except latency on macOS ARM64 and emulated Linux AMD64. This checks **recorded model behaviour**, not new model behaviour. Cost uses recorded usage/operator prices (not billing); replay spends nothing. Request hashes cover prompt/schema/settings/evidence. Every entry must be consumed exactly by its declared case/style/pair-side contexts and count. Unknown, repeated-context and unused requests are staleness, never tolerance issues. The previous 35-entry fixture and gate baseline are preserved byte-for-byte in `datasets/evaluation/archive/pre-abstention-v1/`; historical fake/real/live-v1 and exposure-log prefixes are unchanged.

| Check family | Rule |
| --- | --- |
| Forbidden content, citation/quote, rule, counterfactual, injection echo | Zero failures |
| Freeze/model/fixture/config/baseline integrity, completeness, errors, replay | Exact; no allowance |
| Sufficiency and correct answered per split/style | No count decrease |
| Document recall@5 hits and MRR sum | No decrease; denominators exact |
| False evidence by off-domain/ID/free-text/near-miss | No increase |
| False answers by style/subtype; missed answers | No increase |
| Correct abstention; model abstention | No decrease; exact recorded model-abstention count respectively |
| Verification sub-reasons; Decimal cost/call; unknown cost | No increase |
| Latency | Informational |

Allowances are zero, **provisional until hosted validation**. [ADR 0026](decisions/0026-regression-ci-gate.md) records measurements/limits. These are absolute regression guards, not significance tests. Output is check/baseline/current/pass-fail and verdict, without test row details. `--output` optionally saves aggregate JSON (temporary directory by default). Detailed diagnostics are separate: `python -m rag_audit.evaluation.regression --output /tmp/new-diagnostic.json`; never publish its test rows in CI logs.

### Failure and re-baseline protocol

1. Preserve output. Resolve config/hash/cache errors before interpreting quality. Restore known pinned bytes, never edit trusted hashes to match corruption.
2. Profile changes may fail configuration before numeric checks. Diagnose changed retrieval/selection separately without relaxing the production gate.
3. CI observations are not baseline exposures: historical fake/real/live baselines and `run-log.jsonl` are never written. Do not tune against repeated test outcomes.
4. Intentional reviewed changes require evidence, reason and a unique CHANGELOG marker first. Run locally: `make eval-rebaseline ARGS="--reason 'Meaningful reviewed change with measured evidence' --marker unique-change-marker"`. It refuses CI and safety/incomplete/replay failures. Commit baseline, policy/config changes, chained baseline log and changelog together. New calibration/live exposures follow the existing separate logging rules.
5. Changed requests require investigation, explicit recording approval, forecast and exposure reason. Use `make eval-record ARGS="--allow-live-recording --reason 'Approved recording with frozen policy evidence' --forecast-baseline /private/frozen-real/results.json --output /private/new-recording"`. Key stays in its configured environment variable. Real/all/live mode is fixed; the existing USD 3 reservation ledger/cap applies. Output contains private `candidate-replay`, never automatic public replacements. Review every response and scan identities/secrets before promotion, replay equality and logged rebaseline. Never clean rejected/injection text to pass.
6. First hosted CPU run: retain gate table, selection/request differences, metric deltas and cold/warm times. A measured one-phrasing numerical allowance may be proposed via the logged protocol, not silently edited. Greater drift, safety/integrity changes or fixture staleness requires a separate decision. Emulated AMD64 is not hosted numerical evidence.

Coordinated edits to checks/manifests/baseline/log can bypass in-repository integrity; trusted review remains necessary. Passing regressions does not cure low coverage or zero human-reviewed labels.

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

The historical [114-row dev table](calibration-dev.md) selected [local-calibrated-v1](decisions/0025-calibrated-local-gate.md), cosine-only >=0.75. The [44-row reranker trial](reranker-dev.md) failed its gain condition. The subsequent complete four-candidate live dev trial selects [local-calibrated-v2](decisions/0030-abstention-recalibration.md), cosine-only >=0.70 with explicit model abstention. No test result chooses a threshold.

## Explicit abstention and second live reference

The model returns `answer` with 1–5 statements or `insufficient_evidence` with none. Local validation, not provider schema acceptance, enforces the combination. A valid refusal maps to unchanged no-answer bytes with a private `model_abstained` reason. Gate abstention, model abstention, verification rejection and operational error are reported separately; abstention is not a safety control. Existing citation/quotation/echo/rule checks remain unchanged.

The predeclared dev candidates were V1 0.75, 0.70, 0.65 and 0.60. Eligibility required complete error-free coverage, no hard failures, and zero off-domain/ID/free-text false answers. Ranking used natural correct, keyword correct, fewer near-miss false answers, then stricter gate. Adoption required at least 8/18 natural correct and at most one near-miss false answer. The selected 0.70 achieved 9/18 and zero. Lower candidates failed free-text eligibility. See the additive before/after tables in [results](evaluation-results.md).

One sample per distinct full request was cached across dev candidates. Final dev reuses those samples; only 21 previously unseen final test requests were dispatched. Exactly one new held-out start and completion were appended. This is the second live exposure of these author-written labels, not a fresh blind test. One draw, small n and zero human label review preclude generalised reliability or significance claims.

A confirmed HTTP 429 interrupted the original grid. The retry policy was amended **after observing that failure**, only for confirmed rate-limit rejections: maximum three retries, same bytes, Retry-After or 30/60/120 seconds with a 60-second minimum, and at least five seconds between dispatches. No retry for timeout, 5xx, connection failure or malformed/invalid generation. Unknown holds are retained; above USD 0.60 stops. Total/dev/final caps are USD 5/3.50/1.50, unchanged by resumption. Final retained estimate USD 1.7899175 includes USD 0.1460375 unknown hold; known estimates USD 1.64388. Estimates are not billing. Production generation still never retries.

### Hosted comparison for the new reference

Local verification is not hosted certification. The operator pushes the reviewed branch and runs the existing evaluation job without a provider key, checks `make eval-gate` and `make eval-selftest`, and compares request counts (66 entries/68 consumptions), 130 primaries/22 probes, complete coverage and all non-latency metrics with `live-v2.json`. Keep zero tolerances; if hosted numerics differ, preserve logs and investigate before any explicit reviewed rebaseline. Do not modify the existing proof branches to manufacture new proof.

`sentence-overlap-v1` examines the first sent chunk only; splits at punctuation followed by whitespace or newline; picks a <=2,048-character span with greatest unique non-stopword ASCII-token overlap; ties use source position. Zero-overlap spans are allowed. No label/attack filtering; unchanged verifier may reject output. It cannot combine multi-chunk facts and is not an LLM quality measure.

## Canonical results

All three canonical baselines completed at frozen source `532ddea`, each with exactly one logged held-out pass: 130 primary phrasings, zero hard failures. [Results and intervals](evaluation-results.md) show every baseline separately. Correct answered on test: fake 7/46, real deterministic 10/46, informational live 12/46; these denominators include all primary controls, not just answerable questions. Live dispatched 35 requests and settled an operator estimate of USD 0.28712, below the USD 3 cap; zero unknown usage/cost. The conservative pre-run reservation forecast was USD 4.614675, but actual settlements released headroom. No paid retry or warmup. Raw live records stay private; public provider identity is neutral with a digest.

No test false evidence or hard failures occurred, but real test evidence sufficiency is only 6/20, and the live run still missed 14 answerable/rule phrasings on test. Correct safety controls do not imply useful answer coverage. The deterministic baseline answered some abstention-only dev injection challenges incorrectly without echoing attack text; live had one dev false answer. Exact verification rejected live outputs for quotation/schema/echo reasons. These are reported failures of utility/decision quality, not hidden by the zero-hard-failure result.

## Candidate audit findings

OR-based team/ownership access can intentionally cross tiers. Natural abstention improved on dev but remains high. Near-miss evidence can survive relevance gates. First-chunk generation limits multi-source accuracy. Injection verification may reject relevant sources. These are candidate findings, not a completed release audit.
