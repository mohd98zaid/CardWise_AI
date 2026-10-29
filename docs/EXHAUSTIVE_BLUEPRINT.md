# CardWise AI — Credit Card & Rewards Optimizer
## Exhaustive Product Requirements, Technical Design, and Implementation Blueprint

**Document status:** Implementation blueprint  
**Product market:** India first; extensible to other markets  
**Primary users:** People holding multiple credit cards who want to maximize value without increasing unnecessary spending  
**Architecture principle:** Deterministic calculations + verified versioned rules + evidence-backed AI explanations  
**Implementation style:** Modular monolith first, with clean service boundaries and optional later extraction  
**Default currency:** INR  
**Important limitation:** This document is a build specification, not a claim that current issuer benefits have already been verified. Card rules must be researched against official sources before being activated.

---

# 0. How to Use This Document

This document is intended to be usable by a product owner, software engineer, QA engineer, AI engineer, and implementation agent.

- Treat every requirement marked **MUST** as mandatory for the MVP unless a later section explicitly defers it.
- Treat card benefits as data, never as scattered hard-coded `if/else` logic.
- Never activate a material benefit rule without a source, an effective date, and a verification state.
- Do not let an LLM calculate or silently alter money values.
- Do not interpret unknown or missing values as zero unless the user explicitly chooses that assumption.
- Do not scrape behind authentication, bypass access controls, or violate a source's terms.
- Use synthetic card rules in development until real rules have been independently checked.
- If a requirement cannot be implemented safely, stop and document the gap instead of silently approximating it.

## Requirement language

- **MUST:** Required for release acceptance.
- **SHOULD:** Strongly recommended; deviations require a written reason.
- **MAY:** Optional enhancement.
- **Source fact:** Must be supported by an identified source.
- **Design decision:** A proposed implementation choice that can be revised before coding.

---

# 1. Executive Summary

CardWise AI helps users understand their credit-card portfolio and estimate which card or allocation of cards offers the highest net value for planned spending. It combines:

1. A verified catalogue of exact card variants.
2. A versioned rules engine for reward rates, caps, exclusions, thresholds, fees, and conversion assumptions.
3. A deterministic calculator with an auditable calculation trace.
4. A portfolio optimizer that compares feasible allocations.
5. A financial-terms assistant that retrieves source-backed evidence and explains it in plain language.
6. A review workflow that detects stale or conflicting rules and requires human approval before publishing changes.

The product is not a bank, issuer, credit bureau, payment processor, or financial adviser. It is a decision-support tool. It must communicate uncertainty and must not promise that an issuer will award a specific reward.

## 1.1 Core value proposition

A user should be able to answer:

- Which of my cards is likely to be best for this purchase?
- How much reward could I earn after caps and exclusions?
- What is the estimated net benefit after relevant fees?
- What assumptions drive the result?
- Which official terms support the result?
- What would change if a cap is already partly consumed?
- Is a card's annual fee offset by the value I actually use?
- Which information is uncertain, outdated, or missing?

## 1.2 Non-negotiable product principles

1. **Evidence before confidence:** unverified terms cannot produce a fully verified recommendation.
2. **Deterministic money math:** the same inputs and rule version must produce the same result.
3. **Explicit uncertainty:** unknown eligibility, missing conversion values, and conflicting sources must be visible.
4. **Net value, not headline rate:** caps, exclusions, fees, redemption value, and opportunity cost matter.
5. **No spend inducement:** the product must not recommend spending more merely to earn rewards.
6. **Privacy by design:** do not collect full card numbers, CVVs, PINs, passwords, or issuer login credentials.
7. **User control:** recommendations are advisory; the user decides whether to act.
8. **Version traceability:** every result can be reproduced using the rule versions and assumptions used at calculation time.

---

# 2. Product Goals, Non-Goals, and Success Metrics

## 2.1 Goals

- Provide an accurate, inspectable card catalogue.
- Support exact issuer, product, network, and variant distinctions.
- Model real-world rewards logic, including channel eligibility and caps.
- Compare current usage with alternative allocations.
- Support both cashback and points with transparent valuation assumptions.
- Explain why a transaction or category did or did not earn rewards.
- Provide source citations, source dates, and rule history.
- Offer natural-language help without allowing AI to invent terms.
- Keep the MVP affordable to run, using open-source components where practical.
- Allow rules to be updated without deploying new application code.

## 2.2 Non-goals for MVP

- Applying for, closing, upgrading, or downgrading cards on a user's behalf.
- Initiating payments or moving money.
- Accessing bank or issuer accounts using stored credentials.
- Guaranteeing issuer rewards, lounge access, insurance coverage, or fee waivers.
- Providing individualized regulated financial, legal, tax, or credit advice.
- Using a language model as the authoritative rules database.
- Automatically publishing scraped changes without review.
- Optimizing users into debt, revolving balances, or unnecessary purchases.
- Using private transaction data without explicit consent and a clear retention policy.
- Supporting every issuer at launch. A small verified catalogue is better than a broad unreliable one.

## 2.3 Product success metrics

### Accuracy and trust
- 100% of active material rules have a source URL or documented authoritative source identifier.
- 100% of active material rules have effective dates or an explicit documented date limitation.
- 100% of published rule changes have an audit record.
- 100% of calculation outputs include a reproducible trace.
- 100% of rules in the critical calculation suite pass regression tests before publication.
- Zero silent fallback to an unverified rate when a verified rate is missing.

### User experience
- A new user can create a spending profile without providing payment credentials.
- A user can compare two cards in a short guided flow.
- Each recommendation explains its major assumptions and limitations.
- Users can edit, export, and delete their own spending scenarios.
- Users can distinguish “verified,” “estimated,” “stale,” and “unknown” results.

### Reliability and security
- No raw PAN, CVV, PIN, password, or issuer credential is accepted by the API.
- Authentication and authorization tests cover every private endpoint.
- Database backups and restore procedures are tested.
- Critical application errors are observable without logging sensitive spending details.
- Data deletion requests are completed and verified according to the configured retention policy.

Do not use “money saved” as the sole success metric: rewards depend on issuer fulfillment, redemption behavior, fees, and actual user choices.

---

# 3. User Personas and Jobs to Be Done

## 3.1 Cashback-focused cardholder

**Needs:** Find the best eligible card for online shopping, groceries, dining, bills, fuel, and UPI where supported.

**Typical questions:**
- “Which of my cards should I use for this ₹5,000 purchase?”
- “Is the headline cashback rate limited by a monthly cap?”
- “Does this payment channel qualify?”

**Product response:** show the estimated outcome, eligibility conditions, remaining cap if known, and evidence.

## 3.2 Rewards-point optimizer

**Needs:** Compare point earning with different redemption values.

**Typical questions:**
- “Are these points worth more when redeemed for travel?”
- “What happens if I value each point at ₹0.25 instead of ₹0.50?”

**Product response:** present low/base/high redemption scenarios. Never present one assumed point value as a universal fact.

## 3.3 Multi-card portfolio manager

**Needs:** Allocate existing spending across cards without increasing total spending.

**Typical questions:**
- “How should I split my existing monthly spend?”
- “Does moving spend to another card exceed its cap?”
- “Will I lose a fee waiver or milestone if I change allocation?”

**Product response:** optimize only across feasible allocations and show trade-offs, caps, and threshold effects.

## 3.4 Card-term researcher/editor

**Needs:** Maintain accurate terms across card variants and effective dates.

**Typical questions:**
- “Which rule is outdated?”
- “Did the issuer change the monthly cap?”
- “Which source supports this rule?”

**Product response:** show change candidates, source comparisons, review queue, and immutable audit history.

## 3.5 Financial coach

**Needs:** Compare scenarios with minimal sensitive information.

**Product response:** allow scenario-only analysis and safe export; do not require account credentials or full card numbers.

---

# 4. Release Scope and Milestones

## 4.1 MVP — release gate

- Authentication and private user workspace.
- Exact card catalogue and variants.
- Versioned, source-backed rules.
- Rule editor and reviewer workflow.
- Spending profile and saved scenarios.
- Deterministic calculator.
- Comparison view.
- Current-versus-proposed allocation comparison.
- Fee and cap handling for supported rule types.
- Calculation trace and explanation.
- Basic reminders manually entered by the user.
- Export and delete user data.
- Automated tests, logging, health checks, deployment documentation.
- A small launch catalogue with all rules verified.

## 4.2 Version 1

- RAG-based Q&A over verified issuer documents.
- Full-text and semantic retrieval with citation enforcement.
- Scenario-based point valuations.
- CSV import of spending summaries.
- Stale-source and change-detection workflow.
- Admin dashboard for rule review.
- Notification integrations after user opt-in.
- More card variants and issuers.
- Portfolio history and month-over-month comparisons.

## 4.3 Later releases

- Statement import and transaction categorization, with explicit consent.
- Mobile client or browser extension.
- More markets and currencies.
- Shared editorial workflow for a verified public dataset.
- User-configurable optimization goals.
- Additional benefit types such as travel insurance or lounge visits, each modeled with explicit limitations.
- Optional integrations with supported financial-data providers where legally and contractually appropriate.

## 4.4 Definition of MVP complete

MVP is not complete merely because the UI renders. It is complete when:
- Supported rules are verified and versioned.
- Calculations are reproducible.
- Key edge cases pass tests.
- Uncertainty is shown correctly.
- Private data is protected.
- Admins can correct and roll back rule changes.
- Deployment, backup, restore, and incident procedures are documented.

---

# 5. Functional Requirements by Module

## 5.1 Module A — Authentication and User Workspace

### Requirements
- Support a standard secure authentication method.
- Use established password hashing or a trusted identity provider; never implement custom cryptography.
- Provide logout, session expiry, and account deletion.
- Enforce server-side authorization on every user-owned resource.
- Do not rely on hiding frontend buttons as an access-control mechanism.
- Use secure, HTTP-only cookies when cookie sessions are selected.
- Protect state-changing requests against CSRF where applicable.
- Rate-limit login, reset, and other abuse-prone endpoints.
- Allow a guest/demo mode only if its data separation is clear.

### User-owned objects
- Spending profiles.
- Scenarios.
- Card portfolio selections.
- Reminder settings.
- Saved comparison results.
- User preferences.

### Acceptance criteria
- User A cannot read or modify User B's scenarios by changing an ID.
- Deleted accounts cannot continue to access private data.
- Authentication secrets never appear in logs.
- Session and password-reset behavior is covered by tests.

## 5.2 Module B — Card Catalogue

### Search and display
- Search by issuer, marketed product name, network, product family, and variant.
- Distinguish variants even when their names are similar.
- Display joining fee, annual fee, renewal conditions, fee waiver thresholds, and known taxes/charges only when supported by verified terms.
- Display earn rates, exclusions, caps, thresholds, and conversion assumptions.
- Separate cash-equivalent rewards from non-cash benefits.
- Show “last verified,” “effective from,” and verification state.
- Show source links and relevant excerpts.
- Show the rule change history to authorized editors.

### Card identity rules
A card record must not be identified only by a display name. Use a stable internal ID and structured attributes:
- Issuer.
- Product family.
- Product variant.
- Network.
- Variant or program identifiers when available.
- Country/market.
- Currency.
- Validity period.
- Status: active, discontinued, unknown, or historical.

Do not merge products simply because their names are similar. Do not assume that network, co-brand, tier, or issuance date has no impact.

### Acceptance criteria
- Two variants can have different rates, fees, or caps.
- Historical cards remain available for past scenario reproduction.
- Unverified cards can be browsed but are visibly marked.
- A card's current status is not inferred solely from a search result snippet.

## 5.3 Module C — Source and Evidence Registry

### Source hierarchy
1. Official issuer product page or official terms and conditions.
2. Official issuer PDF, fee schedule, rewards guide, or change notice.
3. Official issuer FAQ or support article.
4. Authorized payment-network or program documentation when relevant.
5. Secondary publications for discovery and corroboration only.
6. Community posts for leads only, never as sole authority for a material current rule.

The precise hierarchy can vary by claim type. A dated official terms PDF may be more authoritative than a marketing page for detailed exclusions.

### Stored evidence
- Source ID and source type.
- Publisher/issuer.
- URL or official document identifier.
- Document title.
- Publication date, if known.
- Retrieved date.
- Effective date, if known.
- Content hash for version comparison.
- Relevant page, heading, or section.
- Exact short excerpt needed to support the rule.
- Reviewer and review date.
- Source reliability classification.
- Source status: current, superseded, inaccessible, or under review.

### Acceptance criteria
- Every material rule can be traced to evidence.
- Source text is stored with provenance.
- An inaccessible source does not silently become verified.
- A secondary source cannot override an official source without documented adjudication.

## 5.4 Module D — Versioned Rules Engine

### Supported rule families
1. Earn rate: cashback percentage, points per amount, fixed reward, or tiered rate.
2. Cap: per transaction, day, month, quarter, year, statement period, or lifetime.
3. Exclusion: merchant category, payment channel, transaction type, merchant, or other defined condition.
4. Threshold: spend milestone, minimum transaction amount, or fee-waiver threshold.
5. Fee: joining, annual, supplementary, conversion, or another explicitly modeled charge.
6. Conversion: points-to-currency or redemption value.
7. Eligibility: card variant, channel, merchant category, date range, transaction status, or other condition.
8. Benefit: non-cash benefit such as lounge access, stored separately from reward earnings.
9. Rounding: reward-unit or currency rounding rule, only where source terms establish it.
10. Reversal: reward reversal for refunds, cancellations, or disputed transactions where terms are known.

### Required rule fields
- Stable rule ID.
- Rule type.
- Card variant ID.
- Schema version.
- Priority or precedence.
- Effective-from and effective-to dates.
- Rule parameters in a validated typed structure.
- Conditions and exclusions.
- Source evidence IDs.
- Verification state.
- Reviewer ID and review timestamp.
- Created/updated timestamps.
- Superseded rule reference, if applicable.
- Test fixtures and expected results.
- Editorial notes.

### Rule evaluation order
1. Resolve the exact card variant and scenario date.
2. Resolve category and channel mapping.
3. Select rules whose effective period includes the scenario date.
4. Apply explicit eligibility conditions.
5. Apply exclusions and transaction-level constraints.
6. Determine the eligible spend basis.
7. Apply the earn formula.
8. Apply relevant caps in their defined order.
9. Apply points conversion only if the selected valuation is available.
10. Apply fee allocation according to the chosen scenario method.
11. Calculate net estimated value.
12. Return a trace containing each decision and evidence reference.

### Conflict handling
- If two active rules conflict and precedence cannot be established from authoritative terms, block a confident calculation.
- If a required rule parameter is missing, return `unknown` or `needs_review`.
- If a source is stale, label the result and apply the configured freshness policy.
- Never select whichever rate yields the highest reward.
- Never assume that a missing exclusion means a transaction is eligible.

### Rule publication states
- `draft`: editable; not used in production calculations.
- `in_review`: awaiting independent review.
- `verified`: reviewed and eligible for production use within its effective dates.
- `needs_review`: issue detected; behavior follows explicit fallback policy.
- `superseded`: retained for history, not used outside its valid period.
- `rejected`: not publishable.
- `expired`: validity ended; may be used for historical scenarios only.

## 5.5 Module E — Spending Profile and Scenario Builder

### Categories
The taxonomy should be configurable, but an initial taxonomy can include:
- Online shopping.
- Offline retail.
- Groceries.
- Dining.
- Fuel.
- Utilities and bills.
- Telecom and internet.
- Insurance.
- Rent.
- Education.
- Government payments.
- Travel and hotels.
- Transport.
- Healthcare.
- Entertainment and subscriptions.
- Wallet loads.
- UPI.
- Other.
- Unknown/unclassified.

This taxonomy is a user-facing classification, not an assertion that a card issuer treats every item in a category the same way.

### Channels
- Online card transaction.
- In-store card transaction.
- UPI via eligible credit-card network, where applicable.
- Wallet.
- Contactless.
- EMI.
- Standing instruction or subscription.
- Other.
- Unknown.

Channel availability and meaning must be configurable by market and card program.

### Scenario fields
- Scenario name.
- Currency.
- Month or scenario period.
- Category-level spend.
- Channel split where known.
- Transaction count or average ticket size where relevant.
- Current allocation to cards.
- Known cap usage.
- Selected reward valuation profile.
- Fee treatment.
- Assumptions and unknowns.
- Creation/update timestamps.

### Missing data behavior
- Missing is not automatically zero.
- The UI must distinguish zero spend from unknown spend.
- If a cap depends on prior usage and prior usage is unknown, show a range or conditional result rather than claiming the cap is unused.
- If a merchant category is uncertain, let the user select a classification and show the impact.

### Acceptance criteria
- Users can save multiple scenarios.
- A scenario can be duplicated and edited.
- A calculation records the scenario revision it used.
- Users can export scenario inputs without exposing unrelated personal data.

## 5.6 Module F — Deterministic Rewards Calculator

### Inputs
- Exact card variant.
- Spend amount and currency.
- Scenario date.
- Category and channel.
- Merchant category code if supplied and appropriate.
- Transaction count or ticket size if the rule requires it.
- Previously consumed cap amount if known.
- Point valuation profile if applicable.
- Fee allocation method.
- Rule-set version.
- Explicit user assumptions.

### Outputs
- Eligible spend.
- Excluded spend.
- Exclusion reason.
- Gross cashback or points.
- Cap before and after application.
- Reward value conversion.
- Fee allocation.
- Estimated net value.
- Missing inputs.
- Confidence/verification state.
- Rule and evidence references.
- Calculation trace.
- Warnings and limitations.

### Arithmetic rules
- Use decimal arithmetic for money and reward calculations; do not use binary floating-point for authoritative money math.
- Define currency precision and reward-unit precision per rule.
- Keep intermediate values at sufficient precision.
- Apply rounding only at the stage defined by issuer terms or the product's explicitly documented estimate policy.
- Store raw inputs and calculated outputs with rule-version references.
- Make rounding policy visible in the calculation trace.
- Do not mix currencies without an explicit exchange-rate source and date.
- If exchange rates are not implemented, reject cross-currency calculations rather than silently converting.

### Illustrative example — synthetic rules only
Assume a fictional card gives 5% cashback on eligible online spend, capped at ₹500 per month, and excludes a particular transaction type. These are illustrative values, not real issuer terms.

- Eligible online spend: ₹8,000.
- Uncapped cashback: ₹8,000 × 5% = ₹400.
- Monthly cap: ₹500.
- Estimated cashback: ₹400 before other exclusions and rounding.
- If prior cap consumption were ₹450, remaining cap would be ₹50 and estimated cashback would be limited to ₹50.
- If the transaction is excluded, cashback is ₹0 with an explicit exclusion reason.

The calculation result must distinguish “zero because excluded” from “zero because no eligible spend” and “unknown because rules are incomplete.”

## 5.7 Module G — Portfolio Optimizer

### Objective
Estimate the highest net reward value for a user's existing planned spending, subject to card eligibility, user-defined constraints, known caps, fee assumptions, and milestone interactions.

### Inputs
- Existing spend by category/channel.
- Available cards in the user's portfolio.
- Rule versions and scenario date.
- Cap consumption assumptions.
- Reward valuation assumptions.
- Fixed versus flexible category allocations.
- User constraints.
- Annual-fee treatment.
- Threshold and milestone assumptions.

### Constraints
- Never increase total planned spending as an optimization tactic.
- Do not recommend a card the user does not own as though it were available; new-card comparison must be a separate mode.
- Do not allocate spend to a card if the channel or category is ineligible.
- Respect caps and transaction constraints.
- Respect user-specified card exclusions.
- Preserve fixed allocations.
- Model fee-waiver thresholds only when terms and qualifying spend are known.
- If a milestone cannot be modeled exactly, flag it rather than pretending it is optimized.
- If cap usage is unknown, compare scenarios under explicit alternative assumptions.

### Optimization strategy
**MVP:** Use deterministic enumeration or a transparent greedy method only when the problem's constraints make that method valid. Document its limitations. For general cases involving shared caps, thresholds, and milestones, formulate a constrained optimization problem.

A useful general model:
- Decision variable `x[c, k]` = spend allocated to card `c` for category/channel bucket `k`.
- Total spend per bucket is preserved: sum of `x[c, k]` across cards equals the user's planned spend for that bucket.
- `x[c, k]` is zero if card `c` is ineligible for bucket `k`.
- Reward value is computed using the versioned rules, including caps and thresholds.
- Objective is to maximize estimated net reward value, not raw headline reward rate.
- Additional user constraints may require a minimum share on a particular card or prohibit specific cards.

Some reward functions are piecewise or discontinuous because of caps and thresholds. Use a solver or exhaustive scenario enumeration appropriate to the problem size; do not assume a simple greedy ranking is always optimal.

### Required optimizer output
- Recommended allocation.
- Baseline allocation and estimated value.
- Proposed allocation and estimated value.
- Estimated incremental value.
- Per-card and per-category breakdown.
- Caps reached or nearly reached.
- Fees and milestones included.
- Assumptions and unknowns.
- Cards or buckets excluded and why.
- Solver/method version.
- Rule-set version.
- Sensitivity results for uncertain assumptions.

### Safety guardrail
If the optimizer concludes that a user should spend more to unlock a benefit, it must not include that suggestion in the primary recommendation. It may show a separate neutral explanation of the threshold only when the user explicitly asks, with a warning to compare the benefit against the cost of spending and the risk of carrying debt.

## 5.8 Module H — Fee, Waiver, Milestone, and Benefit Tracker

### Supported records
- Joining fee.
- Annual/renewal fee.
- Fee-waiver threshold.
- Milestone reward.
- Reward expiry.
- Lounge access conditions.
- Benefit-use count where the user chooses to track it.
- Reminder date.
- Verification status and evidence.

### Behavior
- Reminders are informational.
- Do not imply a benefit is guaranteed unless the relevant current terms support it.
- Track qualifying spend separately from ordinary spend if the issuer defines qualifying spend differently.
- Use the correct measurement period.
- Distinguish a reminder date from an issuer deadline.
- Let the user disable reminders.
- Do not send messages to third parties without explicit configuration and consent.

## 5.9 Module I — AI Terms Assistant and RAG

### Allowed tasks
- Explain retrieved terms in plain language.
- Answer questions using verified documents.
- Compare two rule excerpts.
- Summarize exclusions and caps.
- Identify missing information.
- Suggest which official source should be checked.
- Help an editor draft a rule candidate from source evidence, without publishing it.

### Disallowed tasks
- Inventing a rate, cap, fee, eligibility condition, or date.
- Treating model memory as current issuer policy.
- Overriding the rules engine.
- Calculating authoritative money values in free-form language.
- Publishing a rule without required review.
- Claiming a source says something not present in the retrieved evidence.
- Hiding contradictory evidence.

### Retrieval pipeline
1. Ingest only permitted source material.
2. Preserve source URL, title, issuer, dates, and document version.
3. Extract text while retaining page/heading references.
4. Normalize whitespace without losing evidence coordinates.
5. Chunk by headings and logical sections.
6. Attach metadata: issuer, card variant, source type, effective dates, verification state.
7. Index using full-text search first; optional vector retrieval can supplement it.
8. Retrieve candidate chunks with metadata filters.
9. Rerank or select evidence.
10. Generate a response with citations.
11. Validate that every factual benefit claim maps to retrieved evidence.
12. Return “I could not verify this from the available sources” when evidence is insufficient.

### Retrieval preference
Start with PostgreSQL full-text search or another transparent lexical search. Add embeddings only if evaluations show meaningful improvement. Do not add a vector database just because the application uses AI.

### AI response contract
Every answer should separate:
- **What the source says**
- **What it means in plain language**
- **How it affects the user's scenario**
- **What remains unknown**
- **Sources and effective dates**

If a source is stale or not verified, say so prominently.

## 5.10 Module J — Rule Administration and Review

### Roles
- Viewer: read published rules.
- Editor: create draft rules and attach evidence.
- Reviewer: independently review and approve/reject drafts.
- Administrator: manage users, roles, source policies, and system configuration.

A person should not approve their own material rule change in a production workflow unless a documented low-risk exception is defined.

### Review queue
- New card candidates.
- Missing source evidence.
- Expiring or expired rules.
- Source content changed.
- Conflicting rules.
- Failed regression tests.
- User-submitted correction.
- Suspected parsing error.
- Rules whose effective dates are ambiguous.

### Publication gates
A rule cannot be published unless:
- Schema validation passes.
- Source evidence is attached.
- Effective-date behavior is explicit.
- Required fields are present.
- Rule tests pass.
- Conflict checks pass.
- An authorized reviewer approves it.
- The audit event is persisted.

### Rollback
- Never delete historical published rules merely to correct a mistake.
- Create a new version or mark the faulty version invalid for future calculations.
- Preserve the historical calculation trace.
- Recalculate current recommendations under the corrected version.
- Clearly identify results affected by a material correction.

## 5.11 Module K — Notifications and Reminders

### MVP
- User-entered reminder date and label.
- In-app reminder list.
- Time zone stored explicitly.
- Reminder can be edited, dismissed, or deleted.

### Later
- Email or push notifications through a configured provider.
- Opt-in and opt-out.
- Retry policy and delivery log.
- Quiet hours and notification preferences.
- No sensitive card or spending details in notification previews by default.

## 5.12 Module L — Import, Export, and Deletion

### MVP export
- Export card portfolio references.
- Export scenario inputs and outputs.
- Export calculation traces.
- Export saved preferences.
- Exclude authentication secrets and sensitive internal data.

### Future CSV import
- Preview and validate before committing.
- Map columns explicitly.
- Reject or quarantine malformed rows.
- Do not treat a merchant description as authoritative merchant category data.
- Let the user correct category/channel mappings.
- Avoid retaining raw imported files longer than necessary.
- Never upload statements to an external model provider without explicit consent and a clear data policy.

### Deletion
- Delete user-owned rows and uploaded files according to the retention policy.
- Handle backups according to documented backup expiry.
- Explain what may remain temporarily in backups or legally required audit records.
- Verify that deleted user resources are no longer accessible through APIs.
- Do not promise instant removal from immutable backups if the architecture cannot provide it.

---

# 6. User Journeys and Screen-Level Requirements

## 6.1 First-time onboarding
1. Explain what the app does and does not do.
2. Show privacy and data-use summary.
3. Let the user select a market and currency.
4. Ask whether they want to enter cards, explore the catalogue, or use a demo.
5. Allow skipping optional fields.
6. Do not request full card numbers, CVVs, PINs, or issuer passwords.

**Acceptance:** user can reach the catalogue without providing sensitive payment credentials.

## 6.2 Add an existing card
1. Search issuer/product.
2. Choose exact variant.
3. Show verification state and last-verified date.
4. User confirms that the variant matches their card.
5. Store the internal card reference, not payment credentials.
6. If no exact variant exists, allow a request for research rather than inventing a match.

## 6.3 Enter spending
1. Choose monthly scenario.
2. Enter amounts by category.
3. Optionally split by channel.
4. Mark uncertain categories.
5. Set current allocation or ask the optimizer to propose one.
6. Save scenario.
7. Display any missing fields that could materially change results.

## 6.4 Compare cards
1. Select scenario.
2. Select cards.
3. Choose points valuation if applicable.
4. Review calculation summary.
5. Expand a card result to see rates, exclusions, caps, and fees.
6. Open sources from each material claim.
7. Compare estimates and uncertainty.

## 6.5 Optimize allocation
1. Select the cards already owned.
2. Select baseline allocation.
3. Set fixed/flexible buckets and card constraints.
4. Confirm cap-consumption assumptions.
5. Run optimization.
6. Review incremental value and all material assumptions.
7. Save the proposed allocation as a new scenario without overwriting the baseline.

## 6.6 Ask the AI assistant
1. User asks a question.
2. App identifies the relevant card/variant if possible.
3. Retrieve applicable verified sources.
4. If identity is ambiguous, ask a clarifying question.
5. Answer with citations and dates.
6. If evidence is insufficient, say what is missing.
7. Never silently convert an AI explanation into a published rule.

## 6.7 Correct a rule
1. User/editor flags an issue.
2. System records the claim and evidence.
3. Editor drafts a corrected version.
4. Tests run against the draft.
5. Reviewer checks source, dates, and expected behavior.
6. Approved version is published.
7. Affected calculations are marked for refresh.

---

# 7. Technical Architecture

## 7.1 Recommended initial architecture

Use a **modular monolith** with clear package boundaries. This reduces deployment complexity while keeping the system separable if scale later requires it.

```text
Web Client (React + TypeScript)
          |
          | HTTPS / JSON
          v
API Layer (FastAPI)
  |       |         |         |
  |       |         |         +--> Auth / User Workspace
  |       |         +------------> Catalogue / Evidence API
  |       +----------------------> Scenario / Optimizer API
  +------------------------------> Calculation API
                                      |
                                      v
                              Rules Engine (pure logic)
                                      |
                    +-----------------+----------------+
                    |                                  |
                    v                                  v
             PostgreSQL                         Calculation Trace
                    |
                    v
           Rule Review / Audit

Optional AI subsystem:
Source Ingestion -> Text Extraction -> Chunking -> Search Index
                                         |
User Question -> Retrieval -> Evidence Filter -> LLM -> Citation Validator
                                         |
                                  Answer + Evidence
```

## 7.2 Architectural boundaries
- **Frontend:** presentation, input validation for usability, visualization.
- **API:** authentication, authorization, request validation, orchestration.
- **Domain layer:** card, rule, scenario, reward, and optimizer models.
- **Rules engine:** deterministic, side-effect-free calculations.
- **Repository layer:** database access.
- **Evidence service:** source metadata, excerpts, and provenance.
- **AI service:** retrieval and explanation only.
- **Notification service:** scheduling and delivery.
- **Audit service:** immutable-style append-only business events.
- **Admin service:** rule workflow and review gates.

## 7.3 Why not microservices immediately?
The MVP does not require separate deployment units for every module. A modular monolith is easier to test, deploy, and operate. Keep interfaces clean so a background worker, search service, or notification service can be separated later if actual workload justifies it.

## 7.4 Suggested stack

### Frontend
- React.
- TypeScript.
- Vite or a comparable maintained build system.
- Accessible component system.
- TanStack Query or equivalent for server state.
- React Hook Form or equivalent for forms.
- Zod or equivalent for client-side schema validation.
- A charting library only where comparisons benefit from visualization.

### Backend
- Python 3.12+ or the currently supported stable version chosen at project start.
- FastAPI.
- Pydantic for request/domain schema validation.
- SQLAlchemy 2.x or a comparable maintained ORM.
- Alembic for database migrations.
- PostgreSQL for shared deployment.
- SQLite may be used for local tests or a single-user prototype, but production concurrency and migration behavior must be evaluated.

### Calculations
- Python `Decimal` for monetary arithmetic.
- Pure functions for individual rule evaluators.
- Explicit rule schemas and versioned fixtures.
- Property-based testing for caps, boundaries, and rounding.

### AI and search
- PostgreSQL full-text search for the first release.
- Optional `pgvector` if evaluation supports semantic retrieval.
- Optional local inference via Ollama or llama.cpp.
- A provider abstraction to prevent business logic from depending on one model.
- AI model and prompt versions recorded for evaluation and debugging.

### Testing and quality
- pytest.
- Hypothesis for property-based tests.
- HTTP/API integration tests.
- Playwright for end-to-end tests.
- Ruff or equivalent linting.
- Mypy or pyright for type checking.
- Pre-commit hooks.
- Dependency and secret scanning in CI.

### Operations
- Docker.
- Docker Compose for local development.
- A reverse proxy or managed TLS endpoint.
- Structured application logs.
- Error monitoring.
- Database backups.
- CI/CD pipeline with migration and rollback procedures.

**Dependency policy:** pin tested versions in lockfiles. Verify current compatibility at implementation time rather than blindly copying version numbers from this plan.

---

# 8. Repository Structure

```text
cardwise-ai/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── PRIVACY.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── RULE_SCHEMA.md
│   ├── API_SPEC.md
│   ├── SECURITY_THREAT_MODEL.md
│   ├── TEST_PLAN.md
│   ├── DEPLOYMENT.md
│   ├── OPERATIONS_RUNBOOK.md
│   └── ADR/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── catalogue/
│   │   │   ├── portfolio/
│   │   │   ├── spending/
│   │   │   ├── comparison/
│   │   │   ├── optimizer/
│   │   │   ├── assistant/
│   │   │   └── settings/
│   │   ├── api/
│   │   ├── schemas/
│   │   └── tests/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   └── errors.py
│   │   ├── domain/
│   │   │   ├── cards/
│   │   │   ├── rules/
│   │   │   ├── spending/
│   │   │   ├── rewards/
│   │   │   ├── optimizer/
│   │   │   └── evidence/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── db/
│   │   ├── ai/
│   │   ├── notifications/
│   │   └── audit/
│   ├── migrations/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   ├── property/
│   │   └── fixtures/
│   └── pyproject.toml
├── rule-data/
│   ├── schemas/
│   ├── drafts/
│   ├── verified/
│   └── fixtures/
└── scripts/
    ├── validate_rule_data.py
    ├── import_sources.py
    └── check_rule_freshness.py
```

Do not store production secrets or private user data in the repository. Rule data committed to source control must have redistribution rights and a review process.

---

# 9. Data Model and Database Design

The following is a logical schema. Exact SQL types and indexes should be decided during implementation.

## 9.1 `users`
- `id`: UUID primary key.
- `email_normalized`: unique normalized email if email authentication is used.
- `password_hash`: nullable when using external identity provider.
- `role`: user/admin role or relation to role assignments.
- `status`: active, disabled, deletion_pending, deleted.
- `created_at`, `updated_at`, `last_login_at`.
- `timezone`.
- `preferred_currency`.
- Do not store raw authentication tokens or plaintext passwords.

## 9.2 `issuers`
- `id`.
- `name`.
- `country_code`.
- `official_domain`.
- `status`.
- `created_at`, `updated_at`.

## 9.3 `cards`
Represents a product family or market-level card identity.
- `id`.
- `issuer_id`.
- `product_family`.
- `market`.
- `currency`.
- `status`.
- `created_at`, `updated_at`.

## 9.4 `card_variants`
- `id`.
- `card_id`.
- `display_name`.
- `network`.
- `variant_code` where applicable.
- `co_brand` where applicable.
- `valid_from`, `valid_to`.
- `status`.
- `identity_notes`.
- Unique constraints should prevent accidental duplicate variants while allowing legitimate historical variants.

## 9.5 `sources`
- `id`.
- `issuer_id` nullable for general program sources.
- `source_type`.
- `title`.
- `canonical_url` or official document identifier.
- `published_at` nullable.
- `retrieved_at`.
- `effective_from`, `effective_to` nullable.
- `content_hash`.
- `status`.
- `redistribution_permission_status`.
- `created_by`.
- `created_at`.

## 9.6 `source_excerpts`
- `id`.
- `source_id`.
- `page_number` nullable.
- `section_heading` nullable.
- `excerpt_text`.
- `excerpt_hash`.
- `locator`.
- `created_at`.

Store only the excerpts necessary to support rules, subject to source terms and copyright policy.

## 9.7 `rules`
- `id`.
- `card_variant_id`.
- `rule_type`.
- `schema_version`.
- `parameters_json`.
- `conditions_json`.
- `priority`.
- `effective_from`.
- `effective_to` nullable.
- `verification_status`.
- `review_status`.
- `supersedes_rule_id` nullable.
- `created_by`.
- `reviewed_by` nullable.
- `created_at`, `updated_at`, `published_at` nullable.
- `rule_hash`.

Validate JSON against a strict versioned schema before saving or publishing. Do not accept arbitrary executable expressions or user-provided code as rule logic.

## 9.8 `rule_evidence`
- `rule_id`.
- `source_excerpt_id`.
- `evidence_role`: supports, qualifies, contradicts, or contextualizes.
- `notes`.
- Composite key or unique constraint to avoid duplicate links.

## 9.9 `rule_test_cases`
- `id`.
- `rule_id`.
- `case_name`.
- `input_json`.
- `expected_json`.
- `test_type`.
- `created_at`.
- Tests should be versioned with the rule candidate and run before publication.

## 9.10 `rule_reviews`
- `id`.
- `rule_id`.
- `reviewer_id`.
- `decision`: approved, rejected, changes_requested.
- `comment`.
- `created_at`.

## 9.11 `user_cards`
- `id`.
- `user_id`.
- `card_variant_id`.
- `nickname` optional.
- `acquired_at` optional.
- `status`: active, inactive, closed, unknown.
- `created_at`, `updated_at`.
- Never include PAN, CVV, PIN, or issuer login credentials.

## 9.12 `spending_profiles`
- `id`.
- `user_id`.
- `name`.
- `currency`.
- `period_type`.
- `created_at`, `updated_at`.

## 9.13 `scenarios`
- `id`.
- `user_id`.
- `spending_profile_id`.
- `name`.
- `scenario_date`.
- `currency`.
- `rule_set_version` or calculation manifest reference.
- `status`.
- `created_at`, `updated_at`.

## 9.14 `scenario_spend`
- `id`.
- `scenario_id`.
- `category_code`.
- `channel_code`.
- `amount_decimal`.
- `transaction_count` nullable.
- `average_ticket_amount` nullable.
- `classification_confidence` nullable.
- `is_fixed_allocation`.
- `notes` optional.
- Use database numeric/decimal types, not floating-point types.

## 9.15 `scenario_allocations`
- `id`.
- `scenario_id`.
- `scenario_spend_id`.
- `card_variant_id`.
- `allocated_amount_decimal`.
- `allocation_type`: baseline, proposed, manual.
- `created_at`.

## 9.16 `cap_usage_assumptions`
- `id`.
- `scenario_id`.
- `rule_id`.
- `period_start`.
- `period_end`.
- `consumed_amount_decimal` nullable.
- `knowledge_state`: known, estimated, unknown.
- `notes`.

## 9.17 `valuation_profiles`
- `id`.
- `user_id` nullable for system defaults.
- `name`.
- `currency`.
- `created_at`.

## 9.18 `point_valuations`
- `id`.
- `valuation_profile_id`.
- `program_code`.
- `value_per_point_decimal`.
- `valid_from`.
- `valid_to` nullable.
- `source_id` nullable if user assumption.
- `valuation_kind`: user_assumption, source_backed, scenario_low, scenario_base, scenario_high.
- `notes`.

## 9.19 `calculation_runs`
- `id`.
- `user_id` nullable for controlled internal tests.
- `scenario_id`.
- `scenario_revision_hash`.
- `engine_version`.
- `rule_manifest_json`.
- `input_snapshot_json`.
- `result_json`.
- `result_hash`.
- `status`.
- `created_at`.

The snapshot must include enough information to reproduce the result without requiring current mutable card rules.

## 9.20 `calculation_trace_steps`
- `id`.
- `calculation_run_id`.
- `sequence_number`.
- `rule_id` nullable.
- `step_type`.
- `input_json`.
- `output_json`.
- `explanation_code`.
- `evidence_ids_json`.
- `created_at`.

## 9.21 `reminders`
- `id`.
- `user_id`.
- `card_variant_id` nullable.
- `label`.
- `due_at`.
- `timezone`.
- `status`.
- `notification_channel`.
- `created_at`, `updated_at`.

## 9.22 `audit_events`
- `id`.
- `actor_id` nullable for system events.
- `action`.
- `entity_type`.
- `entity_id`.
- `before_hash` nullable.
- `after_hash` nullable.
- `metadata_json` with sensitive values excluded.
- `created_at`.

Audit records should be append-only at the application level and protected against unauthorized modification.

## 9.23 `assistant_sessions` and `assistant_messages` (optional V1)
- Store only what is needed to provide the service.
- Give users a clear retention/deletion policy.
- Avoid retaining raw uploaded statements or sensitive prompts by default.
- Store model and prompt versions for evaluation.
- Store citation IDs separately from generated prose.

## 9.24 Data retention
Define retention by data class:
- User account data.
- Scenario and calculation data.
- Source text and excerpts.
- Audit events.
- AI chat history.
- Uploaded imports.
- Operational logs.
- Backups.

Retention must be configurable and documented. Logs must not contain raw financial records or secrets.

---

# 10. Rule Schema and Example Data

## 10.1 Illustrative rule object

The following is a conceptual example only. It describes fictional terms and must not be copied into a real card record.

```json
{
  "schema_version": 1,
  "rule_id": "synthetic-card-online-cashback-v1",
  "card_variant_id": "synthetic-card-variant",
  "rule_type": "cashback_rate",
  "parameters": {
    "rate_percent": "5.0",
    "cap_amount": "500.00",
    "cap_period": "calendar_month",
    "eligible_categories": ["online_shopping"],
    "eligible_channels": ["online_card"],
    "excluded_transaction_types": ["synthetic_exclusion"]
  },
  "effective_from": "2026-01-01",
  "effective_to": null,
  "verification_status": "draft",
  "evidence_ids": [],
  "notes": "Synthetic test fixture; not an issuer offer."
}
```

## 10.2 Validation rules
- Reject unknown rule types.
- Reject unknown fields unless the schema explicitly allows extensions.
- Validate dates and ensure effective-to is not before effective-from.
- Validate rate bounds and cap units.
- Validate currency and period enums.
- Validate that referenced card variants and evidence IDs exist.
- Reject executable strings, SQL, Python expressions, or arbitrary formulas.
- Reject a production publication if required evidence is absent.
- Warn on overlapping active rules with conflicting parameters.
- Require a migration strategy when schema versions change.

## 10.3 Rule engine interface
Conceptual Python interfaces:

```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Protocol

@dataclass(frozen=True)
class RewardInput:
    card_variant_id: str
    spend_amount: Decimal
    currency: str
    category_code: str
    channel_code: str
    transaction_date: date
    prior_cap_usage: Decimal | None

@dataclass(frozen=True)
class RewardResult:
    eligible_spend: Decimal
    excluded_spend: Decimal
    reward_amount: Decimal | None
    reward_unit: str
    status: str
    warnings: tuple[str, ...]
    trace: tuple[dict, ...]

class RuleEvaluator(Protocol):
    def evaluate(self, request: RewardInput, rules: tuple[dict, ...]) -> RewardResult:
        ...
```

This interface is illustrative. Production types should be stricter than untyped dictionaries and should use validated domain models.

---

# 11. Calculation Semantics and Edge Cases

## 11.1 Cap semantics
A cap can apply to:
- Cashback amount.
- Points earned.
- Eligible spend.
- Number of transactions.
- A particular category.
- A particular channel.
- A statement period.
- A calendar month.
- A quarter or year.
- A combined set of reward categories.

Never assume all caps are monthly or card-wide. The rule schema must explicitly define the cap unit, reset period, scope, and whether other benefits share the cap.

## 11.2 Cap consumption
- If prior usage is known, calculate remaining cap.
- If prior usage is unknown, show a conditional estimate or range.
- Do not treat unknown usage as zero without a clear, user-selected assumption.
- If the issuer's cap reset date is unknown, disclose the limitation.

## 11.3 Exclusions
An exclusion should return:
- Excluded amount.
- Reason code.
- Human-readable reason.
- Rule/evidence references.
- Whether the exclusion is confirmed or uncertain.

An exclusion must not simply remove spend without leaving a trace.

## 11.4 Refunds and reversals
Where issuer terms are known:
- Model how refunds affect rewards.
- Avoid double-counting a refund as negative spend and a separate reward reversal.
- Preserve transaction linkage only if transaction-level imports are implemented.
- If the reversal policy is unknown, disclose that the scenario does not model it.

## 11.5 Fees
Distinguish:
- Joining fee.
- Annual fee.
- Fee waiver.
- Taxes or other charges where verified.
- Transaction fees.
- Opportunity cost of using one card instead of another.
- User-specific fee already paid versus a future fee under consideration.

Do not subtract the full annual fee from every monthly category comparison. Provide a clear allocation method:
- Monthly amortization for a monthly scenario.
- Annual portfolio view.
- Incremental fee only for an add/remove-card comparison.
- User-selected allocation when a fee applies to a broader portfolio.

## 11.6 Point valuations
- Points are not cash unless a reliable redemption path supports that value.
- Store valuation as an assumption with source and date where possible.
- Show multiple values for uncertain redemption options.
- Include redemption restrictions and minimums when known.
- Do not assume all points can be redeemed at the best advertised value.
- Distinguish issuer conversion ratio from the estimated monetary value of a point.

## 11.7 Thresholds and milestones
- Model qualifying spend separately from general spend.
- Define period start/end.
- Specify whether returns, refunds, EMI, fees, or excluded transactions count if terms say so.
- If qualifying spend is not known, show a conditional result.
- Do not recommend additional spend as a default strategy.
- If showing a threshold gap, display the required additional spend and the benefit's estimated value separately, with a debt/spending caution.

## 11.8 Overlapping rules
Use an explicit precedence model. Example ordering may include hard exclusions before earning rules, but the actual order must be defined by the rule type and source terms. Do not rely on database row order.

## 11.9 Rounding
- Use Decimal.
- Define rounding mode.
- Keep intermediate precision.
- Apply rounding at the documented step.
- Add tests for half-cent and reward-unit boundaries.
- If the issuer does not disclose rounding behavior, mark the result as an estimate and document the chosen simulation assumption.

## 11.10 Unknown or contradictory rules
Possible result statuses:
- `verified_estimate`
- `estimated`
- `partial`
- `needs_input`
- `cannot_calculate`
- `stale_rules`
- `conflicting_rules`
- `ineligible`
- `excluded`

The API and UI must not collapse all these statuses into a single numeric result.

---

# 12. API Specification

All endpoints should use a versioned prefix such as `/api/v1`. Exact response schemas must be defined with Pydantic models and documented in OpenAPI.

## 12.1 Authentication and profile
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/password-reset/request` (if password auth is used)
- `POST /auth/password-reset/confirm`
- `GET /me`
- `PATCH /me/preferences`
- `DELETE /me`

Use a trusted identity provider if that materially reduces security risk and maintenance burden.

## 12.2 Catalogue
- `GET /issuers`
- `GET /cards`
- `GET /cards/{card_id}`
- `GET /card-variants/{variant_id}`
- `GET /card-variants/{variant_id}/rules`
- `GET /card-variants/{variant_id}/sources`
- `GET /card-variants/{variant_id}/history` (authorized scope)

Filters may include issuer, market, network, status, and verification state. Do not expose private editorial drafts to ordinary users.

## 12.3 User portfolio
- `GET /me/cards`
- `POST /me/cards`
- `PATCH /me/cards/{user_card_id}`
- `DELETE /me/cards/{user_card_id}`

## 12.4 Spending and scenarios
- `GET /me/scenarios`
- `POST /me/scenarios`
- `GET /me/scenarios/{scenario_id}`
- `PATCH /me/scenarios/{scenario_id}`
- `POST /me/scenarios/{scenario_id}/duplicate`
- `DELETE /me/scenarios/{scenario_id}`
- `PUT /me/scenarios/{scenario_id}/spend`
- `PUT /me/scenarios/{scenario_id}/allocations`

Every endpoint must enforce ownership and validate category/channel codes.

## 12.5 Calculation
- `POST /calculations/estimate`
- `POST /calculations/compare`
- `POST /scenarios/{scenario_id}/calculate`
- `GET /calculations/{calculation_id}`
- `GET /calculations/{calculation_id}/trace`

The calculation request must identify the scenario date, selected cards, currency, assumptions, and rule version policy. The server must not trust a client-supplied reward result.

## 12.6 Optimizer
- `POST /optimizer/run`
- `GET /optimizer/runs/{run_id}`
- `GET /optimizer/runs/{run_id}/trace`

The response must include objective value, baseline, proposed allocation, constraints, assumptions, solver/method version, and warnings.

## 12.7 AI assistant
- `POST /assistant/ask`
- `GET /assistant/sessions`
- `GET /assistant/sessions/{session_id}`
- `DELETE /assistant/sessions/{session_id}`

Assistant output should contain answer text, evidence citations, source dates, uncertainty flags, and the model/prompt version used. It must not be treated as a rules-engine result.

## 12.8 Admin and rule review
- `POST /admin/sources`
- `POST /admin/rules`
- `PATCH /admin/rules/{rule_id}`
- `POST /admin/rules/{rule_id}/validate`
- `POST /admin/rules/{rule_id}/submit-review`
- `POST /admin/rules/{rule_id}/approve`
- `POST /admin/rules/{rule_id}/reject`
- `POST /admin/rules/{rule_id}/publish`
- `GET /admin/review-queue`
- `GET /admin/audit-events`

Require role checks and audit logging. A client must not be able to publish a rule merely by calling the endpoint directly.

## 12.9 Reminders
- `GET /me/reminders`
- `POST /me/reminders`
- `PATCH /me/reminders/{reminder_id}`
- `DELETE /me/reminders/{reminder_id}`

## 12.10 Export
- `POST /me/exports`
- `GET /me/exports/{export_id}`
- `DELETE /me/exports/{export_id}`

Exports should expire after a configured period. Avoid long-lived public links.

## 12.11 Standard error format
Use a consistent machine-readable format:
- `code`
- `message`
- `request_id`
- `field_errors` when relevant
- `retryable`
- `documentation_reference` where useful

Do not return stack traces, secrets, SQL errors, internal file paths, or raw provider errors to clients.

---

# 13. Frontend Information Architecture

## 13.1 Main navigation
- Dashboard.
- My Cards.
- Card Catalogue.
- Spending Scenarios.
- Compare Cards.
- Optimize Portfolio.
- Benefits & Reminders.
- Terms Assistant.
- Settings & Privacy.

Admin navigation is role-gated and separate.

## 13.2 Dashboard
Display:
- Number of cards in portfolio.
- Latest scenario and its date.
- Estimated rewards under current assumptions.
- Potential improvement from a proposed allocation.
- Upcoming reminders.
- Stale or uncertain rule notices affecting the user's saved scenarios.

Do not show a precise “you saved ₹X” claim if the result is only an estimate. Use “estimated reward value” and show assumptions.

## 13.3 Card detail page
Sections:
1. Identity and variant.
2. Verification status.
3. Fees.
4. Earn rules.
5. Caps.
6. Exclusions.
7. Thresholds and milestones.
8. Non-cash benefits.
9. Source documents.
10. Change history.
11. Add to portfolio action.

## 13.4 Scenario editor
- Category/channel rows.
- Currency.
- Period.
- Optional transaction count.
- Current card allocation.
- Unknown/missing-data markers.
- Save and duplicate.
- Validation errors beside fields.
- Clear indication of assumptions.

## 13.5 Comparison screen
- Side-by-side results.
- Gross rewards and net estimated value.
- Fees included.
- Cap utilization.
- Excluded categories.
- Points valuation.
- Verification state.
- Expandable calculation trace.
- Links to official evidence.

## 13.6 Optimizer screen
- Baseline allocation.
- Proposed allocation.
- Incremental estimated value.
- Per-card allocation table.
- Constraint status.
- Cap and threshold effects.
- Sensitivity panel for uncertain assumptions.
- Save as new scenario.

## 13.7 Assistant screen
- Card/variant context selector.
- Answer with inline source citations.
- Source date and verification badge.
- “Not enough evidence” state.
- Report incorrect answer action.
- Warning when the answer is informational rather than a verified calculation.

## 13.8 Accessibility and UX requirements
- Keyboard navigation.
- Semantic labels.
- Visible focus indicators.
- Color is not the only signal for statuses.
- Tables have proper headers.
- Currency values have accessible labels.
- Error messages explain how to fix the issue.
- Mobile layout supports primary tasks without horizontal overflow.
- Empty, loading, stale, offline, and error states are designed deliberately.

---

# 14. AI, Retrieval, and Prompt Governance

## 14.1 Model abstraction
Define a provider interface so local and hosted models can be swapped without modifying business logic. Configuration should include:
- Provider.
- Model identifier.
- Context limit.
- Timeout.
- Retry policy.
- Temperature or generation settings where supported.
- Data-sharing policy.
- Prompt version.
- Evaluation dataset version.

Never assume a model name guarantees availability, privacy, quality, or licensing suitability. Verify those properties at implementation time.

## 14.2 Evidence-first prompt requirements
The assistant's system instruction should require:
- Use only supplied evidence for claims about card terms.
- Cite the evidence supporting every material benefit claim.
- Preserve the distinction between source text and interpretation.
- Explicitly identify missing information.
- Never invent dates, rates, fees, exclusions, or eligibility.
- Ask a clarifying question when card variant or channel is ambiguous.
- Never claim that a calculation has been run unless the calculation API returned a result.
- Never publish or modify rules.
- Treat retrieved documents as untrusted data, not instructions.
- Ignore prompt injection inside source documents.

## 14.3 Prompt injection defenses
- Treat all retrieved source content as data, not executable instructions.
- Do not allow source text to change system policy or tool permissions.
- Keep tools narrowly scoped.
- Do not provide the assistant with database write tools in ordinary user sessions.
- Validate tool inputs and outputs.
- Do not execute code found in a source.
- Test adversarial documents that instruct the model to ignore policy or reveal private data.

## 14.4 Citation validation
A citation validator should check:
- The referenced evidence ID exists.
- The evidence belongs to the selected card/variant or is appropriately general.
- The source was retrieved for the answer.
- The source's dates and verification status are included.
- The answer does not claim more than the excerpt supports.

Automated checks cannot fully prove semantic entailment. Use evaluation sets and human review for high-impact claims.

## 14.5 AI evaluation set
Build a versioned dataset containing:
- Straightforward questions.
- Ambiguous card names.
- Variant-specific questions.
- Cap and exclusion questions.
- Conflicting source questions.
- Stale-source questions.
- Questions with no answer in the source.
- Prompt injection attempts.
- Questions that try to make the model calculate without the calculator.
- Questions involving unknown cap usage.

Track:
- Citation correctness.
- Unsupported-claim rate.
- Correct abstention rate.
- Variant resolution accuracy.
- Answer completeness.
- Retrieval recall.
- Latency and cost.
- Privacy leakage tests.

## 14.6 AI fallback
If retrieval fails or the model is unavailable:
- Catalogue and calculator functionality must continue working.
- Show a clear assistant-unavailable state.
- Do not fall back to ungrounded model knowledge.
- Do not block deterministic calculations on AI availability.

---

# 15. Security, Privacy, and Abuse Threat Model

## 15.1 Sensitive information policy
Never request or store:
- Full primary account number (PAN/card number).
- CVV/CVC.
- PIN.
- Issuer account password.
- OTP.
- Full authentication secrets.
- Unnecessary identity documents.

If a future feature imports statements, minimize retained raw data, obtain consent, restrict access, and document deletion behavior.

## 15.2 Threats and controls

### Broken access control
- Enforce authorization in the service layer.
- Test cross-user resource access.
- Use unguessable IDs but do not treat them as authorization.
- Restrict admin endpoints by role.

### Account takeover
- Use secure password hashing or a trusted identity provider.
- Rate-limit authentication.
- Use secure sessions and reset flows.
- Monitor suspicious login patterns without logging secrets.

### Prompt injection
- Treat retrieved documents as untrusted.
- Keep AI tools read-only for user sessions.
- Validate citations and outputs.
- Test malicious source content.

### Rule poisoning
- Require evidence and independent review.
- Keep audit events.
- Validate rule schemas.
- Run regression tests.
- Prevent ordinary users from publishing rules.

### Data leakage
- Minimize logs.
- Redact personal data.
- Restrict exports.
- Set retention periods.
- Encrypt traffic and use appropriate storage encryption.
- Review model-provider data handling before sending content.

### Supply-chain risk
- Pin dependencies.
- Scan vulnerabilities.
- Review package provenance.
- Keep secrets out of source control.
- Use least-privilege CI credentials.

### Abuse and scraping
- Respect source terms, rate limits, robots directives where applicable, and access controls.
- Prefer official APIs, feeds, or manually reviewed documents.
- Do not bypass authentication or anti-bot protections.

## 15.3 Privacy-by-design checklist
- Collect the minimum data.
- Explain the purpose of each optional field.
- Allow scenario deletion.
- Avoid using user spending data to train models by default.
- Do not send user data to a model provider unless the selected provider and data policy permit it and the user is informed.
- Separate production data from test fixtures.
- Use synthetic data in CI.
- Document backups and deletion limitations.

## 15.4 Compliance work
Before public launch, obtain qualified review of applicable Indian privacy, consumer-protection, advertising, financial-services, data-retention, and source-licensing obligations. This document is not legal advice and does not claim that a particular compliance review has already occurred.

---

# 16. Testing Strategy

## 16.1 Unit tests
Test each rule evaluator in isolation:
- Eligible and ineligible categories.
- Channel matching.
- Effective-date boundaries.
- Zero spend.
- Negative or invalid inputs.
- Caps just below, exactly at, and above the limit.
- Prior cap usage known and unknown.
- Point conversion.
- Fee allocation.
- Exclusions.
- Rounding.
- Overlapping rules.
- Missing evidence.
- Conflicting rules.
- Historical scenarios.

## 16.2 Property-based tests
Examples of invariants:
- Estimated cashback never exceeds an applicable cashback cap.
- Excluded spend does not earn the excluded reward.
- Increasing eligible spend cannot reduce gross reward under a simple uncapped fixed-rate rule.
- Allocated spend totals equal planned spend for each bucket when the optimizer claims a complete allocation.
- The same input snapshot, rule manifest, and engine version yield the same result.
- A result never references a rule outside its effective period.
- Missing cap usage cannot be silently converted into a known zero.
- Net value equals the documented gross-value-minus-cost formula under the selected fee policy.

These properties must be adjusted for legitimate tiered rules, thresholds, and reversal rules.

## 16.3 Integration tests
- Database persistence and retrieval.
- Rule publication gate.
- Scenario calculation.
- Authorization checks.
- Source citation retrieval.
- Export generation and expiry.
- Reminder creation.
- Migration from an empty database.
- Migration from the previous release schema.

## 16.4 Contract tests
- API request and response schemas.
- Frontend/backend validation agreement.
- Rule schema compatibility.
- AI provider abstraction behavior.
- External notification provider failure behavior.

## 16.5 End-to-end tests
1. Register or sign in.
2. Add a verified synthetic card.
3. Enter a spending scenario.
4. Compare two cards.
5. Inspect a calculation trace.
6. Ask a source-grounded question.
7. Create a reminder.
8. Export and delete a scenario.
9. Confirm a user cannot access another user's scenario.
10. Confirm an unverified rule is not treated as verified.

## 16.6 Golden calculation suite
Maintain a reviewed suite of known inputs and expected outputs. Each change to calculation logic must run the suite. When issuer terms change, update the expected result only after the new source and rule have been reviewed.

## 16.7 Performance testing
Measure:
- Catalogue search latency.
- Calculation latency for common scenarios.
- Optimizer latency at realistic portfolio sizes.
- Database query count.
- Assistant retrieval and generation latency separately.
- API throughput and error rate under load.

Set numeric service-level objectives only after a baseline is measured. Do not claim “real-time” or “instant” without testing.

## 16.8 Release gates
A release is blocked if:
- Critical calculation tests fail.
- A published rule lacks required evidence.
- An authorization test fails.
- A migration cannot be tested.
- Secrets are detected in source control.
- The application logs sensitive data.
- An AI evaluation regression materially increases unsupported claims.
- Backup restoration has not been tested for the release's storage changes.

---

# 17. Observability and Operations

## 17.1 Structured logs
Include:
- Timestamp.
- Severity.
- Request ID.
- Endpoint or operation.
- Latency.
- Error code.
- Engine version where relevant.
- Rule manifest identifier where relevant.

Do not log:
- Passwords or tokens.
- Full card numbers.
- CVV/PIN/OTP.
- Raw uploaded statements.
- Unnecessary category-level financial details.
- Full prompts containing sensitive user information.

## 17.2 Metrics
- API request count and latency.
- Error rates.
- Calculation status distribution.
- `cannot_calculate` and `needs_review` rates.
- Rules awaiting review.
- Stale source count.
- Rule publication failures.
- Assistant citation-validation failure rate.
- Retrieval empty-result rate.
- Background job retries.
- Database connection saturation.

## 17.3 Health checks
- Liveness: process is alive.
- Readiness: required services are available.
- AI health: optional subsystem status; AI outage must not make the core calculator unhealthy.
- Database health: connection and basic query.
- Worker health: queue lag and recent heartbeat if workers are used.

## 17.4 Backup and recovery
- Define recovery point and recovery time objectives before production launch.
- Back up the database on a schedule appropriate to actual usage.
- Encrypt backups.
- Restrict backup access.
- Test restore to a clean environment.
- Document how to restore source metadata, rules, audit records, and user scenarios consistently.
- Version object storage content if source files are stored externally.

## 17.5 Incident response
Document procedures for:
- Incorrect published card rule.
- Incorrect recommendation caused by a calculation bug.
- Unauthorized data access.
- Leaked secret.
- Compromised admin account.
- Source licensing complaint.
- AI unsupported-claim incident.
- Database corruption.

For a materially incorrect rule, stop using the affected rule, preserve evidence, publish a correction through review, identify impacted calculations, and communicate the limitation clearly.

---

# 18. Deployment and Environments

## 18.1 Environments
- Local development.
- CI/test.
- Staging.
- Production.

Use separate credentials and databases. Never copy production user data into development by default.

## 18.2 Local development
- Docker Compose for database and supporting services.
- `.env.example` with placeholder values only.
- Seed data must be synthetic and visibly labeled.
- One documented command to start the backend and one to start the frontend.
- One documented command to run tests and linters.
- Database migration instructions.

## 18.3 Production deployment
- HTTPS only.
- Secure headers and appropriate CORS policy.
- Environment-based secrets management.
- Database not exposed directly to the public internet.
- Non-root containers where practical.
- Health checks.
- Controlled migrations.
- Backup verification.
- Error monitoring.
- Rate limiting.
- Rollback plan.

## 18.4 Configuration
Use typed configuration for:
- Environment.
- Database URL.
- Session/auth settings.
- Allowed origins.
- Logging level.
- AI provider/model.
- AI timeout.
- Feature flags.
- Data retention.
- Export expiry.
- Notification provider.
- Source freshness policy.

Fail fast on missing required production configuration. Never fall back to a development secret in production.

## 18.5 CI/CD pipeline
1. Check formatting and lint.
2. Run static type checks.
3. Run unit tests.
4. Run property-based and golden calculation tests.
5. Run integration tests against a temporary database.
6. Validate rule data and schemas.
7. Scan secrets and dependencies.
8. Build frontend and backend artifacts.
9. Deploy to staging.
10. Run smoke and end-to-end tests.
11. Require approval for production.
12. Run migrations safely.
13. Verify health and metrics.
14. Keep a rollback procedure available.

---

# 19. Implementation Backlog — Epics and Detailed Tasks

## Epic 0 — Repository and Engineering Foundations
- [ ] Create repository and documented branching/review strategy.
- [ ] Add README, license, security policy, privacy policy, contribution guide.
- [ ] Create frontend/backend project skeletons.
- [ ] Configure formatter, linter, type checker, test runner.
- [ ] Add environment configuration validation.
- [ ] Add Docker Compose for local development.
- [ ] Add CI pipeline.
- [ ] Add request IDs and structured logging.
- [ ] Add architecture decision record template.
- [ ] Add synthetic seed data.
- [ ] Verify that no secrets are committed.

**Definition of done:** a new developer can clone the repository, start the app, run tests, and understand the module boundaries.

## Epic 1 — Domain Models and Database
- [ ] Define card, variant, issuer, source, evidence, rule, scenario, and calculation models.
- [ ] Define strict schemas and enums.
- [ ] Implement database migrations.
- [ ] Add foreign keys and unique constraints.
- [ ] Add indexes for catalogue and rule lookups.
- [ ] Add repository interfaces.
- [ ] Add migration tests.
- [ ] Add synthetic fixtures.
- [ ] Document data retention.
- [ ] Test historical rule version retention.

**Definition of done:** schema constraints prevent invalid references and accidental duplicate variants.

## Epic 2 — Source Registry and Rule Workflow
- [ ] Create source record CRUD.
- [ ] Store source metadata and content hashes.
- [ ] Add evidence excerpt storage and locators.
- [ ] Implement draft rule creation.
- [ ] Validate rule schema.
- [ ] Attach evidence to rule.
- [ ] Add automated rule-test execution.
- [ ] Add reviewer approval/rejection.
- [ ] Prevent self-approval for material changes by default.
- [ ] Publish immutable version references.
- [ ] Record audit events.
- [ ] Add rollback/supersede workflow.
- [ ] Add stale-source queue.

**Definition of done:** no draft can affect production calculations, and publication is audited.

## Epic 3 — Catalogue APIs and UI
- [ ] Implement issuer and card search.
- [ ] Implement exact variant detail.
- [ ] Show fees, rates, caps, exclusions, and verification state.
- [ ] Show official source links.
- [ ] Show effective and verification dates.
- [ ] Add filters and pagination.
- [ ] Add empty/loading/error states.
- [ ] Add accessible mobile layout.
- [ ] Add variant identity tests.
- [ ] Ensure draft data is not exposed to ordinary users.

**Definition of done:** a user can identify a specific card variant and see what is known versus unknown.

## Epic 4 — Spending Profile and Scenario Builder
- [ ] Define configurable category and channel taxonomies.
- [ ] Build scenario create/edit/duplicate/delete APIs.
- [ ] Build category spend editor.
- [ ] Add currency and scenario date.
- [ ] Add fixed/flexible allocation flags.
- [ ] Add cap-usage assumption input.
- [ ] Distinguish zero, missing, and unknown.
- [ ] Add server-side validation.
- [ ] Add ownership/authorization tests.
- [ ] Add exportable scenario representation.

**Definition of done:** a user can build a complete scenario without providing sensitive card credentials.

## Epic 5 — Deterministic Calculation Engine
- [ ] Define calculation input/output domain types.
- [ ] Implement Decimal money handling.
- [ ] Implement rule selection by variant and date.
- [ ] Implement eligibility matching.
- [ ] Implement exclusion logic.
- [ ] Implement cashback rate rules.
- [ ] Implement points rules.
- [ ] Implement cap logic by supported period.
- [ ] Implement conversion profiles.
- [ ] Implement fee allocation methods.
- [ ] Implement uncertainty and conflict states.
- [ ] Implement calculation trace.
- [ ] Implement result reproducibility manifest.
- [ ] Add golden tests.
- [ ] Add property-based tests.
- [ ] Add tests for rounding and boundaries.

**Definition of done:** all supported rule types have deterministic, reviewed test fixtures and explainable outputs.

## Epic 6 — Comparison and Portfolio Optimizer
- [ ] Implement multi-card comparison API.
- [ ] Build side-by-side comparison UI.
- [ ] Define optimizer constraints.
- [ ] Implement baseline allocation calculation.
- [ ] Implement candidate allocation generation.
- [ ] Select and document the optimization method.
- [ ] Model caps and thresholds supported by the engine.
- [ ] Preserve total planned spend.
- [ ] Report infeasible constraints.
- [ ] Add sensitivity analysis for unknown cap usage and point valuation.
- [ ] Persist optimizer run manifest and trace.
- [ ] Add tests where greedy allocation fails.
- [ ] Add tests ensuring no spend inflation.

**Definition of done:** optimizer outputs are reproducible and explain why the recommended allocation wins under stated assumptions.

## Epic 7 — AI Terms Assistant
- [ ] Create source ingestion interface.
- [ ] Extract text and preserve source locators.
- [ ] Implement metadata-aware chunking.
- [ ] Implement full-text retrieval.
- [ ] Build a question-answering API.
- [ ] Enforce evidence-only prompting.
- [ ] Add citation validation.
- [ ] Add abstention behavior.
- [ ] Add source freshness display.
- [ ] Add prompt-injection tests.
- [ ] Add versioned evaluation set.
- [ ] Record model and prompt versions.
- [ ] Ensure core calculation works without AI.
- [ ] Add user feedback/reporting flow.

**Definition of done:** assistant answers cite relevant sources or clearly abstain; it never writes production rules.

## Epic 8 — Reminders, Export, and Privacy Controls
- [ ] Implement reminders CRUD.
- [ ] Implement time-zone-aware display.
- [ ] Implement user export.
- [ ] Set export expiry.
- [ ] Implement scenario deletion.
- [ ] Implement account deletion flow.
- [ ] Document backup retention behavior.
- [ ] Add privacy settings.
- [ ] Add deletion verification tests.
- [ ] Add notification opt-in controls before external delivery is added.

**Definition of done:** users can control their own stored data and understand what deletion means.

## Epic 9 — Security, Observability, and Release Readiness
- [ ] Run authorization tests across all user resources.
- [ ] Run dependency and secret scans.
- [ ] Review CORS and security headers.
- [ ] Configure production secrets.
- [ ] Configure metrics and error reporting.
- [ ] Add liveness/readiness checks.
- [ ] Create backup and restore runbook.
- [ ] Test restore.
- [ ] Write incident response procedures.
- [ ] Run load tests.
- [ ] Conduct accessibility checks.
- [ ] Verify source and data licensing.
- [ ] Complete release acceptance checklist.

**Definition of done:** production deployment can be operated, monitored, recovered, and rolled back by a documented process.

---

# 20. Suggested Eight-Week Delivery Plan

The schedule is a planning estimate, not a guarantee. Adjust based on team size, data verification workload, and review requirements.

## Week 1 — Foundations
- Repository setup.
- Domain model.
- Database migrations.
- CI and local development.
- Synthetic fixtures.
- Initial architecture decisions.

**Exit gate:** local app runs and automated tests execute in CI.

## Week 2 — Evidence and catalogue
- Source registry.
- Card and variant catalogue.
- Rule schema.
- Draft/review/publish workflow.
- Catalogue UI.

**Exit gate:** a verified synthetic card can be displayed with evidence and dates.

## Week 3 — Spending scenarios
- Spending categories/channels.
- Scenario CRUD.
- Portfolio selection.
- Unknown/missing-value handling.
- Scenario UI.

**Exit gate:** user can save and reload a scenario.

## Week 4 — Calculator
- Rule evaluator framework.
- Cashback and point rule types.
- Exclusions and caps.
- Fees and conversion assumptions.
- Trace output.
- Golden and property-based tests.

**Exit gate:** supported synthetic examples pass deterministic tests.

## Week 5 — Comparison and optimizer
- Multi-card comparison.
- Baseline and alternative allocation.
- Cap-aware optimizer.
- Sensitivity display.
- Explainability UI.

**Exit gate:** allocation preserves total spend and output is reproducible.

## Week 6 — RAG assistant and reminders
- Source ingestion.
- Retrieval.
- Citation-backed Q&A.
- Abstention and injection tests.
- Basic reminders.

**Exit gate:** assistant can answer supported questions and abstain on unsupported ones.

## Week 7 — Security and hardening
- Authorization review.
- Data export/deletion.
- Logging and monitoring.
- Performance testing.
- Accessibility review.
- Backup/restore drill.

**Exit gate:** no critical security or calculation issue remains open.

## Week 8 — Verified data, pilot, and release
- Research and independently review launch-card terms.
- Run regression suite.
- Pilot with synthetic and consenting test users.
- Fix usability issues.
- Complete runbooks and release notes.
- Deploy to production only after acceptance gates pass.

**Exit gate:** verified rule coverage, reproducible calculations, operational readiness, and clear limitation disclosures.

---

# 21. Example Calculation and Optimizer Walkthrough

All values in this section are fictional and for testing only.

Suppose a user has two cards:

- **Synthetic Card A:** 4% on eligible online shopping, monthly cashback cap ₹300.
- **Synthetic Card B:** 2% on eligible online shopping, monthly cashback cap ₹1,000.

User plans ₹20,000 of eligible online shopping and has no prior cap consumption.

Card A:
- Uncapped value: ₹20,000 × 4% = ₹800.
- Cap applies: estimated reward = ₹300.

Card B:
- Uncapped value: ₹20,000 × 2% = ₹400.
- Cap does not bind: estimated reward = ₹400.

Despite the lower headline rate, Card B produces the higher estimated cashback for this scenario. This illustrates why cap-aware calculations are essential.

A mixed allocation can also be evaluated:
- ₹7,500 to Card A yields ₹300 before cap.
- ₹12,500 to Card B yields ₹250.
- Combined estimated reward = ₹550, assuming the fictional terms permit this allocation and there are no transaction-level constraints.

The optimizer should compare feasible allocations and report the assumptions. It should not recommend extra purchases to reach the cap.

---

# 22. Sample API Contracts

These examples are illustrative and should be formalized with Pydantic models.

## 22.1 Calculation request

```json
{
  "scenario_date": "2026-10-01",
  "currency": "INR",
  "card_variant_ids": ["synthetic-card-a", "synthetic-card-b"],
  "spend": {
    "category": "online_shopping",
    "channel": "online_card",
    "amount": "20000.00"
  },
  "cap_usage": {
    "synthetic-card-a": {
      "state": "known",
      "amount": "0.00"
    },
    "synthetic-card-b": {
      "state": "unknown"
    }
  },
  "valuation_profile_id": null,
  "fee_method": "monthly_amortized",
  "rule_policy": "verified_only"
}
```

## 22.2 Calculation response

```json
{
  "calculation_id": "example-run-id",
  "status": "partial",
  "currency": "INR",
  "results": [
    {
      "card_variant_id": "synthetic-card-a",
      "gross_reward": "300.00",
      "reward_unit": "INR",
      "net_estimated_value": "300.00",
      "status": "verified_estimate",
      "warnings": [],
      "trace_ref": "example-trace-a"
    },
    {
      "card_variant_id": "synthetic-card-b",
      "gross_reward": null,
      "reward_unit": "INR",
      "net_estimated_value": null,
      "status": "needs_input",
      "warnings": [
        "Prior cap usage is unknown; provide an assumption or calculate a range."
      ],
      "trace_ref": "example-trace-b"
    }
  ],
  "engine_version": "example-version",
  "rule_manifest_id": "example-manifest"
}
```

The example intentionally shows how a missing cap assumption can prevent a confident numeric result. Production behavior may calculate a range when both minimum and maximum outcomes can be established from the rules.

---

# 23. Configuration and Environment Variables

Use a validated configuration object. Example names:

```text
APP_ENV
APP_BASE_URL
DATABASE_URL
AUTH_PROVIDER
SESSION_SECRET
ALLOWED_ORIGINS
LOG_LEVEL
AI_PROVIDER
AI_MODEL
AI_TIMEOUT_SECONDS
AI_MAX_RETRIES
AI_DATA_POLICY
SOURCE_FRESHNESS_DAYS
EXPORT_EXPIRY_HOURS
USER_DATA_RETENTION_DAYS
ENABLE_ASSISTANT
ENABLE_NOTIFICATIONS
NOTIFICATION_PROVIDER
```

Rules:
- `.env.example` contains placeholders only.
- Do not commit real values.
- Production startup fails when required secrets are missing.
- Never log secret values.
- Separate staging and production credentials.
- Feature flags must default to the safest behavior.

---

# 24. Product Copy and Disclosure Requirements

Use wording that reflects uncertainty accurately.

Preferred:
- “Estimated reward value.”
- “Based on the terms verified as of [date].”
- “This result assumes the monthly cap has not already been used.”
- “The issuer may apply transaction-specific conditions.”
- “We could not verify this rule from the available official source.”
- “Point value is your selected assumption, not a guaranteed cash value.”

Avoid:
- “Guaranteed cashback.”
- “You will definitely earn ₹X.”
- “Best card in India” without a defined comparison set and date.
- “Guaranteed lounge access.”
- “AI verified” as a substitute for actual source review.
- “Save ₹X” when the result is only a modeled estimate.

---

# 25. Definition of Done for Each Feature

A feature is done only when all applicable criteria are met:

1. Requirements and edge cases documented.
2. API schema defined and validated.
3. Authorization checked.
4. Data model and migration added.
5. Unit tests written.
6. Integration tests written where persistence or external systems are involved.
7. Error states designed.
8. Logs contain useful diagnostics but no sensitive values.
9. Accessibility reviewed for user-facing components.
10. Documentation updated.
11. Metrics or operational signals added where appropriate.
12. Failure behavior defined.
13. Security implications reviewed.
14. Rollback or recovery behavior documented for material data changes.

---

# 26. MVP Acceptance Checklist

## Product
- [ ] Users can create an account or use the configured safe demo mode.
- [ ] Users can search and inspect exact card variants.
- [ ] Verification state and source dates are visible.
- [ ] Users can save spending scenarios.
- [ ] Users can compare cards.
- [ ] Users can inspect calculation traces.
- [ ] Users can compare baseline and proposed allocations.
- [ ] Users can create and manage reminders.
- [ ] Users can export and delete their own data.
- [ ] Unknown and conflicting terms are clearly disclosed.

## Rules and calculations
- [ ] Every active material rule has required evidence.
- [ ] Rule dates are enforced.
- [ ] Cap behavior is tested at boundaries.
- [ ] Exclusions have explicit reason codes.
- [ ] Monetary calculations use decimal arithmetic.
- [ ] Rounding policy is documented.
- [ ] Point valuations are explicit assumptions.
- [ ] Fee allocation is transparent.
- [ ] Results can be reproduced from a stored manifest.
- [ ] Unverified rules cannot silently drive verified recommendations.

## AI
- [ ] Answers use retrieved evidence.
- [ ] Material claims cite sources.
- [ ] Unsupported questions trigger abstention.
- [ ] Prompt injection tests pass.
- [ ] The AI cannot publish rules.
- [ ] Calculator functionality works when the model is offline.
- [ ] Model/prompt versions are tracked for evaluation.

## Security and operations
- [ ] User ownership is enforced server-side.
- [ ] Sensitive card credentials are not accepted or stored.
- [ ] Secrets are not committed or logged.
- [ ] Dependency and secret scans pass.
- [ ] Backup and restore are tested.
- [ ] Production configuration is validated.
- [ ] Incident and rollback runbooks exist.
- [ ] Privacy and data-retention disclosures are available.

---

# 27. Key Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Issuer terms change | Incorrect estimates | Effective-dated rules, source monitoring, review queue |
| Card variants are confused | Wrong eligibility/rates | Exact variant identity and variant-resolution tests |
| Caps are modeled incorrectly | Inflated rewards | Typed cap scope/period and boundary tests |
| AI hallucinates terms | User misinformation | Evidence-first RAG, citation validation, abstention |
| Point value is overstated | Misleading comparison | User-selected and multi-scenario valuations |
| Unknown prior cap usage | False precision | Explicit unknown state and ranges |
| Optimizer misses a threshold interaction | Suboptimal allocation | Constraint model, scenario tests, method limitations |
| Source rights are unclear | Legal/operational risk | Source licensing review and minimum necessary excerpts |
| Personal data is over-collected | Privacy risk | Data minimization, retention policy, deletion controls |
| User assumes guarantee | Financial disappointment | Clear estimate language and source dates |
| AI provider becomes unavailable | Assistant outage | Separate optional subsystem; calculator remains available |
| Rules change without audit | Unreproducible results | Versioning, audit events, immutable calculation manifests |

---

# 28. Recommended Build Order

Do not start with autonomous agents or a complex multi-agent architecture. Build the product in this order:

1. **Domain model and source registry.**
2. **Exact card catalogue and variant identity.**
3. **Strict, versioned rule schema.**
4. **Human review and publication gates.**
5. **Deterministic calculator using synthetic fixtures.**
6. **Spending scenarios.**
7. **Comparison UI and trace visualization.**
8. **Portfolio optimizer with explicit constraints.**
9. **Verified real-card data set.**
10. **RAG assistant with citation and abstention tests.**
11. **Reminders, export, deletion, and privacy controls.**
12. **Security hardening, deployment, monitoring, and pilot.**

This sequence reduces the risk of building a polished AI interface on top of inaccurate data.

---

# 29. Open Decisions to Resolve Before Implementation

These are genuine product decisions, not assumptions to hide in code:

1. Is the initial release single-user/local-first or multi-user hosted?
2. Which exact issuer/card variants are in the launch catalogue?
3. Who verifies and approves card rules?
4. Which official sources may be stored or excerpted, and under what terms?
5. What is the source freshness policy for each source type?
6. Which categories and channels are required in MVP?
7. Which cap periods are supported in the first calculation release?
8. Is annual-fee allocation monthly, annual, or user-selectable?
9. Which point programs and valuation assumptions are included?
10. Is optimization limited to cards the user already owns?
11. Is RAG required for MVP or deferred to V1?
12. Will inference be local, hosted, or configurable?
13. What retention period applies to scenarios and assistant history?
14. What deployment target and budget are available?
15. Which notification channels are actually required?
16. What legal/privacy/source-licensing review is required before public launch?

**Recommended defaults:** multi-user-capable architecture; India-only launch; a small verified card catalogue; owned-card optimization first; deterministic calculation before AI; PostgreSQL; full-text retrieval before vector search; no bank connections; no sensitive card credentials; and human approval for all material rule changes.

---

# 30. Final Engineering Principle

CardWise AI succeeds when its outputs are explainable, reproducible, and honest about uncertainty. The catalogue, rule engine, and evidence workflow are the product's foundation. The AI assistant is a helpful interface over that foundation—not a replacement for it.

For every recommendation, the system should be able to answer:

- Which card variant was evaluated?
- Which rule version was applied?
- Which source supports that rule?
- What scenario inputs were used?
- Which caps, exclusions, and fees changed the result?
- Which assumptions were unknown?
- Can this result be reproduced?
- What would change if the assumptions changed?

If those questions cannot be answered, the product should lower its confidence, show a conditional estimate, or abstain.
