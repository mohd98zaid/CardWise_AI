# Portfolio Optimizer

## Objective
Maximize estimated net reward value for already-planned spending across cards the user owns.

## Inputs
Spend by category/channel, owned variants, baseline allocations, scenario date/rule manifest, cap usage, point valuation, fee method, fixed allocations, user constraints.

## Constraints
- Preserve total spend in every bucket.
- Set allocation to zero for ineligible card/bucket pairs.
- Respect caps, transaction limits, fixed allocations, and user exclusions.
- Do not silently assume unknown cap usage is zero.
- Do not increase planned spend to unlock rewards.
- Do not treat unowned cards as available in owned-card mode.
- Flag unsupported milestones.

## Model
Let `x[c,k]` be spend assigned to card `c` for bucket `k`.
`sum_c x[c,k] = planned_spend[k]`
For ineligible combinations, `x[c,k] = 0`.
Maximize estimated reward value minus explicitly allocated fees. Caps/thresholds can make the objective piecewise or discontinuous.

## Method
Use enumeration for small bounded cases or a suitable constrained solver for complex cases. Greedy allocation only when validity is proven for the supported rule subset. Record method/version and test cases where greedy fails.

## Output
Baseline/proposed allocation, total spend preserved, reward values and delta, per-card/category breakdown, cap/threshold effects, fees, unknowns, sensitivity, infeasible constraints, manifest, method version.

## Safety
Never make increased spending the primary recommendation. If asked about a milestone, show the gap and estimated benefit separately and caution that spending/debt costs can exceed rewards.
