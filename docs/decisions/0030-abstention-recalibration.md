# 0030: Dev-selected recalibration with explicit abstention

Status: Accepted

Recorded: October 3, 2026, after the complete dev grid and before final test results. Supersedes the runtime threshold in ADR 0025; historical evidence remains unchanged.

## Context

The previous live reference correctly answered 5/18 natural single/multi dev phrasings and falsely answered one near miss. Explicit model abstention permits a less restrictive evidence gate without forcing an answer.

## Decision drivers

Selection must use dev only, preserve every safety check and count false answers separately from selected false evidence. No new model, retrieval algorithm, labels or rule changes.

## Options considered

| V1 threshold | Natural correct /18 | Keyword correct /18 | Free-text false answers | Eligible |
| --- | ---: | ---: | ---: | --- |
| 0.75 | 5 | 5 | 0 | Yes |
| 0.70 | 9 | 9 | 0 | Yes |
| 0.65 | 14 | 12 | 1 | No |
| 0.60 | 14 | 14 | 1 | No |

All four completed 84 primary phrasings with zero hard failures, zero operational errors and zero off-domain, ID-style or near-miss false answers. Lower gates improved coverage but failed the predeclared unauthorised free-text eligibility requirement; those results are retained, not excused by noninterference passing.

## Decision

Adopt `local-calibrated-v2`, V1 cosine floor 0.70, with the explicit outcome contract. It is the eligible candidate with most natural correct answers (then keyword, fewer near-miss false answers, stricter threshold). Nine natural correct exceeds the predeclared minimum eight, and zero near-miss false answers does not exceed the prior one. The fake demo remains V0 0.15. Freeze before the single final test exposure; never choose another candidate from test results.

The grid was interrupted by one HTTP 429. An explicitly approved amendment after observing that interruption permits only confirmed 429 retries: at most three, same request bytes, Retry-After or 30/60/120-second backoff with a 60-second minimum, and at least five seconds between dispatches. All other failures stop. Existing samples and failed-attempt holds remain; unknown holds above USD 0.60 stop. Task caps remain USD 5 total, USD 3.50 dev and USD 1.50 final. These are operator estimates, not billing. The retry succeeded; there was no resampling of a successful response.

## Consequences

One live draw and correlated cached samples do not estimate model reliability. Labels are author-written, small and have zero human review. A false answer to hidden-intent free text is a quality failure even if inaccessible rows never affect the request. Final dev reuses samples; test is a second exposure of the historical held-out set, no longer pristine. Hosted verification is not implied.

## Revisit when

Independent labels, repeated preregistered trials, changed model/corpus/prompt, or observed regressions justify a new dev-only study; do not silently retune on the final test.

## Sources

- [Policy](../../src/rag_audit/policy.py), [selection and ledger tests](../../tests/test_abstention_trial.py), [retry tests](../../tests/test_rate_limit.py).
- [Prior decision](0025-calibrated-local-gate.md), [abstention contract](0029-explicit-model-abstention.md), [results](../evaluation-results.md).
