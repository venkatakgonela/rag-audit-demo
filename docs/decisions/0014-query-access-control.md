# 0014: Query-enforced fixture access control

Status: Accepted

## Context

The synthetic demonstration needs isolated customer claims and explainable staff access.

## Decision drivers

Fail closed, preserve customer/broker boundaries, and rank only authorised evidence.

## Options considered

Explicit grant lists are flexible but add administration. Conjunctive tier/team rules are tighter but do not support independent staff ownership. Role tiers OR trusted team ownership OR claim ownership/assigned broker relationships fit the demonstration, provided external identities cannot join staff teams and claims are always restricted.

## Decision

Public clears all roles; broker clears brokers/admin; internal clears underwriters/admin; restricted clears admin only. Staff team ownership and claim owner/assigned broker are independent grants. Customers and brokers have no staff memberships. Claims require a customer owner and restricted tier. This is a conscious owner-subject extension to tier/team access.

The CLI resolves trusted fixture identities from the database. A materialised eligible SQL relation applies grants before exact vector and full-text ranking. No approximate index exists in the application schema. Ingestion and retrieval share an advisory-lock boundary to avoid mixed corpus/identity snapshots.

## Consequences

Exact search costs grow with eligible corpus size. This is not authentication infrastructure, row-level database security or a constant-time service. Anyone controlling the process/database is trusted. Semantic abstention remains planned; inaccessible content must not influence visible results or signals.

## Revisit when

External authentication, arbitrary team assignment, multiple organisations or measured scale require a stronger model.

## Sources

[Implementation](../../src/rag_audit/retrieval.py), [tests](../../tests/integration/test_retrieval.py), [PostgreSQL materialisation](https://www.postgresql.org/docs/16/queries-with.html), [pgvector filtering](https://github.com/pgvector/pgvector#filtering).
