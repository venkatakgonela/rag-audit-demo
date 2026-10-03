# Glossary

- **Builder self-assessment:** an assessment performed by the system's author;
  transparent evidence is useful but does not establish independence.
- **Evidence manifest:** pinned source revision and file digests checked before
  report generation; it is not a signature from an independent reviewer.
- **Contextual severity:** impact and likelihood judged for the demonstrated
  deployment, separate from confidence in the supporting evidence.
- **Reported observation:** an attributed account, explicitly distinguished from
  a result verified from a retained hosted log.

- **HTTP replay:** returning recorded response bytes through the real provider adapter without live generation.
- **Fixture staleness:** current requests no longer match the recorded request set exactly.
- **Regression observation:** repeatable read-only comparison, not a calibration or baseline-producing exposure.
- **Gate baseline:** logged reference metrics/configuration for regression; separate from historical evaluation baselines.
- **Trusted model manifest:** committed publisher-derived file identities, independently checked against cache bytes.
- **Provisional tolerance:** measured local allowance awaiting confirmation on the actual hosted CPU.

- **Evidence sufficiency:** at least one selected chunk; not a correct answer guarantee.
- **Anchored tie band:** configurations with minimum false evidence or one more, before quality tie breaks.
- **Counterfactual probe:** repeat an unauthorised request with absent identity or hidden rows removed, without inflating primary denominators.
- **Wilson interval:** descriptive uncertainty interval for a binomial proportion, not a significance or independence guarantee.
- **Reservation ledger:** durable worst-case allocation before dispatch, settled against reported usage while unknown costs remain reserved.

- **Golden case:** a drafted information need with expected source facts and two question phrasings; not a measured model success.
- **Candidate freeze:** explicit semantic digests pending acceptance; tests verify rather than refresh them.
- **Independent access intent:** authored allowed-subject lists compared with the SQL policy, not generated from that policy.
- **Profile-qualified chunk:** a source chunk ID tied to its tokenizer identity; fake and real IDs differ.
- **Verification abstention:** standard no-answer presentation with a distinct verification-failure trace reason. The trace-only `verification_reason` classifies extractive failures as schema, citation, quotation, instruction_echo or duplicate; other paths retain null.

- **Eligible set:** rows authorised inside SQL before either ranking branch.
- **RRF:** reciprocal rank fusion; sums `1/(60+rank)` across available lists here.
- **Source offsets:** zero-based half-open Unicode positions reproducing chunk text.
- **CLS pooling:** selecting the first output token before L2 normalisation.
- **Snapshot ingestion:** atomic replacement of this demo's corpus and identities.

Definitions describe the design vocabulary; they do not imply implementation. Follow [architecture](ARCHITECTURE.md) for status and [technology choices](technology-choices.md) for official references.

| Term | Meaning here |
| --- | --- |
| ACL | Access-control grants for tiers, teams, claim owners and assigned brokers, enforced inside SQL. |
| ADR | Architecture decision record: context, drivers, alternatives, choice, consequences and revisit trigger. |
| ANN | Approximate nearest-neighbour search; may trade retrieval completeness for performance. No ANN index exists here. |
| ASGI / WSGI | Python server/application interface families; this app uses an ASGI stack. |
| BM25 | Keyword relevance-ranking approach contemplated for hybrid retrieval; implementation undecided. |
| Chunk | Bounded source slice with stable identity, section, offsets and access scope. |
| Citation validity | Implemented authorised retrieved-and-sent membership plus exact quotation check; not a full truth test. |
| Deterministic core | Code computes reproducible Decimal outcomes rather than asking a model to decide. |
| Embedding | 384-dimensional representation from the pinned local model or deterministic synthetic fake. |
| Fail closed | Reject protected operations when required identity, evidence, verification or durable trace conditions fail. |
| Faithfulness | Whether an answer is supported by evidence; planned evaluation distinct from citation syntax. |
| Golden set | Planned labelled cases with expected outcomes for regression evaluation. |
| Hybrid retrieval | Exact vector and PostgreSQL full-text ranks combined with reciprocal rank fusion. |
| Liveness / readiness | Process responding versus being able to serve required dependencies/work; health is liveness only. |
| Lockfile | Committed dependency resolutions/hashes; not a lock on all operating-system or container bits. |
| ORM | Object-relational mapper; not currently used. |
| Ports and adapters | Separate generation/embedding contracts; fake and opt-in local Responses generation, fake/local embeddings. |
| Pre-filter ACL | Authorisation restricts candidates inside the query before exact ranking; no ANN index in production schema. |
| Prompt injection | Untrusted instructions influencing model behaviour, including instructions embedded in retrieved documents. |
| RAG | Retrieval-augmented generation: fetch evidence before generation; extractive selection via fake or opt-in local Responses. |
| Reranker | Optional planned second-stage ranking of candidates; not selected. |
| SecretStr | Masking wrapper for ordinary representations; not encryption or permission enforcement. |
| Synthetic data | Fabricated, labelled demonstration material, not real customer records; realism is a limitation. |
| Mutation evidence | Temporarily break an invariant and show a test fails, then restore; not exhaustive correctness proof. |
| Trust boundary | Transition between components/actors with different assumptions about data or authority. |
| Release gate | A check that prevents promotion on failure; current CI checks the foundation, planned gates evaluate RAG safety/quality. |
| Judge calibration | Planned comparison of model judging with human labels to quantify error rather than assume reliability. |
| Extractive answer mode | Statement text equals its exact source quote; only current mode, deliberately not general synthesis. |
| Abstention profile | Versioned per-embedder raw-score gate; current constants are provisional, not calibrated probabilities. |
| Synthetic usage units | Fake-reported UTF-8 bytes; never presented as real vendor tokens. |
| Cache-write tokens | Provider-reported input subset written to cache, priced separately from cache reads; synonymous counters are not added. |
| Reported-model mapping | Exact operator-configured requested alias to expected reported name, not a wildcard or fallback. |
| Token upper bound | Serialized request UTF-8 bytes plus a fixed margin here; qualified conservative assumption, not a universal tokenizer proof. |
| List-price estimate | Provider usage multiplied by dated operator-supplied rates, not a verified invoice or billing guarantee. |
| Trace-before-release | Commit the decision record before returning a response; storage failure replaces it with a generic error. |
| Model abstention | Valid explicit insufficient-evidence outcome, shown as the standard no-answer; quality behaviour, not an access-control boundary. |
| Gate abstention | No answer because the deterministic evidence gate selected no usable context, before model generation. |
| Context-bound replay | A recorded response may be consumed only by declared case/style/pair-side contexts, with exact expected counts. |
| Retained unknown hold | Conservative reservation kept for an attempt whose cost cannot be established; not a claim of billing. |
| Subject-only stub | Signed synthetic identifier; roles/teams are resolved from PostgreSQL, without production expiry/replay protections. |
| p50 / p95 | Median and 95th-percentile measurements, planned for latency reporting; no numbers measured for RAG yet. |
