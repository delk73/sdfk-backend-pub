---
version: TBD
lastReviewed: 2025-07-17
---

# Test Structure

This directory contains all tests for the SDFK Backend.

## Unit Tests

Unit tests are located in the `tests/unit` directory. They test individual components and functions in isolation.

## Integration Tests

Integration tests are located in the `tests/integration` directory. They test the interaction between different components and services.

## Fixtures

Fixtures are defined in `conftest.py` and `fixtures/factories.py`. They provide reusable test data and setup/teardown functionality.

### Database Fixtures

- `db_session`: A database session for a test
- `clean_db`: A clean database session with all tables emptied

### Model Fixtures

- `shader_lib`: A test shader library
- `shader`: A test shader
- `control`: A test control
- `tone`: A test tone
- `haptic`: A test haptic
- `modulation`: A test modulation
- `synesthetic_asset`: A test synesthetic asset with all components
- `complete_asset`: A complete synesthetic asset with all related components

### Client Fixtures

- `client`: A test client for the API
- `auth_client`: A test client with authentication

### Other Fixtures

- `example_dir`: A temporary directory with example files
- `auth_token`: A test authentication token
- `auth_headers`: Test authentication headers

## Factories

Factories are used to create test data. They are located in `tests/fixtures/factories.py`.

## Running Tests

To run all tests, use the following command:

```bash
pytest
```

To run unit tests:

```bash
pytest tests/unit
```

To run integration tests:

```bash
pytest tests/integration
```

Alternatively, execute the helper scripts from the project root:

```bash
./codex.sh       # run tests locally using SQLite
./test.sh        # run tests inside the Docker environment
```

### Poetry & requirements.txt sync

- The project now uses Poetry as the source of truth for dependencies (`pyproject.toml`).
- Docker builds still install via `requirements.txt` for layering speed.
- `./test.sh` will, if Poetry is available and using Python 3.11, best‑effort:
  - `poetry lock`
  - `poetry export -f requirements.txt --output requirements.txt --without-hashes`
- You can also run `make sync-reqs` locally (preferred) to explicitly lock and export.
- The Dockerfile copies `libs/synesthetic-schemas/python` before `pip install` so the exported editable path dep installs correctly.

## Coverage

To check test coverage, use the following command:

```bash
pytest --cov=app --cov-report term-missing
```
