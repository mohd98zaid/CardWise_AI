# Rule Schema and Governance

## Rule families
`cashback_rate`, `points_rate`, `fixed_reward`, `cap`, `exclusion`, `eligibility`, `threshold`, `fee`, `point_conversion`, `benefit`, `reversal`, `rounding`.

## Required fields
Stable ID, exact card variant, type/schema version, typed parameters, conditions, precedence, effective dates, verification state, evidence, author/reviewer, timestamps, supersedes ID, regression fixtures.

## Lifecycle
`draft -> in_review -> verified/published -> superseded/expired`; additional states: `needs_review`, `rejected`. Draft/rejected rules never affect production calculations.

## Publication gates
Schema valid; authoritative evidence attached; effective dates explicit; required parameters present; regression tests pass; conflicts resolved; authorized review recorded; audit event persisted; publication atomic.

## Conflict policy
Never choose the most favorable value. If sources conflict or precedence is unclear, block confident calculation and queue review.

## Synthetic example only
```json
{
  "schema_version": 1,
  "rule_id": "synthetic-online-cashback-v1",
  "card_variant_id": "synthetic-variant",
  "rule_type": "cashback_rate",
  "parameters": {
    "rate_percent": "5.0",
    "cap_amount": "500.00",
    "cap_period": "calendar_month",
    "eligible_categories": ["online_shopping"],
    "eligible_channels": ["online_card"]
  },
  "effective_from": "2026-01-01",
  "effective_to": null,
  "verification_status": "draft",
  "evidence_ids": [],
  "notes": "Fictional fixture; not a real issuer offer."
}
```

Reject unknown rule types, invalid dates, missing references, invalid ranges, executable expressions, and production rules without evidence. Version schemas and preserve historical rule snapshots.
