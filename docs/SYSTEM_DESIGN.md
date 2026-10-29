# System Design

## Quality attributes
Determinism, reproducibility, access isolation, explicit uncertainty, maintainable rules, AI isolation, and auditable editorial changes.

## Calculation request lifecycle
1. Authenticate and authorize.
2. Validate variant, date, currency, category, channel, amount, and assumptions.
3. Load an immutable rule manifest for the scenario date.
4. Detect missing/conflicting rules.
5. Evaluate eligibility and exclusions.
6. Calculate gross rewards using Decimal.
7. Apply caps in documented order.
8. Convert points only with selected valuation.
9. Apply transparent fee treatment and rounding.
10. Persist input snapshot, trace, manifest, engine version, and result.
11. Return result status, warnings, and trace reference.

## Reproducibility and concurrency
- Same input snapshot + rule manifest + engine version => same result.
- Use transactions for rule publication.
- Use optimistic concurrency/version fields for drafts.
- Publish manifests atomically so calculations cannot read a mixed rule set.

## Optimizer
Preserve total spend per category/channel bucket. Model eligibility and fixed allocations as constraints. Evaluate caps/thresholds as piecewise functions. Use enumeration for small bounded cases or a suitable solver for complex cases. Record method/version and report infeasibility.

## Caching
Cache public catalogue only with invalidation on publication. Isolate user-specific keys. AI cache keys include source versions. Never reuse stale calculation output without its manifest.

## Security
TLS, private database network, least-privilege credentials, role checks, no sensitive card credentials, untrusted retrieved documents, and narrow AI tools.
