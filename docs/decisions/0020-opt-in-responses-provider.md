# 0020: Opt-in Responses integration and token accounting

Status: Accepted

Recorded October 3, 2026 during implementation. Extends the offline-only integration decision without changing access, extraction, rules or trace-before-release.

## Context

A real OpenAI-compatible Responses endpoint must fit the existing evidence-carrying boundary. Requested aliases may differ from reported names; real usage is tokens rather than synthetic bytes. Incomplete calls can still incur cost.

## Decision drivers

Preserve policy, bound calls before dispatch, reject unknown prices/model substitution, retain valid accounting on rejected output and prevent credential disclosure.

## Options considered

- Responses strict JSON schema: explicit schema and usage; selected with local verification still mandatory.
- Chat completions JSON mode: simpler formatting but weaker schema contract; not selected.
- Tool-call formatting: encodes structure but adds a needless tool-shaped interface; rejected.
- Standard-library worker-thread HTTP versus async httpx: fewer dependencies versus cancellable bounded I/O. Promote the already-locked httpx to runtime without changing version or adding an SDK.
- Retry versus no retries: ambiguous timeouts may have been billed. Select zero transport and verification retries.
- Reject every alias difference versus exact configured mapping: aliases are legitimate but wildcards permit substitution. Select one explicit requested/reported pair, never fallback.

## Decision

[ResponsesProvider](../../src/rag_audit/responses.py) sends strict extractive/rule schemas, reasoning effort, no tools, no streaming and `store=false`. The environment-only key is held in SecretStr and excluded from repr. Redirects/proxy-environment inheritance are disabled; HTTP is loopback-only, otherwise HTTPS. Response bytes are bounded, upstream bodies/exceptions are not logged, and responses containing the literal key are rejected. This does not protect against arbitrary secret transformations or hostile local code.

Real calls require versioned USD/token prices for the exact configured reported model. No private model or real rates are committed. Cost is provider usage times **operator-supplied list prices, not verified billing**; trace `cost_basis` carries provenance. Cached reads/writes are disjoint input subsets; aliases must agree and read+write must not exceed input. Reasoning is an output subset in the observed contract; separate-reasoning arithmetic is independently tested. Unknown counts fail closed. Input above 272,000 tokens is rejected rather than guessing a surcharge.

`responses-utf8-margin-v1` bounds input by actual serialized request UTF-8 bytes plus 1,024. This is a qualified conservative assumption, not a universal tokenizer proof; observed probe ratios were approximately 7.69–13.03 times reported input. Exceeding the bound is a contract error; live validation stops rather than tuning it. Keep 32 KiB full-request and 12 KiB evidence caps. Real defaults: 2,048 total billable output tokens, 60 seconds, USD 0.55 per-call ceiling. The explicitly configured maximum is 4,096 and USD 0.65; not every maximum-size request is affordable. Fake defaults remain unchanged.

Valid usage/cost is recorded before incomplete or invalid output is rejected. The original identical no-answer, quotation, rule allowlist and trace-before-release controls remain unchanged. The adapter is **implemented for opt-in local use only; CI never exercises the real service**. A private validation campaign has a reservation ledger; no public live harness or task-budget ledger is shipped. Missing-price real calls never dispatch; unpriced fake calls remain supported.

## Consequences

The loose bound can reject affordable requests and is not an invoice guarantee. Natural-language questions may abstain at the unchanged keyword gate. Valid quotes do not certify relevance; rejecting an attack quotation does not prove the model followed an instruction. Raw provider response/error text is intentionally unavailable in logs. Production rate limiting, billing reconciliation and evaluation remain Planned.

## Revisit when

A verified tokenizer/framing counter is available, usage schemas change, invoices require reconciliation, or labelled evaluation supports policy changes. Stop on unsupported semantics, never silently infer a new mapping.

## Sources

Official pages read October 3, 2026: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs) for text.format/strict schemas/incomplete handling; [reasoning](https://developers.openai.com/api/docs/guides/reasoning) for reasoning inside max_output_tokens and possible incomplete output before visible text. Gateway alias/cache fields were measured separately, not assumed universal. [Adapter tests](../../tests/test_responses.py), [accounting](../../src/rag_audit/accounting.py) and [orchestration tests](../../tests/test_answering.py) enforce local choices. Prices are operator supplied, not verified by these sources.
