# 0022: Verification abstention and qualified payout wording

Status: Accepted

Recorded October 3, 2026. Additive clarification of decisions 0017–0019; their historical rationale is preserved.

## Context

Authorised evidence may quote an unsafe instruction or yield an invalid quotation. A generic service error is misleading when the application merely cannot release a verified answer. A numerical payout calculation can also be misread as an approved settlement on a declined claim.

## Decision drivers

Preserve access, exact verification, trace-before-release and deterministic arithmetic; improve public outcome semantics without hiding operational distinctions from reviewers.

## Options considered

- Verification failure as HTTP 503: visible to operators but conflates evidence rejection with service failure. Superseded for extractive verification only.
- Distinct public rejection details: helpful for debugging but expands public output and exposes unnecessary evidence-dependent detail. Rejected.
- Existing no-answer envelope with distinct trace reason: selected; future metrics must count verification rejections separately from no evidence.
- Treat declined claims as zero payout: could imply a new eligibility rule and changes the arithmetic. Rejected.
- State calculation-only and claim status alongside the unchanged result: selected. More explicit, without pretending this demo determines settlement.

## Decision

Extractive verification rejection returns the byte-identical standard no-answer envelope and HTTP 200; trace reason remains `verification_failed`. Provider, contract, budget, configuration and trace-storage failures remain infrastructure errors. Existing deterministic rule rephrase fallback remains an answered template with `rule_template_fallback`, not a no-answer. Verification criteria, echo phrases and gate thresholds do not change.

Rule version `synthetic-rules-v2` records the validated claim status in payout inputs and includes it in both code-owned templates with “calculation only”. The separate numeric result and formula are unchanged. A rephrase omitting/changing that qualification falls back to the template.

## Consequences

Clients cannot distinguish weak evidence from rejected generation using the public envelope; operators need traces. A benign attack quotation can still cause abstention. A status-qualified value is still not an eligibility or payment decision. A trace-write failure continues to override any otherwise releasable answer.

## Revisit when

Evaluation justifies better safe explanations, production monitoring needs an explicit operational contract, or the product acquires a separately specified settlement/eligibility workflow.

## Sources

[Presentation tests](../../tests/test_answer_presentation.py), [rule tests](../../tests/test_rules.py), [orchestration](../../src/rag_audit/answering.py), [unchanged verifier](../../src/rag_audit/policy.py).
