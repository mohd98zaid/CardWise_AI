# Product Requirements Document (PRD)

## Product summary
CardWise AI helps users compare estimated rewards across existing credit cards for already-planned spending. It combines a verified catalogue, versioned rules, deterministic calculator, constrained portfolio optimizer, and evidence-grounded assistant.

## Problem
Card terms are spread across product pages, PDFs, fee schedules, FAQs, and change notices. Headline earn rates can be misleading once caps, exclusions, fees, channels, eligibility, and point redemption assumptions are considered.

## Users
- Cashback-focused cardholders.
- Rewards/points users.
- Multi-card portfolio managers.
- Editorial researchers and reviewers.

## Goals
- Compare exact variants.
- Show rates, caps, exclusions, fees, and assumptions.
- Produce reproducible traces.
- Optimize existing spend without increasing it.
- Maintain effective-dated, source-backed rules.
- Let AI explain evidence without inventing terms.

## Non-goals
No payments, card issuance, issuer-account access, guaranteed rewards, regulated financial advice, auto-publication of scraped changes, or recommendations to incur debt or unnecessary spending.

## MVP
1. Secure workspace or isolated demo.
2. Exact card catalogue.
3. Evidence/source registry.
4. Versioned rules and review workflow.
5. Spending scenarios.
6. Deterministic calculator and trace.
7. Card comparison.
8. Constrained optimizer.
9. Reminders, export, deletion.
10. Tests, logging, backups, deployment docs.

## Functional requirements
### Catalogue
Search issuer/product/variant/network/market. Show verification state, dates, evidence, fees, rates, caps, exclusions, and thresholds. Preserve historical variants.

### Rules
Support earn rates, caps, exclusions, thresholds, fees, point conversion assumptions, eligibility, reversals, and benefits. Publishing requires evidence, explicit dates, tests, and reviewer approval.

### Scenarios
Store category/channel spend, currency, date, allocations, cap-use assumptions, valuation profile, and unknowns. Distinguish zero, missing, estimated, and unknown.

### Calculator
Use Decimal. Enforce exact variant and effective dates. Return eligible/excluded spend, rewards, caps, fees, net estimate, warnings, status, evidence, and trace.

### Optimizer
Preserve total planned spend. Optimize only across owned cards by default. Respect eligibility, caps, fixed allocations, and constraints. Return baseline, proposal, incremental value, assumptions, and method version.

### AI
Use retrieved evidence, cite material claims, abstain when evidence is insufficient, and never publish rules or replace the calculator.

## Non-functional requirements
Security, privacy, explainability, accessibility, maintainability, and operational readiness are mandatory.

## Success metrics
- 100% active material rules have evidence and date policy.
- 100% published rules pass required tests.
- 100% calculation results include a rule manifest.
- Zero silent fallback to unverified values.
- No acceptance/storage of full PAN, CVV, PIN, OTP, or issuer credentials.
- AI citation and unsupported-claim rates measured against a versioned evaluation set.

## Assumptions/open decisions
India-first, small verified catalogue, modular monolith, PostgreSQL, no bank connection in MVP. Decide launch issuers, source licensing, reviewers, point valuation, retention, hosting, and whether RAG belongs in MVP.
