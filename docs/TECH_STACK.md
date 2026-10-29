# Technical Stack

## Frontend
React, TypeScript, Vite or equivalent, TanStack Query or equivalent, React Hook Form/Zod or equivalents, accessible components, and charting only where useful.

## Backend
Python supported stable release, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, PostgreSQL, Decimal for money.

## AI/search
Start with PostgreSQL full-text search. Add pgvector only if evaluation demonstrates benefit. Optional local inference via Ollama or llama.cpp behind a provider abstraction. Version prompts and evaluation datasets.

## Testing/operations
pytest, Hypothesis, Playwright, Ruff, Mypy/Pyright, Docker, Docker Compose, CI dependency and secret scans, structured logs, error monitoring.

## Dependency policy
Verify maintained status, vulnerabilities, licenses, and compatibility at implementation time. Pin tested dependencies. Keep AI dependencies out of calculator domain code. Do not assume a model ID guarantees privacy, availability, or licensing suitability.

## Avoid premature complexity
Do not begin with microservices, multi-agent orchestration, dedicated vector DB, or autonomous rule publishing.
