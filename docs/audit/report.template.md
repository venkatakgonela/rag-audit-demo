---
title: "Sample AI audit: rag-audit-demo"
author: "Venkata K Gonela"
date: "{{date}}"
---

# 1. Executive summary

**Builder self-assessment. Synthetic data. Not an independent audit.**

System audited: **rag-audit-demo**, source revision `{{commit}}`. This sample report examines a local retrieval-and-answering demonstration, not an operational insurer system. It was built with AI coding assistants under the author's direction; two early commit messages name one of them. The author also assessed the work. **{{review}}**

The evidence consists of frozen synthetic examples, automated controls, recorded model responses, dev-only selection and existing hosted checks. Results describe those runs only; they are not system-wide accuracy or production-readiness claims.

## Five things to know

1. **What held:** the recorded references have no hard-check failures; access filtering, exact quotations and deterministic calculations are code-enforced and tested.
2. **What did not:** answer coverage is modest; related evidence can be irrelevant, valid questions can be rejected, and the final test contains lost successes.
3. **What changed:** explicit refusal plus dev-selected calibration improved the recorded before/after counts without removing the existing checks.
4. **What this does not show:** independent assurance, general injection resistance, future model behaviour, production identity, scalability or billing accuracy.
5. **What next:** review policy semantics and labels, build a new independent adversarial evaluation, and address operational controls before real exposure.

{{severities}}

Finding counts are generated from `docs/audit/findings.json`. Severity is contextual: synthetic data and local use constrain current impact. A mitigated item is not necessarily eliminated; accepted means a documented design boundary, not acceptance of deployment risk.

<div class="page-break"></div>

# 2. Scope and reusable audit checklist

The checklist is reusable; the evidence and conclusions are specific to this revision. Reproduction pointers are repository-relative. Unit checks run without provider credentials; database checks require a disposable database and cached model.

| Control area | Method and evidence | Boundary of conclusion |
| --- | --- | --- |
| Access and existence leakage | Query inspection; `tests/integration/test_retrieval.py` and visibility tests | Query pre-filter and tested hidden/absent pairs, not timing equivalence |
| Grounding and citations | `tests/test_answer_policy.py`; exact quote and authorised-ID checks | Verbatim support, not universal relevance |
| Deterministic rules | `tests/test_rules.py`; independent evaluation oracle | Tested calculations, not advice or settlement decisions |
| Retrieved prompt injection | Echo/benign-control tests; injection labels; F-13 | Structural limits and a phrase heuristic, not broad obedience resistance |
| Refusal and errors | `tests/test_model_abstention.py`, presentation tests | Same public no-answer bytes, private reason retained |
| Evaluation and release gate | Frozen source checks; replay; self-test faults | Recorded behaviour, not a new live sample |
| Labels and data | Frozen digests, source bindings, review-status count | Synthetic and author-written; review does not imply independence |
| Cost and latency | Recorded usage, Decimal estimates, bounds tests | Estimates and cooperative limits, not invoices or load testing |
| Integration security | Repository/history/PR scan; workflow inspection | Scoped inspection, not penetration testing |
| Observability | Trace-before-release and storage-failure tests | Synthetic traces; retention policy not established |
| Operations | Stub identity, exact search and settings inspection | Local demonstration only |

**Not assessed:** a deployed production service, real personal data handling, legal/regulatory compliance, independent red teaming, production identity provider, volumetric attacks, network isolation under attack, disaster recovery, invoice reconciliation or user outcomes. This document is not a security certification.

<div class="page-break"></div>

# 3. System and trust boundaries

The caller submits a bounded question under a signed synthetic subject. Database roles and teams are resolved inside the service. Retrieval pre-filters access before ranking; the answer policy selects evidence within budgets. The model may propose extractive statements or refuse. Code verifies the whole answer and commits a trace before release. Rules compute values without delegating arithmetic to the model.

![Implemented components: local service, authorised retrieval and verification.](figures/components.png)

![Implemented answer sequence, including explicit model abstention.](figures/sequence.png)

Sources: `docs/ARCHITECTURE.md`, audited commit `{{commit}}`; local rendered Mermaid assets. Solid elements are implemented. The provider is opt-in; recorded CI does not contact it. The database, operator and local machine are trusted. Retrieved text remains untrusted data even when authorised. Signed fixture identity is not production authentication. A trace write failure changes the response to a generic error rather than claiming an unrecorded successful answer.

<div class="page-break"></div>

# 4. Recorded safety and remediation results

These are separate references, not independent replicated trials. “Hard” is the harness's tested access/citation/rule/noninterference/echo criteria. Zero observed failures is not proof that failures are impossible. False answers are a separate quality measure.

{{safety}}

## Answerable single/multi phrasings

{{comparison}}

Intervals are Wilson 95%, descriptive rather than significance tests. Natural and keyword wordings of the same case are paired, not independent. The historical test split includes both answerable and negative/rule/injection examples; do not confuse answerable denominators with all primary phrasings.

## Dev-only selection

{{candidates}}

Eligibility excluded off-domain and unauthorised false answers and required complete error-free runs with no hard failures. Ranking used natural correct, keyword correct, fewer near-miss false answers, then stricter threshold. Lower gates were rejected, not adopted for their better coverage. The committed decision records the adoption bar. Final dev reuses candidate samples; test did not select the winner. The previous deterministic grid and rejected reranker experiment are distinct studies, documented in `docs/calibration-dev.md` and `docs/reranker-dev.md`.

<div class="page-break"></div>

# 5. Results that must not be hidden

{{categories}}

For unanswerable, unauthorised and ordinary-injection cases, refusal is the right outcome, shown separately from correct answers; injection allowed outcomes include correct answers or permitted refusals without hard failures. Counts cover all phrasings in each category; “After” is the final reference, not extra trials.

Answers include code-produced rules. Multi-fact coverage remains poor. Both case-058 test phrasings regress because output differs from its quote; unchanged verification rejects it. Failures remain in `docs/evaluation-results.md`.

{{outcomes}}

False evidence means material was selected for a negative case; a subsequent refusal does not erase it. Rejections are not operational errors. More evidence can raise coverage and still be irrelevant. Model abstention is a quality feature, never an access-control or injection-security replacement.

## Cost and latency

{{costs}}

Costs use operator prices, not invoices. Logical calls are not billable dispatch counts. Final dev latency mostly measures cache reuse, not a network speedup. Percentiles describe these runs only. No new model call was made for this report.

<div class="page-break"></div>

# 6. Findings: policy and answer quality

{{findings_a}}

<div class="page-break"></div>

# 7. Findings: assurance and operational boundaries

{{findings_b}}

<div class="page-break"></div>

# 8. Findings: remaining evidence gaps

{{findings_c}}

The frozen corpus includes {{injection_cases}} injection cases. Exact instruction quotations in early live smoke checks were rejected by the echo rule; that observation does not demonstrate instruction obedience or absence of novel attacks. No general-purpose tools are available to the model in this service. The reported native crash is distinct from these security/quality results and has not been diagnosed here.

<div class="page-break"></div>

# 9. Remediation roadmap

Effort sizes are planning judgements: S is a bounded policy/documentation decision, M a scoped engineering/evaluation change, L a coordinated research or deployment programme. They are not measured delivery estimates. Prioritise assurance and deployment prerequisites over cosmetic improvements.

{{roadmap}}

## Positive observations

- Query-scoped access and independent visibility tests catch tested forbidden evidence paths.
- Verified statements must point to authorised retrieved chunks and exact source wording.
- Rules compute values in code, and an independent oracle checks recorded rule outcomes.
- Generic no-answer bytes conceal the internal refusal/rejection reason from the caller.
- Trace-before-release fails closed when storage fails.
- The release gate has passing controls and deliberately faulty variants that fail.

These observations describe implemented controls, not complete prevention. Preserve the controls while testing better answer relevance and broader adversarial behaviour. Do not change labels or thresholds in response to the old test results.

<div class="page-break"></div>

# 10. Regression plan and existing hosted evidence

With a disposable `DATABASE_URL` and verified cached model, run `make eval-gate` and `make eval-selftest`. No provider key is required. The gate checks frozen data/configuration/fixture identity, complete coverage, hard failures and measured quality against the approved reference. It blocks on mismatch rather than hiding drift with a wider tolerance.

{{runs}}

{{selftests}}

{{proof}}

The first two entries are the reviewed remediation/main runs. The deliberate proof runs are expected failures: [PR #7](https://github.com/venkatakgonela/rag-audit-demo/pull/7) lowers the evidence gate; [PR #8](https://github.com/venkatakgonela/rag-audit-demo/pull/8) weakens access filtering. Their recorded job conclusions are shown even if a reader cannot open private links. This report does not modify those branches or infer that all failed jobs were caused by one check.

For future changes: add reviewed examples in a new version, preserve old frozen evidence, calibrate on development data and expose a new test split only under a declared protocol. Follow `docs/evaluation.md` for explicit local recording/rebaseline reasons, changelog marker and chained history. Do not baseline a hard failure or run recording from CI. Owner label-status updates can rebuild this report without changing semantic labels; this task makes no such update.

Monitoring suggestions for a later service: separately track gate refusal, model refusal, verification rejection, errors, denied evidence, unknown cost and trace failures; version the prompt/schema/model; sample real-model behaviour with approval; investigate changes instead of interpreting recorded replay as live monitoring.

<div class="page-break"></div>

# 11. Limits and independence

Cumulative retained estimate: USD {{retained_estimate}}; final phase: USD {{final_spend}}. Source: `live.retained_estimate` and `live.phase_spend.final` in `datasets/evaluation/baselines/live-v2.json` at `{{commit}}`. These are operator estimates, not billing.

This is a builder's self-assessment of synthetic examples, not an independent audit. AI coding assistants were used under the author's direction; two early commit messages name one of them. **{{review}}** An AI reviewer checked all 65 labels against their sources and found no factual, outcome or visibility disagreement and three wording notes ([record](label-review.md)); that is not human review and not independent of the AI-assisted build, and every label remains `drafted`. Owner review does not make the project or its audit independent.

The committed canonical log contains {{exposures}} test-start events, including {{live_exposures}} live references. The split is visible and repeatedly exposed, not a pristine blind benchmark. Final dev reused samples; one successful draw per distinct request is not an estimated success probability. A later separately reported reviewer spot check is not a new canonical baseline or part of an independent sample-size claim.

The score tables describe exact labels and contexts. Correct quotation does not prove relevance, completeness or advice quality. Author-written acceptable-decision labels and synthetic document construction may favour the implementation. Numeric intervals cannot correct that bias. Paired styles and shared cached samples introduce dependence.

Recorded replay tests adapter/pipeline behaviour against earlier outputs, not a current model's changing tendencies. General prompt-injection obedience, real user workflows, production authentication, resource exhaustion, timing channels, native cross-platform stability and broad scaling remain unestablished.

Costs are list-price estimates with a conservative unknown hold, not verified billing. Local and emulated performance is not a service-level objective. Historic metadata can be incomplete; unavailable measurements are not converted to zero. No judgement here claims regulatory compliance, fitness for insurance decisions, production readiness or zero hallucinations.

Private history/metadata exceptions are disclosed in `docs/PUBLISHING.md`: accepted early co-author provenance, known workflow-derived merge/ref identifiers and platform committers. No history was rewritten to polish the record. Publication settings and independent document review remain owner decisions, separate from the test results.

<div class="page-break"></div>

# 12. Rubric, evidence index and reproduction

| Impact / likelihood | Exceptional/unobserved | Plausible | Observed/repeatable |
| --- | --- | --- | --- |
| Minor usability/operational effect | Low | Low | Low |
| Material quality or assurance loss | Low | Medium | Medium |
| Major confidentiality/integrity/availability harm | Medium | High | Critical |

Critical means immediate containment of demonstrated major harm; High means a credible major-impact path; Medium denotes material bounded risk/assurance gaps; Low denotes limited operational/hardening concerns. Informational denotes a property without established adverse impact. No example of a Critical/High outcome is asserted by this rubric. Production exposure to real data could increase impact/likelihood. Confidence is separate: high for directly inspectable/tested evidence, medium for reasoned operational limits, low for sparse or reported observations.

| Evidence | Reproduction / location |
| --- | --- |
| Audited revision and per-file hashes | `docs/audit/evidence-manifest.json`; input digest mismatch fails the build |
| Frozen corpus/labels and canonical runs | `datasets/evaluation/freeze.json`, baseline files and `run-log.jsonl` |
| Historical selection and remediation | `docs/calibration-dev.md`, `docs/reranker-dev.md`, ADR 0030 |
| Current release reference | `datasets/evaluation/baselines/ci-v1.json` and chained baseline log |
| Named findings | `docs/audit/findings.json`; each path exists and every finding has a status and recommendation |
| Existing hosted/observer evidence | `docs/audit/verification-evidence.json`; reported observations are labelled, not replayable evidence |
| Tests | `make lint`, `make typecheck`, `make test`; database/model checks as described in section 10 |
| Report reproduction | `make audit-report`; installed pandoc, Chrome and Poppler; committed local fonts and figures; no network |

**Glossary:** false answer = released answer on a negative case; false evidence = selected context on a negative case; refusal = deliberate no-answer; verification rejection = proposed output violates contract; hard failure = named harness invariant violation; replay = reuse of recorded provider outputs; Wilson interval = descriptive interval for a labelled count; retained hold = unknown-cost reservation, not an invoice.

All report numbers are generated from the cited committed sources. Full table data is `docs/audit/tables.json`. The report is a sample of an audit method, not an endorsement of a production deployment.
