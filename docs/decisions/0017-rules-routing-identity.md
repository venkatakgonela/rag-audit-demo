# 0017: Deterministic rules, entity routing and signed fixture identity

Status: Accepted

Recorded October 2, 2026 during implementation.

## Context

Synthetic claims need reproducible status, payout and eligibility answers. A model must not decide outcomes or infer access. Corpus v2 is the only supported format: 50 documents, ten policies and ten claims; regenerate rather than retain v1 compatibility.

## Decision drivers

Authorisation before facts, exact money, explainable routing, offline demonstration and small dependency surface.

## Options considered

- Pure rules and a pattern router: auditable and cheap, but a narrow grammar. Selected.
- Model routing/calculation: more natural phrasing, but ambiguity and unvalidated numerical decisions; rejected for this increment.
- Templates alone versus unrestricted rephrasing: templates are safest but repetitive; optional rephrasing can only select an exact code-owned template, not change numbers, statuses or negation.
- Self-declared role versus signed subject versus production identity service: self-declared roles violate the boundary; a production service needs deployment requirements. Choose a signed local stub and explicitly defer production authentication.

## Decision

[Rules](../../src/rag_audit/rules.py) version `synthetic-rules-v1` computes status; payout `max(0,min(loss-excess,limit))` with Decimal and final 0.01 ROUND_HALF_UP; eligibility requires covered peril and notification delay within the inclusive window. Inputs are decimal strings, nonnegative, at most 999999999.99 GBP with no fractional cents; windows are 0–365 days. No current clock enters eligibility. Results preserve authorised input IDs, inputs, output and corpus version.

[Routing](../../src/rag_audit/routing.py) recognises status, payout/payable, eligibility/eligible, exactly one synthetic claim ID and optionally its matching policy. Ambiguous/multiple operations or entities abstain. Every explicit claim/policy ID is scoped before semantic retrieval, including non-rule questions; missing and invisible both stop without public fallback. Payout and eligibility require both claim and policy ACLs. The [shared SQL predicate](../../src/rag_audit/access.py) serves retrieval and structured lookups; documents remain authoritative for ACLs.

[Authentication](../../src/rag_audit/auth.py) is a subject-only canonical HMAC-SHA256 stub. Role/teams come from the database. HTTP unknown fields, including role, are rejected. Key is environment-backed SecretStr, minimum 32 UTF-8 bytes with no runtime fallback. CLI subject selection is trusted local administration, not authentication.

## Consequences

Predictable outcomes and explicit provenance; phrasing flexibility is deliberately tiny. JSONB facts are validated on ingestion and linked by database keys; the database/operator is trusted. Signed tokens have no expiry, replay defence, revocation list or JWT compatibility. Key rotation invalidates tokens; the committed synthetic sample is not a deployment secret.

## Revisit when

Production identity requirements exist, routing coverage is measured, or a calibrated faithfulness policy permits broader phrasing. Do not loosen ACLs to improve answer rate.

## Sources

Local implementation and [rule tests](../../tests/test_rules.py), [HTTP tests](../../tests/test_answer_http.py), [database tests](../../tests/integration/test_answer_database.py) are the evidence. No external library/version claims or online research underpin this decision.
