# 0001: Record product architecture decisions

Status: Accepted

## Context

This synthetic-data demonstration needs a concise, reviewable record of important design choices. Code and feature documentation explain what exists, but do not consistently capture alternatives and trade-offs.

## Decision

Record significant product architecture decisions as numbered Markdown files in `docs/decisions/`, using the accompanying template. Keep records focused on the product, the alternatives considered, and consequences. Supersede older decisions explicitly rather than silently rewriting their rationale.

## Alternatives

- Rely on commit messages alone: useful history, but difficult to browse as design documentation.
- Put every choice in the architecture overview: simpler initially, but mixes current design with historical reasoning.

## Consequences

The architecture overview stays concise while important decisions remain discoverable. Contributors maintain a small amount of additional documentation. Routine implementation details do not require an ADR.

## Documentation-schema addendum — October 2, 2026

This additive clarification preserves the original accepted decision and rationale. The record was created during foundation work on October 2, 2026.

### Decision drivers

Keep reasoning discoverable, separate current architecture from historical choices, and expose alternatives without turning routine edits into design ceremonies.

### Revisit when

Revisit the format if readers cannot trace decisions to consequences or maintenance becomes disproportionate; supersede the policy rather than silently rewriting accepted decisions.

### Sources

The original [ADR format discussion](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) motivates short context/decision/consequence records. Expanded headings here are a project choice.
