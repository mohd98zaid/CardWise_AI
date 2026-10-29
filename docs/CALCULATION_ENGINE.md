# Deterministic Calculation Engine

## Purpose
Deterministic, explainable reward estimates. No LLM calls, network access, or frontend-provided authoritative result.

## Inputs
Exact variant, scenario date, amount/currency, category/channel, optional merchant category, transaction count/ticket size, cap usage state, valuation profile, fee method, rule manifest, assumptions.

## Outputs
Eligible/excluded spend, reason codes, gross reward/unit, cap before/after, conversion, fee allocation, net estimate, status/warnings, evidence IDs, trace, engine version, manifest hash.

## Pipeline
1. Validate inputs.
2. Resolve variant and date-valid rules.
3. Detect missing/conflicting rules.
4. Evaluate eligibility and exclusions.
5. Determine eligible spend.
6. Apply earn formula.
7. Apply caps in documented order.
8. Convert points only with explicit valuation.
9. Apply fee treatment.
10. Apply documented rounding.
11. Persist trace and manifest.
12. Return only the certainty supported by inputs.

## Arithmetic
Use Decimal and database numeric types. Avoid float for authoritative money calculations. Keep intermediate precision. Do not mix currencies without dated FX source. Point value is an assumption unless a reliable cash redemption path is evidenced. Unknown cap usage is never silently zero.

## Statuses
`verified_estimate`, `estimated`, `partial`, `needs_input`, `cannot_calculate`, `stale_rules`, `conflicting_rules`, `ineligible`, `excluded`.

## Edge cases
Cap scope/period/reset/order must be explicit. Exclusions return a reason. Fees must not subtract an entire annual fee from every monthly category comparison. Refund reversals are modeled only when terms are known. Undisclosed rounding behavior must be labeled as an estimate.

## Synthetic example
A fictional 5% cashback rule capped at ₹500/month yields ₹400 on ₹8,000 eligible spend if no cap has been used. If ₹450 has been consumed, at most ₹50 remains. If the spend is excluded, return zero with an exclusion reason. These are test values only.
