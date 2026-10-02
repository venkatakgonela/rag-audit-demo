# 0007: Use Make as the developer and CI command interface

Status: Accepted

Recorded retrospectively on October 2, 2026; the decision was made during the foundation work.

## Context

The [Makefile](../../Makefile) exposes setup, lifecycle, lint/format, typing, tests, initialisation and API execution. [CI](../../.github/workflows/ci.yml) calls its targets.

## Decision drivers

Make local reproduction of CI commands straightforward and avoid a second set of hidden shell steps.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| Make | Visible named recipes shared with CI | Make/shell availability and syntax quirks; accepted. |
| just | Dedicated command recipes | Another executable/convention without a current need. |
| Task | Declarative task configuration | Another runtime/configuration dependency. |
| nox | Python-defined isolated automation sessions | More environment machinery than the single pinned environment requires. |
| Ad-hoc scripts | Flexible implementation | Discovery and CI/local drift would need separate discipline. |

## Decision

Keep shell `run` steps expressed as Make targets. Action setup remains `uses` steps, not shell recipes.

## Consequences

The [configuration test](../../tests/test_configuration.py) checks the first token is exactly `make`, not every subsequent shell operation or target existence. Chaining/piping is a known gap recorded in the [backlog](../BACKLOG.md); this is a command convention, not a sandbox.

## Revisit when

Cross-platform portability or environment-matrix complexity outweighs the benefits of a small common interface.

## Sources

[GNU Make](https://www.gnu.org/software/make/manual/make.html), [just](https://just.systems/man/en/), [Task](https://taskfile.dev/docs/), [nox](https://nox.thea.codes/en/stable/). Verified October 2, 2026; alternatives assessed retrospectively.
