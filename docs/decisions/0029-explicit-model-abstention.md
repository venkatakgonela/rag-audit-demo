# 0029: Explicit model abstention and identical-request evaluation

Status: Accepted

Recorded: October 3, 2026. Accepted after the complete predeclared dev grid; final held-out verification is a separate step.

## Context

The extractive model previously had to supply cited statements. The local evidence gate therefore carried all abstention decisions, limiting conversational coverage. A looser evidence gate can select irrelevant but authorised material. Giving the model a way to decline may help quality; it does not replace code-enforced safety.

## Decision drivers

Unchanged access filtering, literal citations, instruction-echo protection, deterministic rules, generic no-answer bytes and accounting. Honest single-draw evaluation with no test-based candidate selection. Finite explicit spend; retry only confirmed rate-limit rejections, never ambiguous generation failures.

## Options considered

- Interpret an empty statements array as refusal: compact but conflates malformed empty answers with a declared outcome.
- Add an explicit outcome enum: makes intent independently validatable and traceable, at the cost of a versioned schema/prompt and stale recordings. Chosen for the trial.
- Rely only on provider structured output: convenient but cannot replace local semantic and safety validation. Rejected.
- Query identical protected pairs twice: samples new model randomness and can create false byte differences. Reuse one sample only after full request-byte equality and independent input construction instead.

## Decision

Trial `outcome: answer` with 1–5 verified statements, or `outcome: insufficient_evidence` with no statements. Both fields are required, extra fields rejected. Existing per-statement checks remain unchanged. The provider receives a strict object schema with outcome enum and bounded statements; local code enforces the conditional length rule independently. Root unions and conditional schemas are not assumed supported. Fixed instructions require directly relevant verbatim evidence or abstention. Rule-wording instructions/schema remain unchanged.

Valid model abstention maps to the existing no-answer envelope and private `model_abstained` trace reason, not verification failure. Usage and cost remain recorded. Invalid combinations continue through existing rejection semantics. Abstention is a quality feature, never an authorisation or injection-security boundary.

Evaluation caches one sampled response per complete request identity across dev candidates. Protected pair members independently build requests; only byte-identical bodies may share the sample. Different hidden-dependent requests never receive identity credit, and existing source/signal/response-byte checks remain enforced. Final replay consumers are bound to case/style/pair-side contexts and exact expected counts; arbitrary repeats, unused entries and over-consumption fail.

Four dev candidates are fixed in advance: V1 at 0.75, 0.70, 0.65 and 0.60. Eligibility requires complete error-free runs, no hard failures, and no off-domain/unauthorised false answers. Selection maximises natural single/multi correct answers, then keyword, then minimises near-miss false answers, then favours stricter threshold. Adoption needs at least three additional natural correct answers and no increase in near-miss false answers relative to the recorded current system. No new test outcome chooses a candidate.

## Consequences

Recorded outputs are one random draw, not a measured success probability. Reusing them correlates candidate results but avoids selective resampling and duplicate spend. Zero human-reviewed labels and small synthetic samples limit generalisation. A failed trial may retain the previous runtime and baseline; no forced adoption or artificial live baseline.

## Revisit when

The dev trial completes, a negative result rejects adoption, labels are reviewed, or the provider/schema/prompt changes. Any adopted reference requires new reviewed fixtures and an explicitly logged gate rebaseline.

## Sources

- [Policy](../../src/rag_audit/policy.py), [answer presentation](../../src/rag_audit/answering.py), [trial](../../src/rag_audit/evaluation/trial.py).
- [Abstention tests](../../tests/test_model_abstention.py), [paired replay tests](../../tests/test_pair_replay.py).
- [Official structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs): consulted October 3, 2026; root object, required fields, additionalProperties and supported schema subset. Local cross-field validation remains authoritative.
