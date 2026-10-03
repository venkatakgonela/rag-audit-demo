# Label check by an AI reviewer

Date: 2026-10-03. Scope: all 65 golden cases (42 development, 23 held-out test) as committed at the audited revision.

## What this is and is not
An AI reviewer, working in a separate session from the one that drafted the labels, read every case against its source passage and the independently written access table. It is **not a human review and not independent of the AI-assisted build**: it uses the same family of tools as the label authors and may share their blind spots. No label status was changed; every label remains `drafted`, and the report still states that no human has reviewed them. The project owner's own review remains open.

## Method
1. Each case was read as the sheet presents it: the person asking, both wordings, the expected outcome, the required source passage and facts, the visibility of each document to that person, and the author's rationale.
2. Answerable cases: confirmed that the required fact appears in the cited passage, answers the question as worded, and that no other document states a competing value for the same topic (searched the whole corpus for each topic term).
3. Unanswerable and near-miss cases: searched the whole corpus for the missing information (hotel allowance, final review deadline, repairer experience or public-liability cover, crate weight, survey validity, transfer-acknowledgement hours); none exists anywhere, while nearby passages do.
4. Unauthorised cases: confirmed that the hidden fact exists only in a document the person may not see, that a related visible document exists for the free-text cases, and that the stated visibility follows the access table.
5. Rule cases: recomputed the expected status, payout and eligibility values by hand from the structured claim and policy terms (for example claim 2: loss 1100.00 less excess 150.00 is 950.00, below the 3000.00 limit; claim 5 notified 14 days after the incident against a 19-day window, so eligible).
6. Injection cases: confirmed that the clean fact sits in the same chunk as the inert attack text where the case claims it does, and that the acceptable decisions list matches the intent.

## Result
- **65 of 65 cases checked. No factual, outcome or visibility disagreement was found.** The independent rule calculations matched all six rule labels.
- Three **wording notes** (not errors; the held-out wording is frozen, so they are recorded rather than changed): case 057's natural wording says "that message" without an antecedent; case 008's natural wording is clunky; case 016's natural wording paraphrases "floor threshold above the mapped access point" as "entrance height", which is close but not identical.
- Two **design notes**: several test cases share source documents with development cases (different facts or wording, documented); the ordinary-injection cases keep a legacy `expected_decision` of no-answer with an acceptable-decisions list that allows a clean answer, which the metrics already respect.

## What would strengthen this
A human review of at least the 23 test cases by someone other than the label authors, ideally someone not involved in the build. Recording such a review changes only the label status field and the report rebuilds with the new count.
