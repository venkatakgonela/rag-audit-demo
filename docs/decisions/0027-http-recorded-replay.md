# 0027: Sanitised HTTP replay and independent model integrity

Status: Accepted

Recorded: October 3, 2026.

## Context

Canonical live evaluation retained 35 raw responses privately. CI cannot reach that provider and must not have a key. Cache-local hashes cannot protect against poisoning that changes metadata too.

## Decision drivers

Exercise the real Responses adapter/verifier, preserve rejected responses, avoid identity/secret disclosure and detect changed request semantics without external dispatch.

## Options considered

- Fake accepted statements bypass parsing, usage and rejection behaviour. Retain fake tests, not as this oracle.
- HTTP-boundary replay exercises those paths without provider availability. Adopt it.
- Cache-local identity hashes are easy but replaceable with the poisoned file. Reject as a CI trust root.
- Publisher-sourced pinned hashes committed separately permit offline verification on every hit. Adopt, retaining review and publisher authenticity as trust boundaries.

## Decision

Reconstruct each original request byte-for-byte against its private digest, require all 35 matches once, replace only the requested model with `local-provider-1`, then compute a versioned canonical JSON hash. Old and neutral hashes are intentionally different. The manifest records source commit, date, count, request hashes and file SHA-256; entries also carry response digests. Keep meaningful text, status and usage; remove message IDs, reasoning payloads and provider identity. Rejected injection text is not repaired.

An `httpx.AsyncBaseTransport` returns responses through the real adapter. Unknown, duplicate or unused fixtures fail the run, including when runtime error handling catches transport exceptions. Python socket/DNS connections and real HTTP transport construction are trapped during replay. The already-open PostgreSQL connection is allowed; this is an in-process guard, not an OS sandbox against malicious native code. Provisioning is separate.

Revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a` has publisher LFS SHA-256 for `onnx/model.onnx`. The publisher API gives Git blob SHA-1 for `tokenizer.json`; verify blob header/content first, then record locally computed SHA-256. Every gate hashes bytes against the committed manifest. Cache metadata alone never suffices. Existing corrupt directories fail without replacement; interrupted provisioning may leave an incomplete directory requiring explicit cleanup/reprovisioning.

`make eval-record` requires opt-in, key, reason, new private output and frozen forecast, outside CI. It reuses the existing capped recording transport/ledger and emits allowlisted candidate fixtures privately. It never promotes automatically: review every retained text and scan identity/secrets before replacement and logged rebaseline. No live recording was run for this increment.

## Consequences

Recorded behaviour is repeatable; new model behaviour is not tested. Prompt/schema/evidence/settings changes require investigation and potentially new recording. Replay estimates use recorded usage/operator prices, not new spend or billing. Hashes detect ordinary edits, not coordinated repository rewrites. Model caches contain public artifacts, not credentials.

## Revisit when

Provider schema/settings, prompts, selected evidence, model/corpus change; poisoned artifact; new recorded baseline. Signed provenance is separate future hardening.

## Sources

- [Replay](../../src/rag_audit/evaluation/replay.py), [model integrity](../../src/rag_audit/evaluation/model_integrity.py), [recorder](../../src/rag_audit/evaluation/record.py).
- [Replay tests](../../tests/test_replay.py), [record guards](../../tests/test_record.py), [manifest](../../datasets/evaluation/model-manifest.json).
- [Publisher pinned file listing](https://huggingface.co/api/models/BAAI/bge-small-en-v1.5/tree/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a?recursive=true).
