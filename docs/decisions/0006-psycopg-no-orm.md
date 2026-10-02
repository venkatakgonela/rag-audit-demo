# 0006: Use psycopg 3 without an ORM for connectivity

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

The [database module](../../src/rag_audit/db.py) performs extension initialisation/checking, not persistence for a domain model.

## Decision drivers

Keep SQL explicit and connection cleanup testable without selecting migrations, entity models, pooling or an asynchronous database architecture prematurely.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| psycopg 3 with binary extra | Direct PostgreSQL driver and simple installation | Binary packaging/platform dependency; accepted for this demo. |
| SQLAlchemy | SQL toolkit/ORM with a larger persistence vocabulary | Unneeded modelling layer for two SQL operations today. |
| asyncpg | asyncio-native PostgreSQL driver | Requires an async execution decision not justified by a connectivity command. |
| psycopg2 | Established DB-API driver | Another viable driver but no legacy compatibility requirement here. |

## Decision

Use synchronous psycopg 3 contexts with a bounded connection timeout, shared init SQL, and generic `DatabaseCheckError` raised without displayed exception chaining.

## Consequences

[Tests](../../tests/test_db.py) check success/failure, context exits and rendered traceback secrecy. Connections are opened per operation; no pooling or concurrency benchmark exists. `from None` suppresses normal traceback display, not access to exception internals. Broad sanitisation sacrifices diagnostic detail; no arbitrary query API or ORM is implied.

## Revisit when

Domain persistence, migrations, measured connection overhead or asynchronous workloads justify additional abstractions; keep query-level ACL requirements explicit.

## Sources

[psycopg contexts](https://www.psycopg.org/psycopg3/docs/basic/usage.html), [SQLAlchemy](https://docs.sqlalchemy.org/en/20/intro.html), [asyncpg](https://magicstack.github.io/asyncpg/current/), [psycopg2](https://www.psycopg.org/docs/). Verified October 2, 2026; no driver-performance comparison performed.
