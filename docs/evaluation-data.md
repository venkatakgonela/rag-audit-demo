# Evaluation data

Implemented data, not an evaluation harness. All 72 documents are original synthetic AI-assisted drafts for Synthetic Lanternfold Mutual, edited and mechanically checked. Independent human label review is pending; all 60 labels are `drafted`, zero human-reviewed. There are no real people, insurer records or externally copied policy passages.

## Inventory

| Family | Total | claims-a | claims-b | Tier |
| --- | ---: | ---: | ---: | --- |
| Policy | 12 | 6 | 6 | public |
| Handling | 12 | 6 | 6 | public |
| FAQ | 12 | 6 | 6 | public |
| Underwriting | 12 | 6 | 6 | internal |
| Broker guide | 8 | 4 | 4 | broker |
| Claim | 16 | 8 | 8 | restricted |

Four fictional products (Hearth, Workshop, Voyage, Orchard), three editions each; policy cases name the edition and rule cases name the unique claim bound to it. General procedures expressly cover all editions. Twelve policy records and sixteen claim records bind their exact mandatory terms/facts to source passages; hashes alone would not establish this consistency. One first-contact walkthrough forces overlapping chunks; short FAQs, numbered clauses, tables, near-duplicate evidence-copy instructions and inert FAQ/claim-note attacks exercise other structures. No gate or retrieval quality is measured here.

## Intended access matrix

Authored intent, not a dump of the product ACL. C-A/B = customer, B-A/B = broker, U-A/B = underwriter, A = admin. `yes` grants visibility. Every document is compared with the SQL ACL for all seven subjects. Claims are owner-only between customers, not owner-only against assigned brokers/staff/admin. **Staff team membership grants every document owned by that team across tiers**, including broker guides and restricted claims. Both underwriters see all internal-tier documents. This broad OR policy is unchanged; whether team ownership should override every tier is a future access-design question.

| Document | Team | Owner | C-A | C-B | B-A | B-B | U-A | U-B | A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic-policy-0 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-1 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-2 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-3 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-4 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-5 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-6 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-7 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-8 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-9 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-10 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-policy-11 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-0 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-1 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-2 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-3 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-4 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-5 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-6 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-7 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-8 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-9 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-10 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-handling-11 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-0 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-1 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-2 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-3 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-4 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-5 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-6 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-7 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-8 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-9 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-10 | claims-a | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-faq-11 | claims-b | none | yes | yes | yes | yes | yes | yes | yes |
| synthetic-underwriting-0 | claims-a | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-1 | claims-b | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-2 | claims-a | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-3 | claims-b | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-4 | claims-a | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-5 | claims-b | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-6 | claims-a | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-7 | claims-b | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-8 | claims-a | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-9 | claims-b | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-10 | claims-a | none | no | no | no | no | yes | yes | yes |
| synthetic-underwriting-11 | claims-b | none | no | no | no | no | yes | yes | yes |
| synthetic-guide-0 | claims-a | none | no | no | yes | yes | yes | no | yes |
| synthetic-guide-1 | claims-b | none | no | no | yes | yes | no | yes | yes |
| synthetic-guide-2 | claims-a | none | no | no | yes | yes | yes | no | yes |
| synthetic-guide-3 | claims-b | none | no | no | yes | yes | no | yes | yes |
| synthetic-guide-4 | claims-a | none | no | no | yes | yes | yes | no | yes |
| synthetic-guide-5 | claims-b | none | no | no | yes | yes | no | yes | yes |
| synthetic-guide-6 | claims-a | none | no | no | yes | yes | yes | no | yes |
| synthetic-guide-7 | claims-b | none | no | no | yes | yes | no | yes | yes |
| synthetic-claim-0 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-1 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |
| synthetic-claim-2 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-3 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |
| synthetic-claim-4 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-5 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |
| synthetic-claim-6 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-7 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |
| synthetic-claim-8 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-9 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |
| synthetic-claim-10 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-11 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |
| synthetic-claim-12 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-13 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |
| synthetic-claim-14 | claims-a | synthetic-customer-a | yes | no | yes | no | yes | no | yes |
| synthetic-claim-15 | claims-b | synthetic-customer-b | no | yes | no | yes | no | yes | yes |

Hidden document counts: customer A/B 28 each; broker A/B 20 each; underwriter A/B 12 each; admin 0. Unauthorised cases target hidden underwriting facts, broker procedures and claims. Restricted sentinel strings remain in protected sources and offline labels, never public guidance or generation prompts.

## Golden schema and split

| Category | Total | Dev | Test |
| --- | ---: | ---: | ---: |
| Single document | 20 | 13 | 7 |
| Multiple documents | 8 | 5 | 3 |
| Unanswerable | 10 | 7 | 3 |
| Unauthorised | 10 | 7 | 3 |
| Rules | 6 | 4 | 2 |
| Authorised injection | 6 | 4 | 2 |

Each case has an information need, two tagged phrasings (keyword/natural), subject, scope, category, challenge kind, source document/section and exact required quote facts, forbidden document/sentinel/profile-chunk references, optional independent rule expectation, rationale, labeller/date/status and fact-group identity. Strict models reject extra fields. There are 120 phrasings, 80 dev and 40 test. All seven subjects occur in both splits. Subject totals are 11/11 customers, 9/9 brokers, 7/7 underwriters and 6 admin. Admin has no artificial unauthorised case.

`acceptable_decisions` is the authoritative outcome list. `expected_decision` retains a single baseline outcome for compatibility, but must not reject an otherwise correct clean answer in an ordinary injection case. `must_not_appear` lists hidden facts or attack phrases forbidden anywhere in a response, matched case-insensitively. `support` supplies required clean quote facts for answered outcomes; unauthorised cases instead use it to anchor the hidden answer. `related_visible` records partial, visible evidence, not an answer. `attack_support` identifies visible attack-bearing evidence separately. `absence_review` records the author's source-search/read rationale for near misses. These fields are offline labels, never model inputs.

| Challenge coverage | Cases | Detail |
| --- | ---: | --- |
| Standard | 34 | 20 single, 8 multi, 6 rules |
| Hidden explicit-ID controls | 4 | Missing-ID counterfactual phrasings retained |
| Hidden free-text traps | 6 | Two customers, two brokers, two underwriters; related visible evidence in each |
| Off-domain controls | 4 | Deliberately absurd questions |
| In-domain near misses | 6 | Unstated allowance, deadline, qualification, weight, validity or acknowledgment limit |
| Instruction-repeat controls | 2 | Deliberately ask to repeat an attack |
| Ordinary injection questions | 4 | Normal questions about claim notes or FAQ markup; clean answered or no-answer allowed |

For free-text traps, the integration counterfactual removes hidden source chunks and repeats the same query: retrieved signals and public response bytes must not change. It is a noninterference test, not a claim that the fake generator answers correctly. Ordinary injection answers must contain the required clean facts and no listed attack phrases; no-answer is also acceptable. Repeat controls have no required clean answer facts.

Rule labels contain two status, two payout and two eligibility cases. The payout examples include a declined claim; arithmetic does not establish settlement. The independent oracle in `tests/data_oracle.py` uses integer pence and dates without importing production rules. Status is taken from the explicitly labelled claim. Cases naming a claim inherit its product/edition; product-specific questions otherwise name both. Multi-document cases require facts from at least two sources; no single document contains all their facts.

## Checks and lifecycle

Run `make test` from the checkout: dataset checks use no Docker, key, network or real-model runtime. They validate schemas, exact facts in named sections, source bindings/hashes, intended visibility, forbidden references/facts, acceptable decisions, challenge counts, unique questions and semantic freeze digests. Mutation tests for forbidden facts and acceptable decisions disable freeze checking so stale digests cannot mask missing validation. Near-miss rationales combine source search and author reading of related visible passages; this is not independent human verification or proof of semantic absence. Integration compares authored intent to SQL across 504 pairs. The separate cached-real ingestion check validates tokenizer-specific references against actual stored chunks; the default unit path recomputes the fake profile only.

`check_response_constraints` enforces offline outcome, forbidden-string and required-quote-fact labels. It is not a harness, semantic leakage detector or replacement for citation/source correctness checks. A paraphrase of a hidden fact can evade literal matching. Production verification remains mandatory.

`datasets/evaluation/freeze.json` is a **candidate awaiting acceptance**, not a claim of review approval. Both paraphrases and shared labelled source facts stay in one split. Semantic question/label changes invalidate the digest; tests never refresh it. After acceptance, any semantic change requires a new digest and CHANGELOG reason. Review-only status is excluded from semantic hashes. No label becomes reviewed until a human returns a decision. Related source documents can span splits for different facts; this is not a source-held-out evaluation.

The label author wrote information needs, then questions, then checked facts without running retrieval to choose successful wording. A private per-phrasing report measures non-stopword token overlap and longest shared sequence against expected sections. Those statistics are descriptive, not pass/fail thresholds and not proof of naturalness. No wording is tuned to achieve a score.

## Limits and safety

Small synthetic sample, same team as implementation, single phrasing author, optimistic bias and no statistical power claim. Independent calculations reduce self-testing but do not replace human judgement. All eligibility examples in this six-case subset are positive; negative and boundary outcomes remain covered by rule unit tests rather than being claimed as balanced golden coverage. Five of the six rule cases are single-claim lookups. Two injection controls explicitly request attack repetition; four use ordinary questions with attack-bearing evidence. A phrase echo does not establish model obedience.

The entire corpus and labels are visible to repository maintainers; this is a procedural held-out split, not a secret benchmark. Labels and sentinels must never enter ingestion or prompts. Data checks are implemented; harness metrics, dev calibration, reranker choice, record/replay and CI quality gates remain Planned. There is no LLM judge. The current lexical evidence gate is unchanged and may still abstain on natural questions even when the corpus supports them.

See [data decision](decisions/0021-versioned-evaluation-data.md), [presentation decision](decisions/0022-answer-outcome-presentation.md), [dataset tests](../tests/test_evaluation_data.py) and [visibility comparison](../tests/integration/test_evaluation_visibility.py).
