### Pull Request Summary
*   **Purpose:** Provide repository overview and development workflow documentation.
*   **Key Areas Updated:** Project summary, developer workflow, environment configuration.
*   **Human Review Focus:** Verify accuracy of feature list and onboarding steps.

### Project Overview
*   **High-Level Summary:** FastAPI service managing synesthetic assets with PostgreSQL and Redis.
*   **Key Features:**
    - RESTful endpoints for synesthetic asset CRUD operations.
    - Text generation via Ollama and Google Gemini.
    - Protobuf asset upload and retrieval.
    - Vector search and embeddings using pgvector.
    - Asset patching workflow with rating feedback.
*   **Technology Stack:**
    - Python 3.11, FastAPI, Starlette.
    - Pydantic v2 for schema validation.
    - SQLAlchemy and Alembic for database management.
    - PostgreSQL, SQLite, Redis.
    - Docker and Docker Compose.
    - Pytest for testing.
    - Google Generative AI and Ollama integrations.
    - Protobuf and gRPC.

### Developer Workflow
*   **Primary Entry Points:**

| Script | Role |
| --- | --- |
| `codex.sh` | Run SQLite-backed tests or serve the API locally. |
| `test.sh` | Run full Docker-based test suite with PostgreSQL and Redis. |
| `lint.sh` | Format code, run flake8, and check types. |
| `cleanup.sh` | Stop Docker services while preserving data. |
| `nuke.sh` | Reset all data and recreate the database. |

*   **Workflow Philosophy:**
    - Keep implementation simple and explicit.
    - Favor deterministic behavior and reproducible runs.
    - Ensure the codebase remains understandable by a single developer.
    - Run pytest-based test pipelines without shortcuts.

*   **Onboarding Guide:**
    1. `git clone <repo-url>`
    2. `cd sdfk-backend`
    3. `python3.11 -m venv .venv`
    4. `source .venv/bin/activate`
    5. `pip install -r requirements.txt`
    6. `cp .env.example .env`
    7. `./codex.sh`  # run local tests

*   **Dependency Management:**
    - Poetry is used as the source of truth (`pyproject.toml`).
    - Keep `requirements.txt` in sync for Docker by running `make sync-reqs`.
    - `test.sh` performs a best‑effort lock+export using Poetry when Python 3.11 is available.
    - Dockerfile copies `libs/synesthetic-schemas/python` before `pip install` to support the exported editable path dependency.

*   **Configuration:**
    - `DATABASE_URL`: PostgreSQL connection string.
    - `JWT_SECRET`: Secret key for JWT tokens.
    - `OLLAMA_API_URL`: Endpoint for Ollama service.
    - `OLLAMA_TIMEOUT`: Request timeout for Ollama calls (seconds).
    - `OLLAMA_FALLBACK`: Fallback model for Ollama text generation.
    - `OLLAMA_VISION_FALLBACK`: Fallback model for Ollama vision tasks.
    - `GEMINI_API_KEY`: API key for Google Gemini.
    - `GEMINI_MODEL`: Default Gemini model.
    - `GEMINI_TIMEOUT_SEC`: Request timeout for Gemini calls (seconds).
    - `RLHF_DATASET_PATH`: Path to RLHF feedback dataset.
    - `RLHF_TRAIN_CMD`: Command for RLHF training process.
