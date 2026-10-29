# Test Plan and Evaluation

## Unit tests
Variant/effective-date selection; eligibility; exclusions; rates; cap scope/period/boundaries; prior cap usage; fees; point conversion; rounding; refunds where implemented; missing/conflicting rules.

## Property tests
- Rewards do not exceed a defined cap.
- Excluded spend does not earn excluded rewards.
- Simple uncapped fixed-rate rewards are monotonic.
- Allocations preserve planned spend.
- Same input snapshot + manifest + engine version produces same result.
- Rules outside effective period are not applied.
- Unknown cap use is not silently zero.
- Net value follows documented formula.

Adapt properties for tiered rules, thresholds, and reversals.

## Integration
Persistence, publication gates, scenario calculations, ownership checks, citations, export expiry, deletion, reminders, fresh DB migrations and upgrade migrations.

## E2E
Sign in/demo, add synthetic card, create scenario, compare, inspect trace, ask supported assistant question, create reminder, export/delete, test cross-user denial, verify draft rule cannot drive a verified result.

## Golden suite
Maintain reviewed inputs/expected outputs for each rule type. Changes require tests. Change expected outputs only after evidence/rule review.

## AI evaluation
Measure retrieval recall, citation correctness, unsupported claims, abstention, variant resolution, completeness, latency, cost, privacy leakage. Test stale/conflicting sources and prompt injection.

## Performance/release blockers
Measure catalogue/calculation/optimizer latency and errors. Block release for critical test failures, unsupported published rules, authorization failure, failed migration/restore, secrets in source, sensitive logs, or material AI regression.
