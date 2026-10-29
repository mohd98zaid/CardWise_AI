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
- **Severity**: High (Mitigated)
- **Location**: `backend/app/api/v1/extended.py` — `register` endpoint
- **Description**: Previously, admin role was granted to the account whose email matched `admin@cardwise.local`.
- **Status**: Remediated (October 2026).
- **Remediation**: Hardcoded email check has been removed completely. All public registrations unconditionally assign role `user`. Privileged administrator provisioning is handled strictly out-of-band via `scripts/provision_admin.py` or configured via `INITIAL_ADMIN_EMAIL`/`INITIAL_ADMIN_PASSWORD` in `backend/app/db/bootstrap.py` with full audit logging.
