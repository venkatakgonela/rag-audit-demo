# 0028: Pin all CI jobs to Ubuntu 24.04

Status: Accepted

Recorded: October 3, 2026; hosted verification pending.

## Context

An earlier hosted run warned of an upcoming `ubuntu-latest` migration. Platform-sensitive baselines should not change OS implicitly. Real embeddings need public weights, not provider secrets.

## Decision drivers

Consistent OS, explicit upgrades, secret-free fork checks, bounded setup cost and unconditional cache verification.

## Options considered

- Follow `ubuntu-latest`: less maintenance but implicit OS changes.
- Pin only evaluation: preserves its OS but leaves unrelated failures possible in other jobs.
- Pin all three jobs to `ubuntu-24.04`: adopt consistent reviewed upgrades, accepting maintenance. This is an OS label, not immutable VM contents or CPU features.
- Download weights each run: simpler but wasteful. Cache pinned bytes and verify independently instead.

## Decision

All jobs use `ubuntu-24.04`; existing checks/integration steps remain unchanged. Evaluation adds its own PostgreSQL service, locked embedding runtime, `actions/cache@v4`, unconditional model verification/provisioning, read-only gate and faulty-variant tests. Cache key includes full model revision and manifest digest; no fallback keys. Corrupt cache fails. Fifteen-minute timeout; warm target under about ten minutes, subject to hosted measurement.

Use ordinary `pull_request` and `push`, `contents: read`, checkout `persist-credentials: false`, no secrets/provider access. Bootstrap may download locked dependencies/pinned model; tests do neither. Fork execution can need owner approval under platform policy; no elevated event is used. Existing major-tag actions remain; SHA pins, dependency update automation and image digests stay separate hardening work.

## Consequences

Syntax checks/emulated x86 results are not hosted success. Observe initial cold/warm timing and all gate values before accepting provisional tolerances. Image updates still happen within the label. Model cache contains no private material.

## Revisit when

First hosted run, Ubuntu support/runtime changes, unexplained drift, or supply-chain hardening.

## Sources

- [Workflow](../../.github/workflows/ci.yml), [guards](../../tests/test_ci_gate_configuration.py).
- [Runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [cache v4](https://github.com/actions/cache/blob/v4/README.md), [cache scope](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).
