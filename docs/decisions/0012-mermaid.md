# 0012: Use Mermaid for architecture diagrams

Status: Accepted

Recorded on October 2, 2026 as a new documentation-baseline decision, not a retrospective claim about the earlier foundation.

## Context

The [architecture](../ARCHITECTURE.md) needs context, containers, components, sequence, conceptual data model and deployment views with clear implementation status.

## Decision drivers

Keep diagrams near their explanation, review changes as text, and avoid binary drawing files as the sole source of truth.

## Options considered

| Option | Benefit | Cost / why not selected |
| --- | --- | --- |
| Mermaid in Markdown | Text source with flow, sequence and ER notation | Automatic layout and renderer-version variation; accepted. |
| draw.io | Detailed visual editing and layout control | Separate diagram source/editing workflow. |
| PlantUML | Text-based UML vocabulary | Different rendering toolchain for this Markdown-focused baseline. |
| Structurizr | Shared C4 model behind multiple views | More modelling machinery than six small views require now. |

## Decision

Use Mermaid fences with captions, legends and explicit Implemented/Planned labels. Dashed flowchart styling reinforces status but never carries it alone. Keep conceptual schemas labelled planned.

## Consequences

[Unit checks](../../tests/test_docs.py) detect missing/empty fences and required diagram captions, not all Mermaid grammar or visual problems. Validate rendering separately; host renderers can differ from the pinned local CLI. No generated image is the authoritative architecture source.

## Revisit when

Layouts become unreadable, a reusable cross-view model is needed, or published rendering differs materially from validated output.

## Sources

[Mermaid](https://mermaid.js.org/intro/), [flowcharts](https://mermaid.js.org/syntax/flowchart.html), [sequences](https://mermaid.js.org/syntax/sequenceDiagram.html), [ER](https://mermaid.js.org/syntax/entityRelationshipDiagram.html), [official CLI](https://github.com/mermaid-js/mermaid-cli), [draw.io](https://www.drawio.com/), [PlantUML](https://plantuml.com/), [Structurizr](https://docs.structurizr.com/). Consulted October 2, 2026.
