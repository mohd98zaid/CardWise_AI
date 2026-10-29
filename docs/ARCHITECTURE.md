# Architecture

## Decision
Use a modular monolith first, with strict package boundaries and interfaces. Extract services only when measured scale or reliability needs justify it.

## Logical architecture
```text
React + TypeScript
       | HTTPS/JSON
       v
FastAPI API
  |      |        |        |
 Auth Catalogue Scenarios Admin
             |
             v
        Domain services
        /            \
       v              v
Rules calculator   Evidence/AI retrieval
       |              |
       v              v
 PostgreSQL       Citation validator
       |
       v
Manifests / traces / audit events
```

## Modules
- `identity`: auth, sessions, roles.
- `catalogue`: issuers, cards, exact variants.
- `evidence`: sources, excerpts, locators, hashes.
- `rules`: schemas, effective dates, review/publish workflow.
- `scenarios`: spend buckets and allocations.
- `calculator`: pure deterministic evaluation.
- `optimizer`: feasible allocation and objective.
- `assistant`: retrieval and grounded explanations.
- `notifications`: reminders.
- `audit`: append-only business events.
- `exports`: export and expiry.
- `operations`: metrics, logging, retention.

## Boundaries
Frontend is not trusted for authorization or authoritative arithmetic. Calculator has no network calls. AI cannot publish rules or execute arbitrary code. Rules are typed data, not executable expressions. Every private resource requires server-side ownership checks. AI outages must not disable calculations.

## Failure modes
Missing rules => partial/needs-input/cannot-calculate. Conflicting rules => no confident result and review task. Stale source => explicit stale state. AI outage => assistant unavailable while catalogue and calculator continue.
