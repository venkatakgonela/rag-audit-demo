# 0013: Use synthetic data and original project material only

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

The [project rules](../../AGENTS.md) require fabricated, labelled domain data and original work. Only sample local configuration and test sentinels exist today; a corpus generator is planned.

## Decision drivers

Avoid importing confidential source material, make future fixtures reproducible, and keep the demonstration's evidence inspectable. Synthetic data reduces confidentiality risk; it does not eliminate accidental secrets or all privacy/security risks.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| Original synthetic fixtures | Controlled cases, no intentional real-record dependency | Realism and external validity require honest qualification; accepted. |
| Public datasets | Broader naturally occurring variation | Licensing, provenance and personal-data review would still be necessary. |
| De-identified real records | Potential operational realism | Residual disclosure and permission risks inappropriate for this demonstration. |
| Adapt existing project material | Faster initial implementation | Provenance/confidentiality assumptions become harder to audit; write anew instead. |

## Decision

Keep documents, identities and claims fabricated and labelled. Use official documentation as reference, not other projects' private code or records. Never infer production experience from a synthetic demonstration.

## Consequences

No real corpus is needed to run current tests, but labels and original-work requirements remain review obligations, not a complete automated provenance detector. Future synthetic generation must define seeds, case coverage and known realism limits. The project licence is still undecided; do not imply unrestricted reuse permission.

## Revisit when

A separately authorised use case requires external data and can meet provenance, permissions and security review requirements; record a new decision before changing scope.

## Sources

Project policy evidence: [engineering rules](../../AGENTS.md), [synthetic examples](../../.env.example), [test fixtures](../../tests/test_settings.py). This is a risk-management decision, not legal advice or a claim of formally verified confidentiality.
