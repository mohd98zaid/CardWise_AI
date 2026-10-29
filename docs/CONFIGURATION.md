# Configuration Reference

Example variable names to finalize during implementation:

| Variable | Purpose | Secret |
|---|---|---|
| `APP_ENV` | environment | No |
| `APP_BASE_URL` | canonical URL | No |
| `DATABASE_URL` | DB connection | Yes |
| `AUTH_PROVIDER` | identity mode | No |
| `SESSION_SECRET` | session signing | Yes |
| `ALLOWED_ORIGINS` | browser origins | No |
| `LOG_LEVEL` | logging | No |
| `AI_PROVIDER` | AI provider | No |
| `AI_MODEL` | model identifier | No |
| `AI_TIMEOUT_SECONDS` | timeout | No |
| `AI_MAX_RETRIES` | retry count | No |
| `AI_DATA_POLICY` | permitted data mode | No |
| `SOURCE_FRESHNESS_DAYS` | default review trigger | No |
| `EXPORT_EXPIRY_HOURS` | export expiry | No |
| `USER_DATA_RETENTION_DAYS` | retention policy | No |
| `ENABLE_ASSISTANT` | feature flag | No |
| `ENABLE_NOTIFICATIONS` | feature flag | No |
| `NOTIFICATION_PROVIDER` | provider | No |

`.env.example` must contain placeholders only. Never commit/log secrets. Separate staging/production. Validate required settings at startup. Freshness should be configurable by source/risk, not treated as universal.
