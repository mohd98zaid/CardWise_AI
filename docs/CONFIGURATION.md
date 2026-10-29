# Configuration Reference

This document describes all environment variables used across CardWise AI backend services.

## Environment Variables

| Variable | Description | Required | Default | Service | Sensitive |
|---|---|---|---|---|---|
| `APP_ENV` | Application environment (`development`, `test`, `production`) | No | `development` | Backend | No |
| `DATABASE_URL` | SQLAlchemy connection string (SQLite for dev, PostgreSQL for production) | No | `sqlite:///./cardwise.db` | Backend | Yes (prod) |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowed browser origins | No | `http://localhost:5173,http://127.0.0.1:5173` | Backend | No |
| `SESSION_TTL_HOURS` | Lifetime of bearer session tokens in hours | No | `24` | Backend | No |
| `EXPORT_EXPIRY_HOURS` | Lifetime of user data export bundles in hours | No | `24` | Backend | No |
| `ENABLE_ASSISTANT` | Feature flag to enable/disable the AI assistant endpoint | No | `false` | Backend | No |
| `AI_PROVIDER` | AI provider configuration (`disabled`, `openai`, etc.) | No | `disabled` | Backend | No |
| `AI_MODEL` | AI model identifier when AI provider is enabled | No | `""` (empty) | Backend | No |
| `AUTH_RATE_LIMIT` | Max allowed requests per 60-second window per IP for auth endpoints | No | `10` | Backend | No |
| `VITE_API_BASE_URL` | Base URL of the backend API for frontend HTTP client | No | `http://localhost:8000` | Frontend | No |

## Notes
- `.env.example` contains non-secret development defaults.
- Real credentials and production database connection strings must never be committed to git.
- If `DATABASE_URL` is configured with PostgreSQL, migrations should be applied before starting the server (`alembic upgrade head`).
