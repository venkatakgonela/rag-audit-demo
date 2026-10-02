# Engineering rules for contributors and coding agents

## Rules

1. **Synthetic data only.** All documents, people, claims and identifiers are fabricated and labelled synthetic wherever they appear. No real PII, no real company or insurer names.
2. **No secrets in git.** Configuration comes from environment variables; commit `.env.example` only.
3. **Security invariants (do not weaken to make a test pass):**
   - Access control is enforced inside the retrieval query (pre-filter), never by post-filtering results.
   - Anything computed by the deterministic rules layer is computed by code; the LLM only phrases it.
   - Every citation must reference a chunk that was in the caller's authorised retrieved set.
   - An unauthorised request must not reveal whether a restricted document exists.
4. **Honest results.** Never hardcode, tune-to-the-test, or fake metrics. Report failures as failures.
5. **Original work.** Write from public library documentation; do not paste code or data from other projects.
6. **Stay in scope.** Implement only what the task asks. Park other ideas in `docs/BACKLOG.md`.

## Stack

Python 3.12 (`uv`), FastAPI, PostgreSQL 16 + pgvector (Docker Compose), pytest, ruff, GitHub Actions. LLM access goes through a small provider interface; local open-source embeddings.

## Definition of done

- `make lint` and `make test` pass locally and in CI.
- New behaviour has tests, including failure paths.
- Docs and Makefile targets match reality; runs from a clean clone.

## Commits

Small, focused commits with conventional prefixes (`feat:`, `test:`, `docs:`, `chore:`).

## Documentation

Record non-trivial product decisions as ADRs with real alternatives and revisit triggers. Keep architecture diagrams and technology/pattern catalogues current, label implemented versus planned behaviour, link security claims to tests, and keep documentation checks passing. Preserve accepted decision text; use dated additive clarifications or superseding ADRs rather than rewriting rationale.
