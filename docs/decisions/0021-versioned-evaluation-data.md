# 0021: Versioned synthetic evaluation data

Status: Accepted

Recorded October 3, 2026 during implementation. Dataset acceptance and human label review are separate pending actions.

## Context

Near-identical generated one-liners do not provide a useful basis for measuring retrieval or conversational abstention. Expected answers must be written without using current retrieval success as their oracle.

## Decision drivers

Stable reviewed sources, transparent access intent, independent calculations, reproducible profile-qualified references, offline checks and honest label provenance.

## Options considered

- Larger generated templates: cheap and consistent, but repeated vocabulary makes retrieval unrealistically easy. Rejected as the primary corpus.
- Directly authored static synthetic prose: more work and risk of factual drift, but inspectable varied documents. Selected with structured bindings and review checks.
- Service-generated source drafts: potentially diverse, but adds credential/spend/provenance complexity. Not needed; no model-service generation calls.
- Product rules and ACL as label generators: easy to keep green but circular. Rejected. Author visibility intent separately and calculate rule labels independently.
- Chunk-only labels: direct for retrieval metrics, but tokenizer-dependent and brittle. Use document/section/fact anchors plus an explicit index for each existing tokenizer profile.

## Decision

Track 72 AI-drafted synthetic documents and deterministic metadata outside ignored runtime data. Check source hashes and mandatory structured field bindings before ingestion. The manifest remains format 2; content version is v3. The four products each have three editions, explicitly selected by policy questions or a unique claim reference. General service guidance covers all editions.

Track 60 cases, each with an information need followed by keyword/natural phrasings, 40 dev and 20 test. Freeze candidate semantic digests explicitly; checks never refresh them. Questions sharing the same labelled fact stay in one split. Sources can be shared across distinct facts, so this is not a source-held-out benchmark. Human review starts at zero: all labels are drafted. Review status alone is outside semantic digests; changing a question or expected fact changes the digest and requires a changelog explanation after acceptance.

The independent access table explicitly retains staff team OR semantics: team membership can grant broker guides and restricted claims across tiers. Both underwriters see the internal tier. This is existing policy, not a new permission. Compare all 504 subject/document pairs with SQL. An unauthorised label must target a genuinely hidden document; admin has no such case.

Independent integer-pence/date calculations check rule labels without importing product rules. Exact source checks are not semantic proof. Unanswerable term absence is only a heuristic. Lexical overlap is a descriptive sanity check, not a threshold or wording-tuning target. Do not send labels, hidden IDs or sentinels to the provider. The dataset is not an evaluation harness; calibration, reranking and release gates remain Planned. No judge is used for these extractive labels.

## Consequences

Static data is auditable but authored by the same team as the system, with single-phrasing-author optimism and no statistical power claim. Candidate freeze is not reviewer acceptance. A hand review can correct labels before acceptance; future semantic changes require explicit version history. Installing the package alone does not include repository datasets: export/validation commands are documented for a checkout.

## Revisit when

Human review finds contradictory facts, a new tokenizer requires a reference profile, a larger held-out corpus is available, or access-policy review changes team grants.

## Sources

[Dataset checks](../../tests/test_evaluation_data.py), [independent oracle](../../tests/data_oracle.py), [SQL comparison](../../tests/integration/test_evaluation_visibility.py), [inventory and schema](../evaluation-data.md). These are local design/evidence sources, not claims about an external provider.
