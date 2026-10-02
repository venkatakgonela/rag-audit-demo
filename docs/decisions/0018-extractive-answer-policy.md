# 0018: Extractive answers, evidence profiles and identical abstention

Status: Accepted

Recorded October 2, 2026 during implementation; profiles frozen before acceptance demonstrations.

## Context

Nearest neighbours are not sufficient evidence. Valid quotations alone do not validate arbitrary paraphrases, and absence must not reveal access restrictions.

## Decision drivers

Exact evidence provenance, no hidden-resource oracle, bounded failure paths and honest limits rather than unmeasured quality claims.

## Options considered

- Extractive-only: statements equal their exact source quote. Selected for auditable mechanics, at the expense of natural synthesis.
- Abstractive answers plus calibrated judge: better synthesis, but requires labelled evaluation not available here. Deferred.
- Retry invalid output versus reject whole generation: retry may rescue formatting but repeats cost/attacks; choose zero retries and no partial repair.
- One embedding threshold versus per-identity profiles: different distributions invalidate a shared floor; choose named versioned provisional profiles.

## Decision

`answer_mode` is an explicit enum, currently only `extractive`. The model mainly selects evidence. Each statement must have exactly text/chunk_id/quote, reference this request's authorised retrieved set **and** actual sent subset, and quote an exact nonempty substring. Text equals quote; no Unicode, whitespace, case or CRLF normalization. Section/offset metadata comes from the snapshot. One bad or duplicate statement rejects everything.

[Profiles](../../src/rag_audit/policy.py): `fake-demo-v1` cosine >= **0.15**; `local-provisional-v1` cosine >= **0.55** for the exact pinned local embedder identity. Both require positive keyword score and a keyword rank, rejecting nonfinite signals. Seven separate observation questions preceded acceptance tests. Three longer local-model questions scored approximately 0.70–0.71 but had zero keyword scores. Short observation queries `compartment schedule` scored 0.555–0.563 and `duplicate-payment` 0.651–0.656 with positive lexical matches. Unrelated astronomy scored approximately 0.46–0.49 without a keyword match. Fake short lexical matches scored approximately 0.16–0.19. These motivate provisional floors, not calibration. The fake profile exists to demonstrate offline paths. Neither is a relevance probability; whole-query lexical matching can reject good natural-language questions. Future calibration remains Planned.

Default evidence budget is **12,288 UTF-8 bytes** and five whole chunks. If a chunk does not fit, skip it, trace `whole_chunk_budget_skip`, and continue ranking; never truncate. Twenty authorised candidates are retrieved before the five-context limit. Further prompt/output caps apply independently.

Absent and inaccessible explicit entities or restricted-only sentinel fixtures return exactly `{"decision":"no_answer","text":"I cannot answer from the available evidence.","statements":[],"rule":null}`. HTTP status is 200 in both cases. General free-text guarantees noninterference from inaccessible rows, not knowledge of the user's hidden intent; timing equality is not claimed. Admin has no forbidden document and is tested missing-versus-missing plus full visibility.

`instruction-echo-v1` is a named configured phrase/delimiter tuple. It rejects matching proposed text, including in-set exact attack quotations. This is a fixture-backed heuristic that overblocks benign discussions quoting attack phrases. Typed JSON evidence, no tools and untrusted-data instructions are defence in depth, not a general injection guarantee.

## Consequences

The envelope contains no existence-dependent identifiers/counts. Verification/provider errors use a separate fixed generic error; no raw output is exposed. Extractive answers may still be irrelevant or misleading without wider context. No faithfulness, real-model injection or quality certification is claimed.

## Revisit when

Labelled data supports profile calibration, false-positive measurement, a faithfulness judge or expanded answer modes. Never lower a floor to rescue a particular demo.

## Sources

[Policy tests](../../tests/test_answer_policy.py), [orchestration tests](../../tests/test_answering.py), [role/noninterference tests](../../tests/integration/test_answer_database.py) and [policy code](../../src/rag_audit/policy.py). Observations used the already-cached local model, without downloads or remote generation.
