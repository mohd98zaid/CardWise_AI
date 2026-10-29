# Implementation Backlog

## Epic 0 — Foundations
- [ ] Repo and review strategy.
- [ ] README, privacy, security, contribution docs.
- [ ] Frontend/backend skeleton.
- [ ] Lint, type-check, tests, environment validation.
- [ ] Docker Compose, CI, secret scanning, request IDs.
- [ ] Synthetic fixtures and ADR template.

## Epic 1 — Data
- [ ] Domain types and schemas.
- [ ] Migrations, foreign keys, indexes, constraints.
- [ ] Repository interfaces and migration tests.
- [ ] Historical rule retention.

## Epic 2 — Evidence/rules
- [ ] Source registry, hashes, excerpts and locators.
- [ ] Rule editor and validator.
- [ ] Evidence links and test cases.
- [ ] Independent review and atomic publication.
- [ ] Audit, rollback, stale/conflict queue.

## Epic 3 — Catalogue
- [ ] Search issuers/cards/variants.
- [ ] Detail pages, sources, dates, rules.
- [ ] Filters, pagination, accessibility.
- [ ] Hide drafts from users.

## Epic 4 — Scenarios
- [ ] Taxonomy and CRUD.
- [ ] Spend editor, currency/date.
- [ ] Fixed allocations and cap assumptions.
- [ ] Missing/unknown handling and ownership tests.

## Epic 5 — Calculator
- [ ] Decimal types and effective-date selection.
- [ ] Eligibility, exclusions, rates, caps.
- [ ] Points valuation, fee methods, rounding.
- [ ] Unknown/conflict statuses.
- [ ] Trace, manifest, golden/property tests.

## Epic 6 — Optimizer
- [ ] Compare API/UI.
- [ ] Constraint model and candidate method.
- [ ] Caps/thresholds and total-spend preservation.
- [ ] Infeasibility, sensitivity, trace.
- [ ] Tests where greedy fails.

## Epic 7 — AI
- [ ] Permitted ingestion and locators.
- [ ] Metadata-aware retrieval.
- [ ] Evidence-only prompt and citation validator.
- [ ] Abstention, injection tests, eval dataset.
- [ ] Model/prompt versioning and graceful degradation.

## Epic 8 — User controls
- [ ] Reminders, timezone handling.
- [ ] Export expiry and deletion.
- [ ] Retention policy and deletion tests.

## Epic 9 — Release
- [ ] Authorization, dependency and secret scans.
- [ ] CORS/security headers.
- [ ] Monitoring, health checks, backup/restore.
- [ ] Incident runbook, load/accessibility tests.
- [ ] Source licensing review and acceptance gates.
