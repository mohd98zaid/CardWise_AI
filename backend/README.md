# Backend

FastAPI service for the CardWise AI alpha. The current catalogue is intentionally synthetic.

## Run locally

```bash
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.

## Checks

```bash
python -m pytest -q
python -m ruff check app tests
```

The calculator is pure, uses `Decimal`, and does not make network or AI calls.
