# CardWise AI — Implementation Audit & Gap Analysis

> Generated: 2026-10-29 | Baseline commit: c6679968 | Auditor: Antigravity

---

## GRAVITAS Policy Record
```json
{
  "planning": "deep",
  "context_depth": "full",
  "verification_depth": "impact",
  "delegation": "parallel-workstreams",
  "reason_codes": ["multi-phase", "financial-correctness", "security", "full-stack", "architecture"]
}
```

---

## 1. Quality Gates Comparison

| Gate | Baseline (Pre-Change) | Post-Remediation | Status |
|---|---|---|---|
| Backend tests | 14 passed in 2.57s | **46 passed in 3.13s** (32 new tests) | **PASS** |
| Backend ruff lint | Passed | **All checks passed!** | **PASS** |
| Frontend typecheck | Passed | **tsc --noEmit: 0 errors** | **PASS** |
| Frontend production build | Not run | **Vite build: 17 modules, 0 errors in 1.65s** | **PASS** |
| Database health check | Hardcoded string | **Live DB query (`SELECT 1`), 503 on failure** | **PASS** |
| Auth Rate Limiting | None (vulnerable) | **10 req/min sliding window per IP (429 on abuse)** | **PASS** |
| Cross-user isolation | Partial (scenarios only) | **Verified for scenarios, calculations, traces, exports** | **PASS** |

---

## 2. Repository Inventory

### Application Entry Points
- **Backend:** `backend/app/main.py` — FastAPI app with request correlation IDs, security headers, `/health`, and live DB-checked `/ready`.
- **Frontend:** `frontend/src/main.tsx` → `App.tsx` — React 18 + Vite SPA with tabs for Dashboard, Portfolio, Catalogue, Scenarios, Optimizer, Assistant, and Settings.

### Backend Architecture
- **Framework:** FastAPI 0.115+ with SQLAlchemy 2.0, Alembic, Argon2-cffi, Pydantic v2.
- **Database:** SQLite (development default), PostgreSQL via psycopg (production container).
- **Auth:** Bearer session tokens (SHA-256 hashed), Argon2 password hashing (`min_length=8`), rate-limited endpoints.
- **API Routers:** 
  - `v1_router` (`/api/v1`) — public catalogue (paginated), taxonomy, sources, effective-dated calculation estimates.
  - `auth_router` (`/api/v1/auth`) — register (rate-limited), login (rate-limited), logout (session invalidation).
  - `private_router` (`/api/v1`) — `/me` (preferences, account deletion), scenarios (paginated CRUD, duplication), portfolio CRUD, calculation runs, trace inspection, optimizer, reminders (CRUD with deletion), expiring exports.
  - `admin_router` (`/api/v1/admin`) — rules, review queue, publish gates, audit events, sources.

### Frontend Architecture
- **Framework:** React 18 + TypeScript + Vite.
- **API client:** `src/api.ts` — typed fetch client for all backend endpoints.
- **State:** React component state, localStorage session persistence, token auth headers.
- **Features:** 
  - Catalogue: exact variant listing, pagination support, inline rule inspection with verification badges.
  - Portfolio: add from catalogue, view owned cards, remove cards.
  - Scenarios: custom spend planning, category/channel selection, cap knowledge state toggling.
  - Comparison: multi-card scenario reward comparison with bucket traces.
  - Optimizer: constrained spending allocation across owned cards, displaying friendly card names and shared-cap warnings.
  - Settings: reminders creation and deletion, account deletion, and comprehensive expiring data export.

---

## 3. Feature Traceability & Remediation Matrix

| ID | Feature | Backend Route | Frontend Component | Database | Tests | Remediation Done | Status |
|---|---|---|---|---|---|---|---|
| F01 | User registration | `POST /api/v1/auth/register` | `App.tsx:AuthScreen` | `users`, `sessions`, `audit_events` | `test_security.py`, `test_api.py` | Added `min_length=8` Pydantic validation, sliding window rate limit | **Implemented & Verified** |
| F02 | User login | `POST /api/v1/auth/login` | `App.tsx:AuthScreen` | `sessions` | `test_api.py`, `test_security.py` | Rate limiter enforced (429 on abuse) | **Implemented & Verified** |
| F03 | User logout | `POST /api/v1/auth/logout` | `api.ts:logout` | `sessions` | `test_api.py:test_logout_invalidates_token` | Added integration test verifying session deletion & subsequent 401 | **Implemented & Verified** |
| F04 | Session management | `deps.py:get_current_user` | `api.ts` | `sessions` | `test_api.py` | Session TTL enforced, SHA-256 hashed | **Implemented & Verified** |
| F05 | User preferences | `PATCH /api/v1/me/preferences` | `App.tsx:Settings` | `users` | `test_api.py` | Validated timezone & currency | **Implemented & Verified** |
| F06 | Account deletion | `DELETE /api/v1/me` | `App.tsx:Settings` | All user tables | `test_api.py:test_user_account_deletion_cleans_up` | Cascade cleanup of scenarios, calculations, reminders, exports | **Implemented & Verified** |
| F07 | Data export | `POST /api/v1/exports` | `App.tsx:Settings` | `export_jobs` | `test_api.py:test_cross_user_export_isolation` | Added portfolio cards, scenarios, reminders, expiry metadata | **Implemented & Verified** |
| F08 | Card catalogue listing | `GET /api/v1/catalogue/cards` | `App.tsx:Catalogue` | `card_variants`, `issuers` | `test_api.py` | Added pagination (`limit`, `offset`), network and status filters | **Implemented & Verified** |
| F09 | Card rules inspection | `GET /api/v1/card-variants/{id}/rules` | `App.tsx:Catalogue` | `rules` | `test_api.py` | Wired frontend to fetch and display card rules inline | **Implemented & Verified** |
| F10 | Portfolio CRUD | `POST/GET/DELETE /api/v1/me/cards` | `App.tsx:Portfolio` | `user_cards` | `test_api.py` | Ownership isolation, deletion, duplicate protection | **Implemented & Verified** |
| F11 | Effective-dated calculations | `POST /api/v1/calculations/estimate` | `api.ts` | `rules` | `test_calculation_matrix.py` (20 cases) | Filter rules by date: `effective_from <= date <= effective_to` | **Implemented & Verified** |
| F12 | Multi-card comparison | `POST /api/v1/calculations/compare` | `App.tsx:Scenarios` | `calculation_runs`, traces | `test_api.py` | Full multi-card trace evaluation | **Implemented & Verified** |
| F13 | Portfolio optimizer | `POST /api/v1/optimizer/run` | `App.tsx:Optimizer` | In-memory engine | `test_optimizer_properties.py` (4 tests) | Preserves spend, excludes ineligible cards, displays card display names | **Implemented & Verified** |
| F14 | Reminders management | `POST/GET/DELETE /api/v1/reminders` | `App.tsx:Settings` | `reminders` | `test_api.py` | Added delete API endpoint and frontend delete button | **Implemented & Verified** |
| F15 | System health & readiness | `GET /health`, `GET /ready` | Operational API | Live DB connection | `test_api.py:test_health_and_readiness_endpoints` | `/ready` executes live `SELECT 1` query, returning 503 if DB is down | **Implemented & Verified** |
| F16 | Evidence-grounded AI assistant | `POST /api/v1/assistant/ask` | `App.tsx:Assistant` | `sources` | `test_assistant.py` | Lexical matching, abstains without verified source, citations | **Implemented & Verified** |

---

## 4. Key Fixes Implemented

1. **Security & Input Validation:**
   - Enforced 8-character minimum password length in `backend/app/domain/scenarios/models.py`.
   - Created in-memory sliding-window rate limiter in `backend/app/core/ratelimit.py` (10 requests/minute per IP) on `/auth/register` and `/auth/login`.
   - Added integration test proving logout revokes the bearer token.
   - Added integration tests verifying user isolation on calculations, traces, and export jobs.
   - Added integration test verifying complete account deletion.

2. **Financial Engine & Calculation Precision:**
   - Resolved effective-dated rule lookup in `backend/app/api/v1/router.py` using `and_(Rule.effective_from <= date, or_(Rule.effective_to.is_(None), Rule.effective_to >= date))`.
   - Updated `_manifest_hash` in `backend/app/domain/calculator/engine.py` to support `CashbackRule | PointsRule`.
   - Built table-driven test suite with 20 calculation boundary cases in `backend/tests/unit/test_calculation_matrix.py` (cap limits, exact caps, unknown cap ranges, zero amounts, exclusions, date boundaries, currency checks).
   - Fixed optimizer in `backend/app/domain/optimizer.py` to prevent allocating spend to ineligible or excluded cards.
   - Added property tests in `backend/tests/unit/test_optimizer_properties.py` verifying total planned spend preservation and shared-cap warning generation.

3. **Frontend UX & API Alignment:**
   - Updated `Optimizer` results in `frontend/src/App.tsx` to display human-readable card product names instead of raw UUIDs.
   - Connected `Catalogue` tab to `GET /api/v1/card-variants/{id}/rules` with expandable card rule inspector, parameters, dates, and verification badges.
   - Added reminder deletion in both backend API and frontend Settings UI.
   - Enhanced user export bundle in `backend/app/api/v1/extended.py` to include user profile, portfolio cards, planned scenarios, and reminders.
   - Added pagination (`limit`, `offset`) to `GET /api/v1/catalogue/cards` and `GET /api/v1/me/scenarios`.

4. **Reliability & Operational Observability:**
   - Upgraded `/ready` health check in `backend/app/main.py` to perform a real `SELECT 1` query against the database.
   - Documented all backend configuration variables in `docs/CONFIGURATION.md` and updated `backend/.env.example`.

---

## 5. Production Readiness Decision

**READY FOR CONTROLLED STAGING / ALPHA PILOT**

- **Readiness Justification:**
  - All 46 automated backend tests pass.
  - Code passes strict `ruff` linting and formatting.
  - Frontend compiles with 0 TypeScript errors and builds for production via Vite in 1.65s.
  - Security boundaries (password validation, rate limiting, token invalidation, cross-user isolation) are verified by automated tests.
  - Financial calculations use exact Decimal arithmetic with deterministic traces and effective-dated rule resolution.

- **Remaining Limitations for Full Public Launch:**
  1. **Real Card Data:** The current catalogue contains synthetic/fictional rules only. Real issuer terms and official source evidence must be curated and verified by authorized human reviewers before real financial recommendations are made.
  2. **Identity Provider:** For multi-region production, an external managed identity provider (OAuth/OIDC) and persistent Redis-backed rate limiter should replace the local single-instance in-memory limiter.
  3. **Shared Caps Across Categories:** The optimizer handles caps on a per-bucket basis; cross-category pooled caps are flagged with an explicit warning to users.
