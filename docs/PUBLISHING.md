# Publication checklist

Status: preparation in progress; not publication clearance. The repository remains private. No visibility, settings, pull request, tag or release change has been made by this work.

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

Final local/fresh-clone verification and owner review are required before
publication. Missing platform permissions are unavailable, not successful checks.

## Settings read-back and owner-only commands

Observed: private repository, main default, issues enabled, discussions disabled,
homepage empty, no topics. Description was “Audit-grade RAG with an evaluation
harness (synthetic data)”. Actions enabled, all actions permitted, SHA pinning
not required. Workflow token defaults to read; review approval by Actions is
disabled. Branch protection/rulesets returned plan-related 403; fork policy was
unavailable. Vulnerability alerts returned 404 (disabled); private reporting
returned 404 and is not verified enabled. Secret scanning/push protection status
was absent, not verified. Recheck feature availability after the owner changes
visibility; never equate unavailable with enabled.

These are **manual proposals, not commands run by this task**. The owner should
review each payload and platform eligibility before applying it:

```sh
REPO=venkatakgonela/rag-audit-demo
gh repo edit "$REPO" --description 'Synthetic RAG audit demonstration: builder self-assessment and reproducible evidence' --homepage '' --enable-issues --enable-discussions=false
gh api --method PUT "repos/$REPO/topics" --input - <<'JSON'
{"names":["rag","evaluation","synthetic-data","security-testing"]}
JSON
gh api --method PUT "repos/$REPO/branches/main/protection" --input - <<'JSON'
{"required_status_checks":{"strict":true,"contexts":["checks","integration","evaluation"]},"enforce_admins":true,"required_pull_request_reviews":{"required_approving_review_count":1,"dismiss_stale_reviews":true},"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}
JSON
gh api --method PUT "repos/$REPO/actions/permissions/workflow" --input - <<'JSON'
{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}
JSON
gh api --method PUT "repos/$REPO/actions/permissions/fork-pr-contributor-approval" --input - <<'JSON'
{"approval_policy":"all_external_contributors"}
JSON
gh api --method PUT "repos/$REPO/vulnerability-alerts"
gh api --method PUT "repos/$REPO/private-vulnerability-reporting"
gh api --method PATCH "repos/$REPO" --input - <<'JSON'
{"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}
JSON
```

Read each endpoint back with `gh api` without a mutation method; additionally
inspect the Security settings in the browser. Confirm the three exact check
contexts exist on the final reviewed commit. Keep fork secrets unavailable and
default tokens read-only. Some features require visibility/plan changes; record
errors rather than skipping their prerequisites. The owner decides when/if to
change visibility in repository Settings after review. Renaming the historical
PR titles is optional, never necessary to preserve the report evidence.

## Tag and release preparation (owner only)

After the reviewed branch is merged and checks pass, from the main branch:

```sh
git switch main
git pull --ff-only
git status --short
git tag -a v0.1.0 -m 'Synthetic audit demonstration 0.1.0'
git push origin v0.1.0
gh release create v0.1.0 --verify-tag --title '0.1.0 - synthetic audit demonstration' --notes-file docs/release-notes.md
```

Stop if the checkout is dirty, the reviewed commit is absent, checks fail or the
tag already exists. Do not force-replace a tag. The release notes are prepared,
not published. Pinning the repository and updating any public profile are owner
actions after the anonymous-visitor check, not part of this implementation.
