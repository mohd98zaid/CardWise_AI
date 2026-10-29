# ADR-002: PostgreSQL

- Status: accepted
- Date: 2026-10-26

## Context
The product needs relational integrity, effective-dated rules, ownership, audit, and reproducible manifests.

## Decision
Use PostgreSQL for shared deployment. SQLite may be used in limited local tests if behavior is compatible.

## Consequences
Use constraints and transactions; test migrations against the production database engine.
