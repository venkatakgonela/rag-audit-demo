# Publication checklist

Status: local readiness checks complete; owner review and platform settings remain publication prerequisites. The repository remains private. No visibility, settings, pull request, tag or release change has been made by this work.

## Accepted historical exceptions

The owner explicitly accepted these narrow provenance exceptions on October 3, 2026. They preserve honest history and existing evidence links rather than rewrite commits, invalidate baseline provenance or replace the proof pull requests.

- Commits `14116ca2522be0c1ad055792fb8099859a2060b8` and `dc5cc2e46768c54fa01329eee9101469b1f8b1dd` contain an AI co-author trailer. These two early messages name an assistant used under the author's direction. The metadata is accepted historical provenance, not a credential. No new assistant trailers are added. The platform may display the historical co-author as a contributor.
- Six platform merge bodies retain the branch-derived title lines for pull requests #1–#6: commits `aa0002c`, `384231d`, `365b297`, `569c600`, `2c6447b` and `2d191b5`. These workflow identifiers are accepted in those existing messages only.
- Existing `task/...` and `proof/...` branch/ref names and platform-generated merge subjects quoting them are accepted workflow metadata, not exceptions for private details in file content.
- Seven existing platform merge commits use `GitHub <noreply@github.com>` as committer. Their human author remains Venkata K Gonela with the approved public no-reply identity.
- The branch-derived titles of pull requests #1–#6 remain unchanged. Renaming them is optional and belongs to the owner; doing so would not change historical merge bodies.

All other scan rules remain in force. No history rewrite or replacement repository is authorised. Required third-party attribution is assessed in context, not mistaken for private product information.

## Read-only readiness checks (October 3, 2026)

- Covered all 22 remote refs, all locally reachable history and the two additional
  platform-generated proof-PR merge objects, all nine PR titles/bodies and all
  comment/review endpoints (no comment/review bodies returned). Those two
  ephemeral merge objects also have the required human author and platform
  committer; they do not widen the human-identity exception.
- Four existing Actions logs were inspected: main/reviewed remediation and both
  deliberate proof runs. This is a spot-check, not a claim to inspect every
  historic job. Known-secret variants, private-marker and credential patterns
  are checked without printing secret values.
- Contextual review distinguishes dependency attribution, protocol/library names,
  generated binary bytes and run IDs from disclosures. Font/PDF compressed bytes
  contain accidental text-pattern matches; extracted PDF text and metadata are
  checked separately. Required licence authors retain their original notices.
- Large files are intentional: the existing full live reference retains failed
  and successful synthetic traces; the two Noto Sans font files carry the OFL;
  the PDF and rendered diagrams are reader-facing assets. No model is shipped.
- Licence metadata is MIT for original work. The locked Python inventory includes
  conditional and optional dependencies; copyleft/mixed terms are flagged rather
  than described as all-permissive. Full licence/notice texts are retained.
- Anonymous visitor access cannot be checked while private. After publication,
  the owner must check the first README screen, PDF, file tree, licence display,
  docs index and both proof links without signing in.

Local and fresh no-hardlinks clone checks pass: lint, types, unit tests,
integration, recorded replay gate and fault self-tests. Offline PDF rebuilds
produce the same extracted text and tables, with no external page requests;
the 12-page report has been visually inspected. Owner review remains required.
Missing platform permissions are unavailable, not successful checks.
