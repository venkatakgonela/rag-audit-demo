# 0008: Run a local-only synthetic database with Compose

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

[Compose](../../compose.yaml) provides a PostgreSQL/pgvector container, healthcheck and named volume. [Example credentials](../../.env.example) are explicitly synthetic, disposable and unsuitable for deployment.

## Decision drivers

Avoid modifying a developer's PostgreSQL installation, keep local startup discoverable, and reduce accidental network exposure.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| Docker Compose | Declarative local service lifecycle | Requires Docker; persistent volume state needs care. |
| Testcontainers | Test-owned ephemeral lifecycle | Additional test orchestration when a reusable developer service is also wanted. |
| Local PostgreSQL installation | No container runtime | Host installation/version/extension conflicts and cleanup burden. |

## Decision

Publish `127.0.0.1:5433` by default, initialise the extension from tracked SQL, and retain the named volume on normal shutdown. Port overrides must keep the database URL aligned.

## Consequences

[Tests](../../tests/test_configuration.py) check literal loopback bindings across published mappings without Docker. They do not detect host networking or all alternate exposure mechanisms; localhost also does not stop other local processes. Synthetic passwords are not production authentication. Existing volumes retain credentials/state from their first initialisation.

## Revisit when

Deployment or CI isolation requires a different lifecycle; never turn the local credentials/binding assumptions into a production configuration unchanged.

## Sources

[Compose service and port semantics](https://docs.docker.com/reference/compose-file/services/), [Testcontainers](https://testcontainers-python.readthedocs.io/en/latest/), [PostgreSQL](https://www.postgresql.org/docs/16/intro-whatis.html). Verified October 2, 2026; options assessed retrospectively.
