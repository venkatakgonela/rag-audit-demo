# CPU reranker dev trial — October 3, 2026

**Not adopted:** the anchored selection rule selects V4a at relevance >= 0.95,
but natural evidence sufficiency rises only from 6/18 to 7/18 (+5.56 percentage
points), below the predeclared >=10-point gain (at least 8/18). Keyword sufficiency
rises from 7/18 to 10/18. This measures selection of any evidence, not correct answers.
The non-reranker V1 cosine >=0.75 remains the fallback for subsequent profile adoption;
the runtime default has not yet changed. No test-split evaluation or live calls.

The immutable model/runtime and provenance are in [third-party notices](third-party-notices.md).
The trial used 42 drafted dev cases, two styles each, at commit
`1d6518c89b1d817a9dfe8fa73d9e6c76bdea82ae`. Labels are zero human-reviewed.
All 44 configurations ran on CPU, sequential query/chunk pairs, the same eligible
top-20 retrieval snapshot, unchanged rules/verification. V4a replaces the gate with
relevance >=q; V4b additionally requires cosine >=t (the floor column). No lexical
conjunction or prior 0.75 floor was added. At most five passing chunks enter context.

Selection combines the original 114 configurations with these 44. Eligibility requires
zero off-domain and unauthorised false evidence, hard failures and operational errors.
Within the minimum-to-minimum+1 total-false-evidence band, prefer natural, then keyword
sufficiency, fewer near misses, simpler variant, stricter relevance and cosine floor.
40/44 reranker configurations are eligible, but many have too many near misses for
the selection band. No one-away descriptive-only row exists. All rows have zero hard
failures and operational errors. The selected row has one near miss and zero other
false-evidence counts; lower thresholds' improved sufficiency is not a safe gain.

## Small-sample intervals

Wilson 95% intervals below are descriptive, not significance claims:

- V1 natural: 6/18 (33.33%); 95% interval 16.28%–56.25%.
- V4a natural: 7/18 (38.89%); 95% interval 20.31%–61.38%.
- V1 keyword: 7/18 (38.89%); 95% interval 20.31%–61.38%.
- V4a keyword: 10/18 (55.56%); 95% interval 33.72%–75.44%.

## Resource and invariance checks

- Assets including licence: 91,739,913 bytes (87.49 MiB), below 500 MiB.
- Additional RSS upper bound: 164,986,880 bytes (157.34 MiB), below 1 GiB.
  Measured as process high-water minus current RSS before reranker load; includes
  trial/report allocations, not model-exclusive memory. ARM64 macOS, existing runtime.
- Cold model load 0.103 seconds; first scoring query 0.049 seconds.
- Warm scoring p50 0.0587 seconds, p95 0.0829 seconds (3,607 queries).
  Exactly-20-candidate subset: 3,431 queries, p95 0.0831 seconds, below 2 seconds.
  Timings cover reranking, not end-to-end answering; repeated dev work may warm caches.
- 3,696 primary phrasings and 440 hidden-removal comparisons. Scores and public
  response bytes unchanged under hidden removal; candidate-set audit passes.
- Zero over-512-token unscorable pairs; failure-path unit tests cover this boundary.
- CPUExecutionProvider only; no batching, export, truncation, extra download or package.

## Full fixed grid

Counts combine both styles for false-evidence controls. Each sufficiency denominator
is 18. Floor is unused for V4a. Eligible does not imply selectable or adoptable.

| Variant | q | Floor | Natural | Keyword | Off-domain | Near miss | ID lookup | Free text | Eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V4a | 0.10 | 0.00 | 13/18 | 18/18 | 0 | 8 | 0 | 2 | no |
| V4a | 0.20 | 0.00 | 12/18 | 18/18 | 0 | 8 | 0 | 0 | yes |
| V4a | 0.30 | 0.00 | 12/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4a | 0.40 | 0.00 | 11/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4a | 0.50 | 0.00 | 11/18 | 15/18 | 0 | 7 | 0 | 0 | yes |
| V4a | 0.60 | 0.00 | 10/18 | 15/18 | 0 | 6 | 0 | 0 | yes |
| V4a | 0.70 | 0.00 | 8/18 | 15/18 | 0 | 4 | 0 | 0 | yes |
| V4a | 0.80 | 0.00 | 8/18 | 14/18 | 0 | 4 | 0 | 0 | yes |
| V4a | 0.90 | 0.00 | 7/18 | 12/18 | 0 | 3 | 0 | 0 | yes |
| V4a | 0.95 | 0.00 | 7/18 | 10/18 | 0 | 1 | 0 | 0 | yes |
| V4a | 0.99 | 0.00 | 6/18 | 6/18 | 0 | 1 | 0 | 0 | yes |
| V4b | 0.10 | 0.40 | 13/18 | 18/18 | 0 | 8 | 0 | 2 | no |
| V4b | 0.10 | 0.50 | 13/18 | 18/18 | 0 | 8 | 0 | 2 | no |
| V4b | 0.10 | 0.60 | 13/18 | 18/18 | 0 | 8 | 0 | 2 | no |
| V4b | 0.20 | 0.40 | 12/18 | 18/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.20 | 0.50 | 12/18 | 18/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.20 | 0.60 | 12/18 | 17/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.30 | 0.40 | 12/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.30 | 0.50 | 12/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.30 | 0.60 | 12/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.40 | 0.40 | 11/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.40 | 0.50 | 11/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.40 | 0.60 | 11/18 | 16/18 | 0 | 8 | 0 | 0 | yes |
| V4b | 0.50 | 0.40 | 11/18 | 15/18 | 0 | 7 | 0 | 0 | yes |
| V4b | 0.50 | 0.50 | 11/18 | 15/18 | 0 | 7 | 0 | 0 | yes |
| V4b | 0.50 | 0.60 | 11/18 | 15/18 | 0 | 7 | 0 | 0 | yes |
| V4b | 0.60 | 0.40 | 10/18 | 15/18 | 0 | 6 | 0 | 0 | yes |
| V4b | 0.60 | 0.50 | 10/18 | 15/18 | 0 | 6 | 0 | 0 | yes |
| V4b | 0.60 | 0.60 | 10/18 | 15/18 | 0 | 6 | 0 | 0 | yes |
| V4b | 0.70 | 0.40 | 8/18 | 15/18 | 0 | 4 | 0 | 0 | yes |
| V4b | 0.70 | 0.50 | 8/18 | 15/18 | 0 | 4 | 0 | 0 | yes |
| V4b | 0.70 | 0.60 | 8/18 | 15/18 | 0 | 4 | 0 | 0 | yes |
| V4b | 0.80 | 0.40 | 8/18 | 14/18 | 0 | 4 | 0 | 0 | yes |
| V4b | 0.80 | 0.50 | 8/18 | 14/18 | 0 | 4 | 0 | 0 | yes |
| V4b | 0.80 | 0.60 | 8/18 | 14/18 | 0 | 4 | 0 | 0 | yes |
| V4b | 0.90 | 0.40 | 7/18 | 12/18 | 0 | 3 | 0 | 0 | yes |
| V4b | 0.90 | 0.50 | 7/18 | 12/18 | 0 | 3 | 0 | 0 | yes |
| V4b | 0.90 | 0.60 | 7/18 | 12/18 | 0 | 3 | 0 | 0 | yes |
| V4b | 0.95 | 0.40 | 7/18 | 10/18 | 0 | 1 | 0 | 0 | yes |
| V4b | 0.95 | 0.50 | 7/18 | 10/18 | 0 | 1 | 0 | 0 | yes |
| V4b | 0.95 | 0.60 | 7/18 | 10/18 | 0 | 1 | 0 | 0 | yes |
| V4b | 0.99 | 0.40 | 6/18 | 6/18 | 0 | 1 | 0 | 0 | yes |
| V4b | 0.99 | 0.50 | 6/18 | 6/18 | 0 | 1 | 0 | 0 | yes |
| V4b | 0.99 | 0.60 | 6/18 | 6/18 | 0 | 1 | 0 | 0 | yes |
