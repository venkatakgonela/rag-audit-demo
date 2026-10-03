# 0024: Isolated source-anchored extractive evaluation

Status: Accepted
Recorded: October 3, 2026, before canonical held-out evaluation.

## Context

Released answers are verbatim evidence or code-owned rules. Selecting evidence, quoting correct facts and protecting inaccessible content are different outcomes. All labels are drafted synthetic examples, zero human-reviewed.

## Decision drivers

Reproducibility, independent hard checks, dev-only tuning, explicit uncertainty and durable held-out exposure accounting.

## Options considered

- Exact source-anchored facts/citations with independent rule oracles: transparent, cheap and deterministic, but brittle to authored wording. Chosen for the extractive contract.
- LLM judge: broader semantic grading, but adds cost, variance and injection risk without resolving label quality. Not chosen.
- Runtime-integrated labels: convenient but risks label leakage. Rejected; evaluation imports runtime, never the reverse.

## Decision

Run the actual pipeline in isolated database schemas. Use a first-chunk sentence-overlap baseline. Separate dev/test labels, verify accepted freeze digests and append a locked/fsynced start record before held-out dispatch. Refuse duplicate configurations without a recorded reason. Check forbidden outputs, exact citations, code-owned rules and unauthorised counterfactuals independently. Report rates with Wilson intervals, paired-case success and missing coverage. One sequential informational live run uses pre-dispatch reservations, no retries and a USD 3 cap; unknown usage retains its reservation. Raw provider output stays private.

## Consequences

No judge dependency. The baseline cannot combine multiple chunks; poor multi-source accuracy must remain visible. Small clustered authored data and test visibility to implementers prevent broad claims. Partial live coverage is non-success, not fabricated abstention. CI gating/replay remains planned.

## Revisit when

Human-reviewed larger data or an abstractive answer contract requires revised metrics and a new frozen protocol.

## Sources

- [Definitions and run instructions](../evaluation.md).
- [Metric/completion tests](../../tests/test_evaluation_completion.py), [safety tests](../../tests/test_evaluation_safety.py), [counterfactual integration](../../tests/integration/test_evaluation_runner.py).
