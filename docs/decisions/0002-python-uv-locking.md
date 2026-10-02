# 0002: Pin Python 3.12 and manage dependencies with uv

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work. Alternatives below are retrospective analysis, not a claim of historical benchmarking.

## Context

Implemented configuration: [Python pin](../../.python-version), [project metadata](../../pyproject.toml), [lockfile](../../uv.lock), and [Makefile](../../Makefile). A small service needs the same Python minor version and dependency resolutions locally and in CI.

## Decision drivers

Limit environmental variation, keep setup teachable, and avoid introducing separate tools for resolution and environment execution.

## Options considered

| Option | Benefit | Cost / why not selected here |
| --- | --- | --- |
| uv with committed lock | One workflow for syncing and running | Tool-specific lock and reliance on uv; accepted. |
| Poetry | Integrated packaging/dependency workflow | Another equally viable convention; no demonstrated requirement justifies changing the existing uv interface. |
| pip-tools plus venv | Explicit requirements workflow and familiar pip tools | More separate setup/sync commands for this small project. |
| Python 3.13 | Access to newer interpreter features | Expands compatibility work without a current feature requirement; not claimed incompatible. |

## Decision

Use Python `>=3.12,<3.13`, `.python-version` 3.12, and frozen uv commands. Exact patch versions still depend on available Python builds. No assertion that 3.12 is faster or safer than 3.13.

## Consequences

The committed lock constrains package resolution, not OS/container contents. `--frozen` uses the existing lock without checking metadata freshness; changes to dependencies must deliberately refresh/review the lock. A single Python minor reduces coverage of other environments.

## Revisit when

Interpreter support policy, required libraries, or deployment constraints demand another minor; test it before changing the pin.

## Sources

[uv sync semantics](https://docs.astral.sh/uv/concepts/projects/sync/), [Poetry](https://python-poetry.org/docs/), [pip-tools](https://pip-tools.readthedocs.io/en/stable/), [Python 3.13 changes](https://docs.python.org/3.13/whatsnew/3.13.html). Verified October 2, 2026; relative suitability is project judgement.
