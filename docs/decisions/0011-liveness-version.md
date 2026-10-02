# 0011: Keep health as liveness and derive the version from metadata

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

The [health endpoint](../../src/rag_audit/api/main.py) returns status and the [installed package version](../../src/rag_audit/__init__.py). There is no production readiness endpoint.

## Decision drivers

Keep process liveness separate from database availability and avoid two version constants drifting apart.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| Liveness and installed metadata | Small deterministic endpoint and one version source | Requires installation; accepted. |
| Health queries database | Exposes dependency readiness | A database outage would make liveness fail; use a separate readiness design if needed. |
| Hardcoded endpoint version | Works from an uninstalled source tree | Duplicates package version state. |
| Rich diagnostic health body | More debugging information | Increases coupling and disclosure surface without present need. |

## Decision

Return only `status` and `version` from `/health`, without opening a database connection. Use `importlib.metadata.version("rag-audit")`.

## Consequences

[Health tests](../../tests/test_health.py) compare metadata and assert no connection call. A healthy response proves neither database readiness nor RAG correctness. Importing without installing the package can fail; documented `make setup` installs it.

## Revisit when

A real deployment needs readiness/startup probes or an explicit offline source-tree execution contract.

## Sources

[Python metadata API](https://docs.python.org/3.12/library/importlib.metadata.html) and linked implementation/tests, consulted October 2, 2026. Liveness/readiness semantics here are the project's declared contract.
