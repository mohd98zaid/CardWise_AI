# Security Threat Model

## Assets
Accounts, scenarios, calculations, editorial rules/evidence, sessions/secrets, source material, and audit records.

## Prohibited sensitive data
Never request/store full PAN, CVV/CVC, PIN, OTP, issuer password, or unnecessary identity documents.

## Threats and controls
- Broken access control: server-side ownership checks, role checks, cross-user IDOR tests.
- Account takeover: trusted identity provider or established password hashing, secure sessions, rate limits, safe reset flows.
- Rule poisoning: evidence, schema validation, independent review, test gates, audit, atomic publication.
- Prompt injection: retrieved documents are untrusted; no rule-writing tools for ordinary users; narrow tool allowlist.
- Data leakage: minimization, redacted logs, least privilege, TLS, storage encryption where available, export expiry.
- Supply chain: lockfiles, vulnerability/secret scans, package review, least-privilege CI credentials.
- Scraping abuse: respect source terms, rate limits, access controls, and applicable robots guidance.

## Release gates
Threat model review, authorization tests, clean secret scan, dependency scan, CORS/security header review, validated production secrets, log inspection, restricted backups, incident runbooks.

## Incident handling
For incorrect rules, calculation bugs, data access, leaked secrets, compromised admin, source complaints, or AI unsupported claims: contain, preserve evidence, assess impact, correct, notify as legally required, and record prevention work.

## Risk Register

### RISK-001: Hardcoded admin email for role assignment
- **Severity**: High
- **Location**: `backend/app/api/v1/extended.py` — `register` endpoint
- **Description**: Admin role is granted to the account whose email matches the hardcoded string `admin@cardwise.local`. Any attacker who registers with that email gains full admin access.
- **Status**: SYNTHETIC-MVP-ONLY — acceptable for local development only.
- **Mitigation required before production**: Replace with a proper admin provisioning process (e.g., CLI seeding, environment-variable controlled seed email, or an invite-based flow with a separate secrets-managed admin password).
