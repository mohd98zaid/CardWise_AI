# CardWise AI — Documentation Index

CardWise AI estimates credit-card rewards using exact card variants, source-backed effective-dated rules, deterministic calculations, and transparent portfolio optimization. AI may explain evidence but must not invent terms or calculate authoritative money values.

## Read in this order
1. [Exhaustive implementation blueprint](docs/EXHAUSTIVE_BLUEPRINT.md)
2. [Product requirements](docs/PRD.md)
3. [Architecture](docs/ARCHITECTURE.md)
4. [System design](docs/SYSTEM_DESIGN.md)
5. [Technical stack](docs/TECH_STACK.md)
6. [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
7. [Implementation backlog](docs/IMPLEMENTATION_BACKLOG.md)
8. [Data model](docs/DATA_MODEL.md)
9. [Rule schema and governance](docs/RULE_SCHEMA.md)
10. [Calculation engine](docs/CALCULATION_ENGINE.md)
11. [Portfolio optimizer](docs/PORTFOLIO_OPTIMIZER.md)
12. [API specification](docs/API_SPEC.md)
13. [Frontend specification](docs/FRONTEND_SPEC.md)
14. [AI/RAG design](docs/AI_RAG_DESIGN.md)
15. [Source verification](docs/SOURCE_VERIFICATION.md)
16. [Security threat model](docs/SECURITY_THREAT_MODEL.md)
17. [Privacy and retention](docs/PRIVACY.md)
18. [Test plan](docs/TEST_PLAN.md)
19. [Deployment](docs/DEPLOYMENT.md)
20. [Operations runbook](docs/OPERATIONS_RUNBOOK.md)
21. [Configuration](docs/CONFIGURATION.md)
22. [Observability](docs/OBSERVABILITY.md)
23. [UX specification](docs/UX_SPEC.md)
24. [Acceptance criteria](docs/ACCEPTANCE_CRITERIA.md)
25. [Risk register](docs/RISK_REGISTER.md)
26. [Release plan](docs/RELEASE_PLAN.md)
27. [Implementation status](docs/IMPLEMENTATION_STATUS.md)
28. [Architecture Decision Records](docs/ADR/README.md)
29. [Contribution guide](CONTRIBUTING.md)
30. [Security policy](SECURITY.md)
31. [Privacy summary](PRIVACY.md)

## Non-negotiable principles
- Use exact card variants, not fuzzy name matches.
- Every active material rule needs evidence, effective-date handling, and review state.
- Use Decimal for money calculations.
- Never silently treat unknown as zero.
- Store a calculation manifest and trace.
- AI must cite sources or abstain; it cannot publish rules.
- Never collect full card number, CVV, PIN, OTP, or issuer credentials.
- Never recommend extra spending solely to earn rewards.

This repository is a build blueprint. Real issuer terms are not automatically verified by this documentation. Start with synthetic fixtures and independently verify each launch rule.

## Current alpha build

The runnable synthetic local MVP is implemented in `backend/` and `frontend/`. It includes a database-backed synthetic catalogue, cashback and points rules, a Decimal-based calculator with cap and valuation handling, scenario persistence, comparison, portfolio optimization, reminders, exports, admin review gates, and a responsive React workspace.

Run the API from `backend/` with `python -m uvicorn app.main:app --reload`, then run the frontend from `frontend/` with `npm run dev`. The displayed card and rule are fictional and must not be treated as current issuer terms.
