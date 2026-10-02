# Threat model

All domain data is synthetic. **Implemented** controls are scoped to current code and tests; **Planned** controls have no running RAG system behind them. This is a design review aid, not certification. See [architecture](ARCHITECTURE.md) and [evidence convention](README.md#evidence-convention).

## Assets, actors and boundaries

**Implemented assets:** local database configuration, synthetic credentials/fixtures, source/lockfile, and build/test integrity. **Planned assets:** caller-scoped synthetic documents/claims, embeddings, rule outcomes, generated answers, evaluation evidence, traces and model-spend budgets.

**Implemented actors:** developer/operator, repository contributors and CI dependencies. **Planned actors:** customer, broker, underwriter, administrator, malicious questioner/document author, and external generation provider. No role authentication is implemented.

**Implemented trust boundaries:** environment/dotenv to settings; host process to local database; repository to CI runner/service/dependency downloads. **Planned boundaries:** caller identity to retrieval authorisation, untrusted documents to model context, model output to validated answer, provider usage to cost records.

## Threats, controls and test evidence

OWASP references below use the [2025 LLM Top 10](https://genai.owasp.org/llm-top-10/) consulted October 2, 2026. Mapping indicates relevance, not demonstrated compliance.

| Status / threat | Mitigation or design requirement | Enforced by test | Residual risk / reference |
| --- | --- | --- | --- |
| Implemented: secret leakage through ordinary settings representations (LLM02 relevance for future service) | SecretStr and hidden rendered validation input | [settings tests](../tests/test_settings.py): `test_settings_do_not_leak_database_url`, `test_invalid_timeout_hides_input` | Raw validation inputs, custom serializers, explicit unwrap, debug locals and new log paths remain unsafe. |
| Implemented: driver failure disclosure | Generic error plus displayed-chain suppression | [database tests](../tests/test_db.py): `test_database_errors_are_sanitised`, `test_db_init_failure_is_sanitised` | Exception object internals are not erased; less diagnostic detail is deliberate. |
| Implemented: missing configuration uses unintended DB | Reject missing/empty URL before connecting | [database tests](../tests/test_db.py): `test_missing_url_fails_without_connecting` | Supplied URLs are operator-controlled; not a URL allowlist or production access policy. |
| Implemented: accidental broad published-port binding | Literal 127.0.0.1 host in all current Compose mappings | [configuration tests](../tests/test_configuration.py): `test_compose_published_ports_are_loopback_only` | Host networking/alternate publishing bypass not covered; local processes still reach the port. [Backlog](BACKLOG.md). |
| Implemented: confusing liveness with readiness | Health never calls database | [health tests](../tests/test_health.py): `test_health_without_database` | No production readiness/security check follows from a 200 response. |
| Implemented: CI command convention drifts | Each current run step starts with exact `make` token | [configuration tests](../tests/test_configuration.py): `test_ci_run_steps_begin_with_make` | Chained/piped commands and substitutions can bypass intent; hardening planned. |
| Implemented: documentation loses structural evidence | Index, heading, link, dependency and diagram-fence checks | [documentation tests](../tests/test_docs.py) | Cannot prove prose truth, source freshness or diagram semantics; rendering is separately validated. |
| Implemented baseline / planned hardening: supply chain (LLM03 relevance) | Locked Python artifacts; read-only workflow permission; selected major-tag actions | Not fully enforced by a security test; [workflow](../.github/workflows/ci.yml) and [lockfile](../uv.lock) inspected | Mutable actions/images and compromised dependencies remain risks. Foundation hosted CI verified for `8e7a2a3` (private run), not a security proof. |
| Implemented: access-control bypass | SQL eligible set, trusted fixture roles, restricted claims, no external staff membership | [Role tests](../tests/integration/test_retrieval.py), [metadata tests](../tests/test_retrieval_core.py) | Local operator/database trusted; not production authentication. |
| Implemented: output existence leakage | Inaccessible rows cannot affect visible results, scores or returned ID sets | [Noninterference test](../tests/integration/test_retrieval.py) | No constant-time guarantee; semantic abstention remains planned. |
| Planned: document prompt injection (LLM01 Prompt Injection) | Treat evidence as untrusted data; constrained answer policy and deterministic rules | Planned | Delimiters alone are not a security guarantee; indirect injection cases needed. |
| Planned: fabricated citation or outcome (LLM09 Misinformation; LLM05 Improper Output Handling) | Check cited IDs/quotes against authorised evidence and preserve code-computed results | Planned | Valid quotes need not entail a correct answer; faithfulness requires calibrated evaluation. |
| Planned: cost/usage abuse (LLM10 Unbounded Consumption) | Usage accounting, bounded requests/context and budget policy to be designed | Planned | Current timeout bounds database connection setup only, not model spend or query execution time. |
| Planned: corpus contamination (LLM04 Data and Model Poisoning) | Synthetic labelled corpus provenance and adversarial cases | Planned | Synthetic-only policy is review-backed today; no automated confidentiality/provenance detector. |

## Assumptions and limits

The machine/operator and repository reviewers are trusted; synthetic passwords are not deployment secrets. Fixture retrieval security is implemented; production identity, rate limiting and model-output validation are not. Model artifacts are revision-pinned with local hash verification, but initial HTTPS downloads trust the publisher and cache metadata is not signed. [Adapter smoke tests](../tests/test_embedding_adapter.py) cover shape, offsets and query prefixes, not complete supply-chain defence. The [backlog](BACKLOG.md) records unresolved work.
