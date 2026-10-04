# Reuse, maturity and how this can help other projects

## Stage
This is a **v0.1 reference implementation and worked example**, built on synthetic insurance-style data. It is not a library, a package or a service. There is no stable API, no versioned interface for reuse and no production deployment. It shows how the controls fit together and how to evidence them; it is not a drop-in component. Results come from small author-labelled sets and are not accuracy claims (see the [limits in the README](../README.md#limits) and [evaluation method](evaluation.md)).

## What transfers to another project
| Piece | Where | How reusable |
| --- | --- | --- |
| **Pattern: access decided inside the retrieval query** | [`access.py`](../src/rag_audit/access.py), [`retrieval.py`](../src/rag_audit/retrieval.py), [integration tests](../tests/integration/test_retrieval.py) | The pattern and the hidden-content test approach transfer directly. The SQL grant rules (tiers, teams, claim ownership, broker relationships) are specific to this demo and must be rewritten for your permission model. |
| **Quote and citation verification, abstention** | [`policy.py`](../src/rag_audit/policy.py), [tests](../tests/test_answer_policy.py) | Largely generic: schema, citation, exact-quote and duplicate checks apply to any retrieval system. The instruction-echo phrase list is a small fixture to extend for your threat model. |
| **Rules computed in code** | [`rules.py`](../src/rag_audit/rules.py) | Pattern only. The payout and status rules are domain-specific. |
| **Record-and-replay evaluation, hard checks, regression gate and its self-test** | [`evaluation/`](../src/rag_audit/evaluation/), [`gate.py`](../src/rag_audit/gate.py), [evaluation method](evaluation.md), [release gate](release-gate.md) | The most reusable part conceptually: recorded model responses, hard safety checks, baseline comparison and a gate shown to fail on purpose. Today it is coupled to this repository's dataset schema and oracle, so adopting it means adapting those, not importing a module. |
| **Audit report pipeline** | [`scripts/audit_evidence.py`](../scripts/audit_evidence.py), [sample report](audit/report.md) | Reusable as a template for a severity-rated, evidence-linked report with reproduction steps; the content is specific to this demo. |
| **Governance mapping** | [governance note](governance.md) | Reusable as a starting checklist; verify clause and article references for your context. |

## What does not transfer
The synthetic corpus and generator, the evaluation datasets and labels, the rules oracle, the identity stub, and every number in the results. Re-baseline from scratch on your own data and have your own people label the cases.

## Adapting it to another project (typical order)
1. Write your permission model and the hidden-content tests first; decide the grant rules as SQL or equivalent in the retrieval query.
2. Define the claims your answers must support and keep arithmetic and eligibility in code.
3. Collect 20 to 40 real or realistic questions with expected outcomes; label them with a subject-matter reviewer.
4. Record model responses, set hard checks (safety, integrity, coverage) and a baseline, then add the gate to CI with a deliberate-failure self-test.
5. Write the audit report from the evidence, including what did not improve.

## How I can help
Assessment of an existing assistant against these controls with a written, severity-rated report; building the evaluation gate into your CI; or adapting individual patterns to your stack. Scope, access and an honest statement of what cannot be assessed are agreed first. Start with a GitHub issue on this repository or the profile linked from it.

## Further reading
The design decisions are written up in [Who is allowed to see the evidence?](https://venkatakgonela.substack.com/p/who-is-allowed-to-see-the-evidence) (access control inside the retrieval query and its limits).
