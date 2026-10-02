# Patterns and their evidence

Status labels describe this repository, not general pattern maturity. Source links and behaviour qualifications follow the [reading guide](README.md). Planned locations below are conceptual components, not existing files.

| Status / pattern | Problem and location | Failure prevented / intended | Evidence and limitation |
| --- | --- | --- | --- |
| Implemented: fail-closed database configuration | [Database helper](../src/rag_audit/db.py) requires URL at operation boundary | Silent implicit database use | `test_missing_url_fails_without_connecting` in [database tests](../tests/test_db.py); does not make health require a database. |
| Implemented: masked ordinary secret representations | [Settings](../src/rag_audit/settings.py) use SecretStr and hidden rendered error input | Accidental exposure via tested representations/errors | `test_settings_do_not_leak_database_url`, `test_invalid_timeout_hides_input` in [settings tests](../tests/test_settings.py); explicit unwrap/raw error input remains unsafe. |
| Implemented: sanitised exceptions | [Database helper](../src/rag_audit/db.py) suppresses displayed cause chain | Driver messages leaking credentials in normal tracebacks | `test_database_errors_are_sanitised` in [database tests](../tests/test_db.py); exception internals and debug locals are outside guarantee. |
| Implemented: liveness/readiness separation | [Health app](../src/rag_audit/api/main.py) avoids DB | Database outage misrepresented as process death | `test_health_without_database` in [health tests](../tests/test_health.py); no readiness endpoint yet. |
| Implemented: opt-in integrations | [pytest hooks](../tests/conftest.py) and [Make targets](../Makefile) | Default tests require Docker, or requested integration silently skips | [Integration test](../tests/integration/test_database.py), configuration inspection; skip-hook semantics were manually verified, not independently pinned by another hook test. |
| Implemented: shared init SQL | [SQL file](../docker/init/001-enable-vector.sql) consumed by Compose and db-init | Divergent extension initialisation paths | `test_db_init_executes_supplied_sql` in [database tests](../tests/test_db.py) and real integration; cross-consumer path equality currently inspection-backed, not a dedicated automated assertion. |
| Implemented: context-managed connection cleanup | [Database helper](../src/rag_audit/db.py) bounds operation lifetime | Forgotten closes on tested success/failure paths | `test_vector_check_and_connection_cleanup` and query-error case in [database tests](../tests/test_db.py); mocks establish context exits, not resource exhaustion limits. |
| Planned: evidence-carrying answers | Answer policy after generation | Fabricated or unauthorised citations | Planned authorised-set/quotation checks and negative cases; no code yet. |
| Planned: pre-filter access control | Retrieval query over caller-eligible records | Cross-customer evidence contamination | Planned access/leak and query-plan tests; [pgvector caveat](decisions/0004-postgresql-pgvector.md). |
| Planned: deterministic core / LLM shell | Rules return fixed outcomes; model phrases them | Model-invented business outcomes | Planned pure rule tests and checks that output preserves computed results. |
| Planned: ports-and-adapters provider boundary | Separate generation/embedding implementations behind a small contract | Provider coupling and paid-API unit tests | Planned deterministic fake and adapter contract tests; no interface implemented. |
| Planned: golden-set regression gating | Evaluation/CI compare labelled cases and baselines | Releasing known quality/safety regressions | Planned hard leak/citation/rule constraints and calibrated quality thresholds; current foundation CI is not this gate. |

The [threat model](threat-model.md) separates automated evidence from inspection, historical run evidence and planned controls. No row implies total prevention beyond its stated scope.
