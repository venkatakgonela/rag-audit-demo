# Why it matters: risk, governance and framework mapping

This note explains the problems the project is built to catch, and which governance frameworks the same practices belong to. It is a mapping by the author for orientation. It is **not** a compliance assessment, a certification or legal advice; article and clause references should be checked against the current texts before they are quoted. Everything the project demonstrates uses synthetic data.

## What goes wrong without these controls

These are illustrations of failure modes, not reports of real incidents.

| Without this control | What can happen in a governance, risk and compliance (GRC) setting | What the project does about it |
| --- | --- | --- |
| Access is filtered after retrieval, or only in the prompt | A broker's question surfaces a restricted claim file or another customer's record in an answer. Personal data is disclosed to someone with no right to it, which is a data-protection incident and an access-control finding. | Authorised documents are selected inside the retrieval query, before ranking; integration tests probe hidden content for different roles. |
| Answers are not tied to a source | A reply to a customer cites a policy clause that does not exist or was withdrawn. The firm cannot show where the statement came from, so it cannot defend or correct it. | Every statement must carry an exact quote from authorised evidence; the service verifies the quote and refuses when no evidence exists. |
| Amounts or eligibility are produced by the model | A payout, premium or limit is stated differently on two runs, or is plausible but wrong. Controls over financial calculations are not demonstrable. | Rules run in ordinary code and are tested; the model never calculates. |
| No release gate, or a gate that cannot fail | A prompt or model change quietly lowers answer quality or reintroduces a leak. Nobody notices until a complaint or an audit, and there is no evidence of change control. | Fixed questions replay on every change; hard safety failures and measured regressions stop the build; the gate's own self-test and two deliberately failing changes prove it can fail. |
| No traces | After an incident nobody can reconstruct what was asked, by whom, with what evidence. | Each request stores its question, role, passages, answer and checks. |
| Reporting only the good news | Reviewers and clients cannot judge the result, and over-claiming becomes its own risk. | The report states the limits, small samples, the regressions and that labels are not yet human-reviewed. |

## Framework mapping (indicative)

| Framework | Practice in this project | Area it supports |
| --- | --- | --- |
| **NIST AI Risk Management Framework 1.0** | Fixed evaluation sets, hard checks, recorded baselines, reported limits | Measure (testing, validity and reliability) and Manage (risk response); roles and accountability support Govern |
| **ISO/IEC 42001** (AI management system) | Evaluation baseline, traces, change gate, documented findings | Clause 9 performance evaluation (monitoring, measurement, analysis) and risk and operational controls |
| **OWASP Top 10 for LLM Applications (2025)** | Query-level access control, quote verification, small prompt-injection fixture set | LLM01 prompt injection, LLM02 sensitive information disclosure, LLM09 misinformation |
| **ISO/IEC 27001:2022** | Access decided in code and data layer, logging | Annex A access control and logging controls |
| **SOC 2 Trust Services Criteria** | Access enforcement, monitoring, gated change | Logical access, monitoring and change management criteria |
| **UK GDPR** | Documents selected by entitlement, retained questions noted as a limit | Data protection by design, data minimisation, security of processing |
| **EU AI Act** (if a use is classed high-risk) | Accuracy testing, record-keeping, abstention and human review | Obligations on risk management, record-keeping, human oversight, accuracy and robustness |
| **Financial-services model risk expectations** (for example the PRA's SS1/23 for UK banks) | Independent-style testing, documented limitations, change control | Model validation and ongoing monitoring principles |

## What this does not show

It does not show regulatory compliance, a production deployment, resistance to a determined attacker, or accuracy on real data. The evaluation sets are small and author-labelled. Treat it as evidence that a team can design, test and report on these controls, not as a certificate that a given system meets any framework.
