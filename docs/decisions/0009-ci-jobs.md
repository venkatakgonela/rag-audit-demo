# 0009: Separate foundation checks from database integration in CI

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

[Workflow](../../.github/workflows/ci.yml) has `checks` and `integration` jobs. The former runs lint/type/unit checks; the latter uses its own pgvector service and `make db-init` before integration tests.

## Decision drivers

Separate Docker-free feedback from service-dependent failures, and reuse tracked initialisation SQL without assuming Compose mounts exist in hosted services.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| Separate jobs and service container | Clear failure boundaries | Duplicate setup/cache activity; accepted. |
| One job | Less setup duplication | Couples fast checks to service lifecycle and blurs failure attribution. |
| Testcontainers inside tests | Explicit test-owned lifecycle | Adds Python/container orchestration not needed for one service job. |

## Decision

Use Make targets, read-only repository permissions and synthetic service credentials. Share the init SQL with local Compose. Current actions use major tags; stronger supply-chain pinning remains pending.

## Consequences

Both hosted foundation jobs passed for `8e7a2a3` on October 2, 2026 (private repository run; [evidence convention](../README.md#evidence-convention)). This is not proof that future commits pass. Duplicated setup produced a harmless cache-reservation warning; the run also warned of a forthcoming runner-label migration. Neither warning changed a pass into a failure; both are [backlogged](../BACKLOG.md).

## Revisit when

CI hardening decides action/image pins, cache coordination and runner policy, or integration scale makes the split too expensive.

## Sources

[GitHub PostgreSQL services](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers), [setup-uv](https://github.com/astral-sh/setup-uv), [checkout](https://github.com/actions/checkout), [Testcontainers](https://testcontainers-python.readthedocs.io/en/latest/). Behaviour references consulted October 2, 2026; run observations are revision-scoped.
