# IS601 Module 11 – Calculator API

## Running the Tests

This project has three test layers. All commands assume you are inside the
`module11_is601/` directory with the virtual environment activated.

### Prerequisites

```bash
pip install -r requirements.txt
playwright install chromium
```

### Unit tests (no database needed)

Tests the pure arithmetic operations in `app/operations/`.

```bash
pytest tests/unit/ -v
```

### Integration tests – schema & model logic (no database needed)

Tests Pydantic schema validation and SQLAlchemy model/factory logic without a
live database connection.

```bash
pytest tests/integration/test_calculation.py tests/integration/test_calculation_schema.py -v
```

### Integration tests – database (PostgreSQL required)

Tests that actually insert, query, and validate data in PostgreSQL. Start the
database first:

```bash
# Option A – Docker Compose (recommended)
docker compose up -d db

# Option B – set DATABASE_URL to point at an existing instance
export DATABASE_URL=postgresql://user:password@localhost:5432/myappdb
```

Then run:

```bash
pytest tests/integration/test_db_calculation.py -v
```

### All tests (unit + integration + e2e)

```bash
pytest -v
```

E2E tests launch a headless Chromium browser via Playwright; make sure
`playwright install chromium` has been run first.

### Running with coverage

```bash
pytest tests/unit/ tests/integration/ --cov=app --cov-report=term-missing
```

### CI/CD

GitHub Actions runs all three test layers automatically on every push or pull
request to `main`. A PostgreSQL 15 service container is provided for the
database integration tests. On a successful run on `main`, the Docker image is
built and pushed to Docker Hub as `docsnoop/601_module11:latest`.