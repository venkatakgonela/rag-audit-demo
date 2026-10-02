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
