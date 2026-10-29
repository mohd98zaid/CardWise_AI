# Data Model

## Relationships
Issuer -> Cards -> Card variants -> Rules -> Evidence. Users -> portfolio cards, spending profiles, scenarios, reminders. Scenarios -> spend buckets, allocations, calculation runs -> trace steps.

## Tables

- `users`: ID, normalized email/identity subject, password hash if applicable, status, timezone, currency, timestamps. Never plaintext passwords.
- `issuers`: name, market, official domain, status.
- `cards`: issuer, product family, market, currency, status.
- `card_variants`: card, exact display name, network, variant/co-brand identifiers, validity dates, status.
- `sources`: publisher, type, title, canonical URL/document ID, published/retrieved/effective dates, content hash, status, rights status.
- `source_excerpts`: source, page/heading/locator, excerpt and hash.
- `rules`: variant, type, schema version, validated parameters/conditions, precedence, effective dates, verification/review state, supersedes reference, author/reviewer, hash.
- `rule_evidence`: rule, excerpt, evidence role, notes.
- `rule_test_cases`: rule, inputs, expected outputs, type.
- `rule_reviews`: reviewer, decision, comments, timestamp.
- `user_cards`: user, variant, nickname, status; no payment credentials.
- `spending_profiles`: user, name, currency, period.
- `scenarios`: user, profile, date, currency, revision/manifest.
- `scenario_spend`: scenario, category, channel, Decimal amount, optional count/ticket size, classification confidence, fixed flag.
- `scenario_allocations`: scenario, spend bucket, variant, Decimal amount, allocation type.
- `cap_usage_assumptions`: scenario, rule, period, nullable consumed amount, knowledge state.
- `valuation_profiles`/`point_valuations`: program, Decimal value per point, currency, dates, source/user assumption, valuation kind.
- `calculation_runs`: scenario revision hash, engine version, rule manifest, input snapshot, result/hash, status.
- `calculation_trace_steps`: run, sequence, rule, step type, input/output, reason code, evidence IDs.
- `reminders`: user, optional card, label, due timestamp, timezone, status.
- `audit_events`: actor, action, entity, before/after hashes, redacted metadata, timestamp.

## Constraints
Use numeric/Decimal for money, foreign keys, indexes for search/effective dates/user resources, unique variant identity where possible, transactions for publication, and preserve historical manifests.

## Retention
Set distinct policies for user data, scenarios, source content, AI history, imports, logs, audit, and backups.
