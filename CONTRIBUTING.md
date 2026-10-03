# Contributing

This is a synthetic demonstration, not a production service. Prefer small,
focused changes; use labelled synthetic data only and never include secrets.

## Setup and checks

Follow the [README quickstart](README.md#try-it-locally), then run:

```sh
make lint typecheck test
```

These checks need no database, model download or provider key once dependencies
are installed. Use the [developer reference](docs/development.md) for isolated
integration tests and cached-model replay checks. Changes belong in pull requests;
the CI job names are `checks`, `integration` and `evaluation`. Owner configuration
of required-check protection remains a publication prerequisite, not an assertion
that it is already enabled.

Use the issue and pull request templates. Add failure-path and hostile-input tests
for security boundaries; significant decisions need a short
[decision record](docs/decisions/README.md). Preserve frozen evaluation evidence
and report failures honestly; do not rebaseline merely to make checks green.

## Commit identity

Maintainer commits use `Venkata K Gonela
<60929222+venkatakgonela@users.noreply.github.com>`; contributors use their GitHub
no-reply identity. GitHub merges record `GitHub <noreply@github.com>` as committer,
and Dependabot uses its bot address. Do not add assistant attribution trailers or
internal workflow identifiers. Never commit credentials, personal paths or real
data. See [accepted historical provenance](docs/PUBLISHING.md).
