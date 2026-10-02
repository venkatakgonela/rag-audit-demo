# 0010: Separate units and integrations, and prove invariants can fail

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

[Unit fixtures](../../tests/conftest.py) isolate settings; integrations require an explicit flag. [Configuration](../../tests/test_configuration.py), [settings](../../tests/test_settings.py), and [database tests](../../tests/test_db.py) pin selected invariants.

## Decision drivers

Fast deterministic feedback, honest service failures, and evidence that assertions detect the regressions they purport to prevent.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| Isolated units plus opt-in integrations | Fast default run and genuine database coverage | Requires separate explicit integration execution; accepted. |
| Database required by default | Every run exercises live setup | Network/Docker availability contaminates basic feedback. |
| Mock-only tests | Simple deterministic execution | Cannot establish real extension connectivity. |
| Happy-path-only assertions | Low test effort | Safety regressions can pass unnoticed; rejected. |

## Decision

Skip integration only when not requested. Explicit runs fail on missing configuration, unreachable database or missing vector. For key invariants, deliberately break the condition, observe failure, restore it and rerun; this is targeted mutation evidence, not exhaustive mutation coverage.

## Consequences

Test outcomes prove only the named cases. Published-port and first-shell-token checks leave documented gaps. The current coverage number is a measurement, not a release threshold or proof of security. [Docs checks](../../tests/test_docs.py) extend this discipline to documentation structure and links.

## Revisit when

Retrieval/provider/evaluation behaviour needs property tests, broader adversarial sets or performance tests; keep offline units independent of paid APIs.

## Sources

[pytest markers](https://docs.pytest.org/en/stable/example/markers.html), [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/), and linked repository tests. Consulted October 2, 2026. Test-strategy alternatives are retrospective assessments.
