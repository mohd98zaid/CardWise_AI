# Implementation Plan

## Phase 0 — Foundations
Confirm market, issuers, hosting, source rights, reviewers, and retention. Create repo, CI, environments, synthetic fixtures, and ADRs. Exit: local app and CI work.

## Phase 1 — Evidence/catalogue/rules
Implement issuers, cards, variants, source registry, rule schema, effective dates, review/publish workflow, and audit. Exit: synthetic verified rule can publish only after gates pass.

## Phase 2 — Scenarios
Implement categories/channels, scenario CRUD, ownership, cap usage assumptions, valuation profiles, and unknown semantics. Exit: scenarios save/duplicate/reload.

## Phase 3 — Calculator
Implement selection, eligibility, exclusions, rates, caps, conversions, fees, rounding, statuses, traces, and golden/property tests. Exit: deterministic supported fixtures pass.

## Phase 4 — Compare/optimize
Implement baseline/proposed allocation, constraints, spend preservation, sensitivity, and infeasibility handling. Exit: reproducible outputs.

## Phase 5 — AI assistant
Ingest permitted sources, add retrieval, citations, abstention, prompt-injection tests, and evaluation. Exit: assistant cites or abstains and cannot write rules.

## Phase 6 — Privacy/operations
Export/deletion, reminders, retention, metrics, health checks, backup/restore, security/accessibility review. Exit: no critical issues.

## Phase 7 — Verified pilot
Verify real launch terms from official sources, independent review, regression, pilot, runbooks, release. Eight-week schedule is an estimate, not a guarantee.
