# 0019: Offline generation contract and trace-before-release

Status: Accepted

Recorded October 2, 2026 during implementation.

## Context

Answer decisions need durable evidence and honest nullable costs before a real provider is added.

## Decision drivers

Offline tests, provider neutrality, bounded calls, no invented usage, authorised provenance and fail-closed trace persistence.

## Options considered

- SDK-specific result objects versus small provider-neutral dataclasses: SDK objects reduce adaptation code but couple policy to a vendor. Select dataclasses separate from embeddings.
- Background traces versus synchronous durable commit: background logging is faster but may lose accepted answers. Choose commit before release; trace outage discards the tentative response.
- Guess unknown prices versus nullable estimates: guesses look complete but mislead. Choose null for unknown prices/usage.
- Token estimates versus explicit byte bounds: byte units are reproducible for the fake, not vendor tokens. Choose explicitly synthetic UTF-8 usage and defer real counters.

## Decision

[Generation](../../src/rag_audit/generation.py) accepts system text, data-only question/evidence, schema, mode, limits and deadline. Result carries payload, provider/model identity, finish state and nullable input/output/cached/reasoning usage. Only offline fake execution is allowed now. A future **OpenAI-compatible Responses endpoint, configured by base URL, key variable and model name**, is Planned; no real adapter exists.

Default caps: 4,000 question characters, 16 KiB HTTP body, 12 KiB evidence, 32 KiB entire serialized prompt, five chunks, 512 synthetic UTF-8 output units, 16 KiB serialized output, five statements of at most 2,048 characters, ten-second cooperative asynchronous deadline, zero retries and USD 0.01 known-price ceiling. Output-unit and byte ceilings are independent; the stricter 512 bound governs the fake by default. Request-body limits are checked while streaming before JSON parsing. They do not cap upstream server buffering, database work or hostile blocking Python provider code.

[Accounting](../../src/rag_audit/accounting.py) uses versioned Decimal rates per million explicitly named units. Cached input is subtracted when it is a subset; reasoning already inside output is not charged twice. Missing required rates/usage yield null. Preflight conservatively bounds synthetic spend with maximum input/output category rates; reported anomalies are recorded then rejected, but spent cost cannot be undone. No default price table invents vendor prices. Only fake unpriced requests are permitted. A real provider requires a separate explicit policy and verified counter/bound.

[Store](../../src/rag_audit/store.py) obtains shared corpus and table locks while resolving identity, structured facts and evidence, then releases them before generation. Snapshot provenance survives later corpus changes. Answering requires an idle dedicated connection, avoiding accidental outer transactions. Trace insertion is its own committed transaction with unique request ID and no corpus foreign keys; ingestion preserves traces. Traces contain authorised retrieved/sent/cited IDs, own bounded question, rules, signals, stage durations, config/profile versions, identities, usage and nullable cost. Rejected payloads, invalid citation IDs and raw exceptions are never logged. IDs supplied by a caller in their own question are not an existence finding. Caller questions are for synthetic use only, not a general secret-scrubbing service.

Every writable decision path attempts one trace. If tracing fails, return the fixed generic error (HTTP 503), never an answer. Durable logging is impossible during a database outage; no durability claim is made then. Minimal authentication/validation traces omit token/body contents. Determinism comparisons exclude IDs, timestamps and measured durations; tests inject clocks.

## Consequences

More database availability dependence and no graceful untraced answering. The contract is ready for an adapter but only fake behaviour is tested; no paid API, production rate limiting, real-token accounting, real-service validation or evaluation gate exists. Synchronous local snapshot I/O in the minimal API is not a high-throughput production design.

## Revisit when

A real provider is approved, token/price semantics can be verified, production traffic needs background/offloaded I/O, or retention/access policies for traces are defined.

## Sources

[Orchestration and cost tests](../../tests/test_answering.py), [HTTP tests](../../tests/test_answer_http.py), [database durability/snapshot tests](../../tests/integration/test_answer_database.py). Decisions use local test evidence, not external performance claims.
