# 0005: Typed environment settings with masked secrets

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

[Settings](../../src/rag_audit/settings.py) read environment and optional `.env` data. Database operations need a URL, while health/unit startup do not.

## Decision drivers

Validate timeout bounds, make precedence explicit, and reduce accidental credential disclosure through ordinary representations and rendered errors.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| pydantic-settings and SecretStr | Typed settings and masked representations | Library dependency and careful secret unwrapping; accepted. |
| Plain os.environ | Minimal abstraction | Hand-written coercion, defaults, validation and masking. |
| dynaconf | Broader multi-source configuration | More configuration conventions than this service needs. |
| environs | Environment parsing with a small API | Would require a different validation/masking composition. |

## Decision

Use `SecretStr`, `hide_input_in_errors=True`, environment-over-dotenv precedence, and a bounded timeout. Constructor arguments may override these sources in tests. Fail missing/empty URLs at the database operation boundary, not at health import.

## Consequences

[Tests](../../tests/test_settings.py) cover ordinary representations, JSON, output/log capture, precedence and rendered timeout errors. Masking is not encryption: `get_secret_value()`, custom serializers, structured error input, debugger inspection, or new logging can expose values. This is not a vault or URL-validity/security validator.

## Revisit when

Deployment requires secret rotation, central secret storage, more sources, or stricter database-URL validation; preserve tests for supported disclosure paths.

## Sources

[Settings precedence](https://docs.pydantic.dev/latest/concepts/pydantic_settings/), [SecretStr](https://docs.pydantic.dev/latest/api/types/), [hidden error input](https://docs.pydantic.dev/latest/api/config/), [dynaconf](https://www.dynaconf.com/), [environs](https://github.com/sloria/environs). Verified October 2, 2026; alternatives are retrospective assessment.
