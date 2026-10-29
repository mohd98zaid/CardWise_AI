.PHONY: backend-test backend-lint frontend-build migrate

backend-test:
	cd backend && python -m pytest -q

backend-lint:
	cd backend && python -m ruff check app tests migrations

frontend-build:
	cd frontend && npm run build

migrate:
	cd backend && alembic upgrade head

validate-rules:
	python scripts/validate_rule_data.py
	python scripts/check_rule_freshness.py
