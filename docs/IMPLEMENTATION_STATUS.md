# Implementation Status — Synthetic Local MVP

The selected track is **Synthetic local MVP**. This status describes the implemented code, not commercial production readiness or verification of real issuer terms.

## Quality Gates & Verification Summary
- **Local MVP Quality:** **PASS** (100% green: 76 backend unit/integration tests, 8 frontend component tests, zero lint warnings, clean build)
- **Browser E2E:** **PASS** (Playwright test suite covering 18 complete user journeys against live backend and frontend)
- **Real Issuer Evidence:** **SYNTHETIC ONLY** (no real issuer terms are activated; fictional local fixtures only)
- **Production Readiness Decision:** **NOT APPROVED** (pending independent real-world issuer verification and commercial release sign-offs)

## Phase status

| Phase | Status | Scope completed | Explicitly pending |
|---|---|---|---|
| 0 Foundations | Complete for local MVP | FastAPI, React/Vite, configuration, SQLite, PostgreSQL-compatible SQLAlchemy models, Alembic, Docker files, CI, lint, tests, request IDs, health endpoints | Production secrets, hosted environments, external monitoring, restore drill |
| 1 Catalogue/rules/evidence | Complete for synthetic catalogue | Database-backed exact variants, synthetic cashback and points rules, source records, excerpts, rule tests, admin review/publish gates, audit events, validation scripts | Real issuer research, source rights, independent real-world reviewers |
| 2 Scenarios | Complete for local MVP | Authenticated scenario CRUD, duplication, spend buckets, taxonomy endpoints, allocations, point valuation assumptions, revisions, ownership isolation, portfolio CRUD | Richer multi-row editor polish and external imports |
| 3 Calculator | Complete for supported synthetic rules | Decimal cashback and points, explicit point valuation, eligibility, exclusions, effective dates, caps, unknown cap ranges, traces, manifests, persisted runs, comparison | Fees, milestones, reversals, multiple currencies, all real issuer rule combinations |
| 4 Optimizer | Complete for bounded synthetic subset | Existing-card constraint, shared monthly cap tracking across all buckets, fixed allocation preservation, total-spend checks, baseline/proposal/delta, method version, infeasibility/partial allocation output | Complex multi-period MILP solver, real-time issuer milestone trackers |
| 5 Assistant | Complete as safe local fallback | Lexical evidence lookup, citation-shaped response, abstention, no rule publishing, no model dependency | LLM provider, full ingestion pipeline, semantic retrieval, evaluation dataset |
| 6 Privacy/operations | Complete for local MVP | Argon2 passwords, sessions, ownership checks, export expiry, account deletion, reminders, logs/request IDs, security headers, health checks, persisted traces | Production retention enforcement, encrypted backups, external alerting, legal review |
| 7 Verified pilot/release | Pending by design | Release documentation, Docker Compose, CI gates, synthetic release track | Real launch cards, source verification, pilot, production hosting, security/accessibility/load sign-off |

## Local run

```bash
cd backend
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

Or start PostgreSQL plus the containerized services from the repository root:

```bash
docker compose up --build
```

## Local admin provisioning

Public registration endpoints unconditionally create standard accounts (`role: "user"`). To provision an administrator account:

```bash
# Provision out-of-band via trusted CLI
python scripts/provision_admin.py --email admin@cardwise.local --password "SecureAdminPass123!" --role admin
```

Alternatively, configure `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` in your local environment file prior to starting the service. Every administrative provisioning action is permanently logged to `audit_events`.

## Important boundary

No real card benefit is represented as verified. The synthetic fixture is intentionally marked draft/synthetic, and the assistant abstains when current evidence is unavailable.
