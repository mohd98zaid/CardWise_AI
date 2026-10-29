# Deployment

## Environments
Local, CI/test, staging, production. Separate credentials/databases; never copy production user data into development by default.

## Local
Docker Compose, placeholder `.env.example`, synthetic seed data, documented run/test/migration commands.

## Production
HTTPS, secure headers, restrictive CORS, private database, secrets management, non-root containers where practical, health checks, monitoring, rate limits, backups, safe migrations, rollback plan.

## Configuration
Validate environment, DB URL, auth, allowed origins, logs, AI provider/model/timeouts, retention, export expiry, freshness policy, feature flags, notification provider. Fail fast when required production secrets are missing.

## CI/CD
Format/lint, type check, unit/property tests, integration tests, schema validation, secret/dependency scans, build, deploy staging, smoke/E2E, approval, controlled migration, health verification, rollback readiness.

## Recovery
Define recovery objectives. Encrypt/restrict backups. Test restoration of rules, manifests, traces, audit, and scenarios in a clean environment.
