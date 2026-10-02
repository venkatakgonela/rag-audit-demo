# 0003: Use FastAPI for the service boundary

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work. Alternatives were assessed retrospectively, not benchmarked.

## Context

The [implemented app](../../src/rag_audit/api/main.py) currently has only `/health`. Future structured request/response handling is planned, not delivered by choosing a framework.

## Decision drivers

Typed Python interfaces, documented HTTP contracts, and a small testable API boundary without selecting a database ORM.

## Options considered

| Option | Benefit | Cost / why not selected here |
| --- | --- | --- |
| FastAPI | Type-driven validation and OpenAPI support | Pydantic/Starlette coupling; accepted for the intended API. |
| Flask | Small WSGI core and explicit composition | More contract/validation assembly for this design. |
| Django | Broad web application facilities | Full application conventions exceed today's tiny service needs. |
| Litestar | Credible typed ASGI alternative | A different integration surface with no demonstrated advantage for this scope. |

## Decision

Use FastAPI with Uvicorn; keep domain rules out of request handlers when they arrive. Choice of an ASGI framework does not make synchronous database operations asynchronous.

## Consequences

[TestClient tests](../../tests/test_health.py) exercise HTTP responses without a running server. The dependency stack brings upstream compatibility/deprecation work; no throughput claim or production authentication follows from this choice.

## Revisit when

Product needs demand an integrated admin/ORM stack, deployment incompatibility appears, or measured API bottlenecks justify a different boundary.

## Sources

[FastAPI features](https://fastapi.tiangolo.com/features/), [Uvicorn](https://www.uvicorn.org/), [Flask](https://flask.palletsprojects.com/en/stable/), [Django overview](https://www.djangoproject.com/start/overview/), [Litestar](https://docs.litestar.dev/latest/). Verified October 2, 2026; no comparative benchmark performed.
