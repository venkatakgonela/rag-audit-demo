# Third-party notices

The repository's original code and synthetic content are MIT licensed; dependencies
retain their own terms. This is not a declaration that every dependency is
permissive. Retain attribution and review redistribution obligations.

## Locked Python inventory

Generated from `uv.lock` and exact-version distribution METADATA, refreshed on
October 4, 2026: {{count}} external packages, including transitive, optional and development
packages. Conditional colorama and tzdata metadata/licence texts were retrieved
from their publishers without installation. Updated mypy and ast-serialize
metadata and licence texts come from their exact locked installed distributions.

{{inventory}}

Machine-readable provenance: [inventory](dependency-inventory.json),
[verbatim notices](dependency-licences.json) and [readable licence texts](licence-texts.md).
`python -m scripts.audit_notices --check --installed` checks lock coverage, the
recorded licence files and available exact installed versions. It fails if
metadata is missing except for the two explicitly publisher-verified conditional
packages. It does not claim every upstream binary on every platform was inspected.

**Copyleft / mixed terms:** psycopg and psycopg-binary are LGPL-3.0-only;
certifi and pathspec are MPL-2.0; tqdm has MPL/MIT terms. NumPy distributions
contain multiple component licences. Shipping a combined binary distribution
needs a platform-specific review, including bundled native libraries. These
packages are not relicensed by this project's MIT licence. Package source links
and their licence texts identify applicable source/notice obligations. Even
permissive packages require preserving notices.

## Models (not redistributed)

- Embeddings: `BAAI/bge-small-en-v1.5`, MIT, revision
  `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`. The user downloads weights explicitly;
  [trusted model manifest](../../datasets/evaluation/model-manifest.json) pins bytes.
  [Publisher card](https://huggingface.co/BAAI/bge-small-en-v1.5/blob/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a/README.md).
- Rejected CPU reranker trial: `cross-encoder/ms-marco-MiniLM-L6-v2`,
  revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`. Its retained publisher card
  declares Apache-2.0; that revision has no standalone licence file. The standard
  Apache text was retained in the ignored local trial cache. Not adopted, not
  shipped. [Pinned card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2/blob/233902d25c440f23af6f7d6e94d2946bac0bee0a/README.md).

## Report assets and external build/runtime tools

Noto Sans 2.015 upright (regular/bold) and italic are distributed under SIL OFL
1.1. [Font licence](assets/fonts/OFL.txt) and [source hashes](assets/fonts/provenance.json)
are retained. Do not sell the font alone; retain its notice and follow reserved
name rules when modifying it. Original diagrams and synthetic data are project
content, not real persons or organisations.

These tools are used externally, not bundled or locked Python packages:

| Tool | Verified local version / reference | Licence / source |
| --- | --- | --- |
| Python | 3.12 runtime | PSF; [publisher](https://www.python.org/psf/license/) |
| uv | 0.11.3 | MIT or Apache-2.0; [publisher](https://github.com/astral-sh/uv) |
| hatchling | build requirement >=1.27,<2, not lock-pinned | MIT; [publisher](https://github.com/pypa/hatch) |
| pandoc | 3.10 | GPL-2.0-or-later; [publisher](https://pandoc.org) |
| Google Chrome | 154.0.8037.97 | Proprietary browser terms plus open-source notices; [terms](https://www.google.com/chrome/terms/) |
| Mermaid CLI | 11.12.0, cached render tool | MIT; [publisher](https://github.com/mermaid-js/mermaid-cli) |
| Puppeteer | 23.11.1, existing Mermaid browser controller | Apache-2.0; [publisher](https://github.com/puppeteer/puppeteer) |
| Poppler | 26.05.0 | GPL-2.0-or-later; [publisher](https://poppler.freedesktop.org) |
| PostgreSQL | tracked major 16 image | PostgreSQL Licence; [publisher](https://www.postgresql.org/about/licence/) |
| pgvector | tracked pg16 container tag, mutable | PostgreSQL Licence; [publisher](https://github.com/pgvector/pgvector) |

The PDF embeds only the licensed fonts and original figures, not these tools.
Tool-version observations are not a software bill of materials for a shipped
container. Container tags/actions remain mutable; see the audit's supply-chain
finding. No commercial browser is redistributed here.
