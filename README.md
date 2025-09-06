---
version: v0.5.4
lastReviewed: 2025-08-17
owner: backend@generative
---

# SDFK Backend

A FastAPI backend service with PostgreSQL, Redis caching.

> Grid control and automata have been consolidated into RuleBundle.

## 🚀 Quick Start

Clone the repository and ensure you have Docker, Docker Compose, and Python 3.11+ installed.


## System Context

```mermaid
flowchart LR
    FE["sdfk_fe_ts\n(TypeScript Frontend)"]
    BE["sdfk-backend\n(Python API & CRUD)"]
    RLHF["sdfk_rlhf\n(RLHF Asset Generation)"]

    FE --> |Consumes API| BE
    RLHF --> |Generates Assets via API| BE

    style BE fill:#666666,stroke:#ffffff,stroke-width:2px
```

```bash
# Start the service and run tests
./test.sh

# Stop the service (preserving data)
./cleanup.sh

# Complete reset (removes all data)
./nuke.sh
```

## 📚 API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Additional Documentation

- **Error Handling Architecture**: See `docs/errors/state.md` for comprehensive error handling patterns
- **Error Handling Guide**: See `docs/errors/handling.md` for developer guidance
- **API Status**: All error handling patterns are frozen as of M1.0 (442 tests passing)
- **Database Schema**: See `docs/db_schema.md` for entity relationships and JSON structures
- **Shader DSL Spec**: See `docs/generative/shaders/schema.md` for the canonical shader DSL definition
  
### Schema Versioning

- The backend reads the SSOT schema version from `libs/synesthetic-schemas/version.json`.
- Optional request header `X-Schema-Version` may be provided by clients:
  - If absent, requests proceed (backwards compatible).
  - If present and mismatched, server returns `409 Conflict` with an error body including the expected version.
- Check server version at `GET /schema/version`.
- **Project Roadmap**: See `docs/roadmap/ROADMAP.md` for upcoming milestones

## 🛠️ Development

### Prerequisites

- Docker
- Docker Compose
- Python 3.11+
- Pydantic >=2.5,<3
- Ollama (running locally)
- Redis (handled via Docker)
- Google Generative AI SDK

> Requires `pydantic>=2.5,<3` after migration to Pydantic v2.

### Project Structure

```
sdfk-backend/
├── app/                    # Application code
│   ├── __init__.py
│   ├── main.py            # FastAPI app and routes
│   ├── database.py        # Database configuration
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── security.py        # JWT verification (disabled for dev)
│   └── utils.py           # Utility functions
├── alembic/               # Database migrations
├── data/                  # Persistent data
│   └── postgres/          # PostgreSQL data
├── test.sh               # Setup and run services with Docker
├── codex.sh              # Run tests locally with SQLite
├── cleanup.sh            # Stop services
├── nuke.sh               # Reset everything
└── docker-compose.yml     # Docker configuration
```

### Linting and Type Checking

Run `lint.sh` to format code and check for style or typing issues:

```bash
./lint.sh        # check formatting and lint errors
./lint.sh --fix  # auto-fix simple issues
```

**Using Poetry**
- Install: `python3 -m pip install --user poetry`
- Create env: `poetry env use 3.11 && poetry install`
- Run tests: `poetry run ./codex.sh`
- Serve API: `poetry run ./codex.sh --serve --host 0.0.0.0 --port 8000`
- Sync `requirements.txt` for Docker/CI: `poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev`

Makefile helpers:
- `make sync-reqs` — lock deps and export `requirements.txt` (ensures Docker/CI stays in sync)
- `make poetry-install` — install all deps in the Poetry venv

Note: `make sync-reqs` normalizes the local path dependency to `-e ./libs/synesthetic-schemas/python` so Docker builds can `pip install` it after the Dockerfile copies that folder.


### Environment Variables

Copy `.env.example` to `.env` and adjust as needed:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sdfk
JWT_SECRET=your-secret-key-here
REDIS_URL=redis://localhost:6379
```

### Available Endpoints

- `GET /`: Health check
- `GET /items/`: List all items
- `POST /items/`: Create a new item
- `POST /pb-assets/`: Upload a protobuf asset
- `GET /pb-assets/{id}`: Retrieve an asset in protobuf format

Additional routers expose CRUD endpoints for core asset types. The most commonly used paths are:

- `/synesthetic-assets/` – Full asset lifecycle
- `/shaders/` and `/shader_libs/`
- `/tones/`
- `/haptics/`
- `/controls/`
- `/modulations/`
- `/embeddings/` – Store and query vector embeddings (client-supplied float arrays)
- `/search/assets` – Vector similarity search across assets



### Haptic Complexity

The `meta_info` section of a haptic component includes a `complexity` field. This
value **must be a string**. Numeric values will be coerced to strings when sent
to the API. Use descriptive levels like `low`, `medium`, or `high` to keep asset
metadata consistent.

### Synth Types

The `synth.type` field for a tone must be one of the following:

- `Tone.Synth`
- `Tone.PolySynth`
- `Tone.MonoSynth`
- `Tone.FMSynth`
- `Tone.AMSynth`
- `Tone.DuoSynth`
- `Tone.MembraneSynth`
- `Tone.MetalSynth`
- `Tone.PluckSynth`

Any other value will result in a `422 Unprocessable Entity` response.

### Database Migrations

Migrations are handled automatically by the startup script. For manual control:

```bash
# Generate a new migration
docker compose exec web alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec web alembic upgrade head

# Rollback one migration
docker compose exec web alembic downgrade -1
```

### Authentication

JWT authentication is scaffolded but disabled for development. To re-enable:

1. Edit `app/security.py`
2. Remove the development bypass
3. Implement proper JWT verification

### Services

The application uses several services:
- PostgreSQL: Main database
- Redis: Response caching
- Ollama: LLM integration (must be running locally)

### Loading Example Data

Canonical examples live in the SSOT submodule at `libs/synesthetic-schemas/examples`.
To load them into a running development environment:

```bash
docker compose exec web python -m app.load_examples
```

- The loader validates examples against the SSOT models and posts them to the API.
- Set `EXAMPLES_DIR=/path/to/examples` if you want to use a custom location.
- Note: the legacy `app/examples` directory is deprecated; prefer the SSOT path above.

## 🐛 Troubleshooting

### Permission Issues
If you encounter permission issues with the data directory:
```bash
sudo chown -R 999:999 ./data/postgres
sudo chmod 700 ./data/postgres
```

### Database Connection Issues
If the database won't connect:
1. Stop all services: `./cleanup.sh`
2. Remove data: `./nuke.sh`
3. Start fresh: `./test.sh`

- Cache keys: Based on model and prompt
- Automatic cache invalidation


## Repository SSOT Audit Flow

This project uses a **structured audit loop** to surface mismatches between
ORM models, API schemas, runtime routes, and configuration. The audit provides
a "Single Source of Truth" (SSOT) view across layers, anchored in emitted
snapshots.

### Why This Exists
- **Grounding in runtime artifacts**: Instead of asking an AI to regenerate
  routes or OpenAPI, we emit `_routes.md` and `_openapi.json` snapshots from a
  live app import. These snapshots are the canonical runtime view.
- **Audit by comparison**: The auditor reconciles code models and schemas
  against those snapshots, highlighting drifts, orphans, and config
  inconsistencies.
- **Assisted, not automated**: Codex (or another LLM) interprets the prompt and
  performs mapping/analysis, but final authority stays with developers.

### Audit Flow Commands

Run the following in order:

```bash
./local.sh init       # install deps (pip)
./local.sh db         # create SQLite tables in fallback DB
./local.sh smoke      # sanity-check: import app without error
./local.sh routes     # emit docs/_routes.md (runtime APIRoute table)
./local.sh openapi    # emit docs/_openapi.json (OpenAPI schema dump)
./local.sh emit-ssot  # emit SSOT interrogation prompt (docs/prompts/SSOT_INTERROGATION.md)


## 🧪 Testing

### Running Tests

Use the following commands from the command line:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing

```

To run tests in watch mode (automatically re-run tests on file changes):

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw
```

### Running Tests with Docker

With Docker (Recommended):
```bash
# Start your services (if not already running)
docker-compose up -d

# Run pytest inside the 'backend' container
docker-compose exec backend pytest

# Or, with options:
docker-compose exec backend pytest -v --cov=app
```

One-shot into Container:
```bash
# Run tests once without starting the services in the background
docker-compose run --rm backend pytest

# Or, with options:
docker-compose run --rm backend pytest -v --cov=app
```

### Local Testing Script

When Docker isn't available you can run the full test suite locally using
`./codex.sh`. This script mirrors the `test.sh` workflow but relies on an
SQLite database instead of Docker services.

```bash
./codex.sh              # run tests end to end
./codex.sh --debug      # show verbose example import output
```

The script cleans any prior test database, loads the example data, executes
`pytest`, and performs a few sanity checks on the generated records.

### Test Structure

- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/conftest.py` - Shared pytest fixtures

### Property-Based Testing

Property-based testing using hypothesis for:
- Input validation
- Parameter boundaries
- Edge cases

Example of a property-based test:
```python
from hypothesis import given, strategies as st

@given(
    prompt=st.text(min_size=1, max_size=1000),
    temperature=st.floats(min_value=0.0, max_value=1.0)
)
def test_something(prompt: str, temperature: float):
    # Your test code here
    pass
```

### Performance & Stress Testing

Refer to `docs/performance_testing.md` for instructions on benchmarking the
application with caching disabled and enabled. Caching can be toggled at
runtime via the `/cache` API endpoint.
The `CACHE_ENABLED` environment variable sets the default state on startup.

## 🤖 Agentic Testing System

The SDFK backend includes an **agentic** testing system for validating example configurations and simulating synesthetic asset behavior. These tests leverage modular agents defined in `tests/agents/` to ensure each example asset loads correctly and behaves as expected.  A more detailed overview is available in [`docs/testing/agents_testing.md`](docs/testing/agents_testing.md).

### Overview

The agent testing system consists of:
- **ConfigAgent**: Loads and parses example JSON files into validated Pydantic models
- **StateMirrorAgent**: Maintains mutable state with pub/sub broadcasting for parameter changes
- **ModulationAgent**: Applies LFO-style parameter modulations over time
- **OrchestrationAgent**: Coordinates full asset lifecycle simulations
- **Generic Validation**: Uniform testing rules applied to all examples

### Running Agent Tests

#### Test All Examples
```bash
# Test all examples with the agent system
./test.sh -a

# Test with verbose debugging output
./test.sh -a --agents-debug
```

#### Test Specific Examples
```bash
# Test a specific example file
./test.sh -e SynestheticAsset_Example1.json

# Test Example7 specifically
./test.sh -e7
```

#### Standalone Agent Testing
```bash
# Run the agent test script directly (requires Docker services running)
docker compose exec web python run_agent_tests.py

# With debug output
docker compose exec web python run_agent_tests.py --debug
```

### What Gets Tested

The agent system validates each example file for:

#### ✅ **Configuration Loading**
- JSON parsing and Pydantic model validation
- Schema compliance checking
- Asset name and description validation

#### ✅ **Shader Validation**
- Fragment shader code presence and syntax
- Uniform parameter definitions
- Shader library references

#### ✅ **Parameter Validation**
- Control parameter definitions and bounds
- Duplicate parameter detection
- Min/max value validation
- Parameter type checking

#### ✅ **Modulation Validation**
- Modulation target verification
- LFO configuration validation
- Parameter mapping checks

#### ✅ **Component Detection**
- Audio/tone configuration presence
- Haptic feedback definitions
- RuleBundle setups

#### ✅ **Simulation Testing**
- 5-step orchestration simulation for synesthetic assets
- State variable evolution tracking
- Parameter modulation application
- Final state validation

### Example Output

```bash
🔍 Testing all examples with generic agent system...
Found examples to test:
  • RuleBundle_Example.json
  • SynestheticAsset_Example1.json
  [... etc ...]

🧪 Testing: SynestheticAsset_Example1.json
🔧 Loading configuration for SynestheticAsset_Example1.json...
✅ Loaded: Circle Harmony
📋 Description: A circular pattern that pulses with audio
✅ Shader fragment code present
✅ Found 8 control parameters
✅ Found 2 modulations
🎭 Running orchestration simulation...
✅ Simulation completed with 8 state variables
📊 Final state keys: ['shader.u_r', 'shader.u_g', 'shader.u_b', ...]
✅ All validations passed
  ✅ PASSED

📊 AGENT TEST SUMMARY
✅ Passed: 12
⚠️  Warnings: 2
❌ Failed: 1
📝 Total: 15
```

### Integration with codex.sh

The agent testing system is also integrated with the local testing script:

```bash
# Run agent tests locally (SQLite-based)
./codex.sh --agents

# Test Example7 specifically
./codex.sh --example7

# Test with debug output
./codex.sh --agents --debug
```

### Benefits

#### 🚀 **Rapid Development**
- Test asset configurations without full runtime environment
- Quick validation of new examples
- Fast iteration on asset development

#### 🛡️ **Regression Prevention**
- Catch configuration errors before deployment
- Validate complex multimodal interactions
- Ensure backward compatibility

#### 🔍 **Comprehensive Coverage**
- Tests all example types uniformly
- Validates both simple and complex assets
- Covers edge cases and boundary conditions

#### 📊 **Detailed Reporting**
- Clear pass/fail status for each example
- Warning detection for potential issues
- Summary statistics for test runs

### Extending the System

The agent testing framework is designed to be extensible:

1. **Add New Validation Rules**: Extend the validation logic in `run_agent_tests.py`
2. **Create Specialized Agents**: Add new agent types in `tests/agents/`
3. **Custom Test Scenarios**: Implement domain-specific testing patterns
4. **Enhanced Reporting**: Add custom metrics and analysis

### Files and Structure

```
tests/agents/
├── README.md                    # Agent system documentation
├── base_agent.py               # Base agent lifecycle
├── config_agent.py             # Example file loading
├── state_mirror_agent.py       # State management and broadcasting
├── modulation_agent.py         # Parameter modulation simulation
├── orchestration_agent.py      # Full lifecycle coordination
├── example7_agent.py           # Specialized Example7 testing
└── test_*.py                   # Agent test suites

run_agent_tests.py              # Standalone Python test runner
```

This system ensures that all synesthetic assets maintain high quality and consistency across the platform, while providing developers with fast feedback on their configurations.
