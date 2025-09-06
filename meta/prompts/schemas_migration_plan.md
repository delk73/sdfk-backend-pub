# Synesthetic Schemas Migration Plan (Backend)

Goal: migrate all FastAPI request/response Pydantic models from local `app/schemas` to the external `synesthetic_schemas` package provided by the `libs/synesthetic-schemas` submodule. Keep the plan KISS, deterministic, and actionable.

Scope: Pydantic request/response models only. SQLAlchemy DB models remain unchanged. Do not alter test pipelines.


## Repo Facts (detected)
- Submodule: `libs/synesthetic-schemas` exists with Python package at `libs/synesthetic-schemas/python/src/synesthetic_schemas/`.
- Installation
  - `pyproject.toml`: `synesthetic-schemas = { path = "libs/synesthetic-schemas/python", develop = true }`
  - `requirements.txt`: `-e ./libs/synesthetic-schemas/python`
- Import name: Python import path is `synesthetic_schemas` (underscore), not the hyphenated project name.
- Local Pydantic models live in `app/schemas/` (multiple modules).
- FastAPI routers live in `app/routers/` and import `schemas` in two ways:
  - `from app.schemas import ...`
  - `from app import models, schemas, ...` then use `schemas.X` in signatures/response_model.


## Phases

### G1 — Dependency & Imports

T1. Integrate submodule as an editable dependency
- Current: already integrated.
  - pyproject: `synesthetic-schemas = { path = "libs/synesthetic-schemas/python", develop = true }`
  - requirements: `-e ./libs/synesthetic-schemas/python`
- Gap: none.
- Action: no-op.

T2. Identify and replace local model imports
- Target replacement: use `from synesthetic_schemas import <Model>` for models shipped by the external package.
- Import sites to change (detected lines):
  - app/routers/controls.py:9 — `from app.schemas import ControlCreate, ControlResponse`
  - app/routers/factory.py:17 — `from app.schemas import (...)`
  - app/load_examples.py:9 — `from app.schemas import (...)`
  - app/file_diagnostics.py:11 — `from app.schemas import (...)`
  - app/utils/uniform_params.py:7 — `from app.schemas.shader import UniformDef, InputParameter`
  - app/utils/example_validation.py:6 — `from app.schemas import (...)`
  - app/routers/tones.py:6 — `from app import models, schemas, security`
  - app/routers/rule_bundles.py:11 — `from app import models, schemas`
  - app/routers/patches.py:8 — `from app import models, schemas, security`
  - app/routers/search.py:3 — `from app import schemas, security`
  - app/routers/embeddings.py:4 — `from app import models, schemas, security`
  - app/routers/synesthetic_assets.py:7 — `from app import models, schemas, security`
  - app/services/asset_utils.py:7 — `from app import models, schemas`
- Notes
  - Leave MCP and error schemas as local (external package does not provide them):
    - app/routers/mcp/asset.py imports `...schemas.mcp.asset` and `...schemas.error` — keep local.
  - Also update dev/tooling that imports local schemas:
    - scripts/export_schemas.py (imports from `app.schemas.*`) → import from `synesthetic_schemas`.

Actions
- Replace imports of Control/Tone/Shader/Haptic/Modulation/SynestheticAsset/RuleBundle models to `synesthetic_schemas`.
- Keep local-only modules: compute_shader, vectors, embedding, patch_index, patch, lab, mcp, error.

Validation
- rg queries that should return empty after refactor:
  - `rg "from app\\.schemas" app`
  - `rg -n "from app import .*\\bschemas\\b" app/routers app/services`


### G2 — Model & API Usage

T3. Audit API endpoint signatures and response models
- Replace `schemas.*` types in the following routers where they correspond to external models:
  - app/routers/tones.py
    - Lines: 40, 46, 48, 66, 79, 88, 104, 107, 131
    - Replace ToneCreate, ToneUpdate, Tone (response_model and payloads)
  - app/routers/rule_bundles.py
    - Lines: 16, 17, 26, 35, 39
    - Replace RuleBundleSchema
  - app/routers/patches.py
    - Lines: 15, 17, 32
    - Leave PatchRating/PatchRatingScore local (no external equivalent). Only update if external adds these.
  - app/routers/search.py
    - Line: 12
    - Leave EmbeddingQuery local (no external equivalent).
  - app/routers/embeddings.py
    - Lines: 13, 15, 30, 45, 48, 60, 74, 79
    - Leave PatchEmbedding, PatchEmbeddingCreate, EmbeddingDeleteResponse, EmbeddingQuery local.
  - app/routers/synesthetic_assets.py
    - Lines: 36, 40, 76, 80, 247, 310, 342, 353, 402, 407, 453, 460, 504, 509, 533, 559, 564, 597, 602, 633, 638, 671, 729–735, 744, 758
    - Replace SynestheticAsset*, Tone*, Shader*, Haptic*, Control*, Modulation* where those types come from the external package. Keep any request/response models that are local-only.
  - app/routers/controls.py
    - Line: 9
    - Replace ControlCreate, ControlResponse if equivalents exist externally.
  - app/routers/factory.py
    - Line: 17
    - Replace Tone*, Haptic*, Control*, Modulation*, Shader*, ShaderLib* in the import list. External provides `Shader`; `ShaderLib` is a local Pydantic type — keep local unless external adds it.
- Services/utilities using schemas
  - app/services/asset_utils.py:278, 282 — `schemas.RuleBundleSchema` → `synesthetic_schemas.RuleBundle` or exposed bundle schema type from the external package.
  - app/utils/uniform_params.py:7 — `UniformDef, InputParameter` → from `synesthetic_schemas.shader`.
  - scripts/export_schemas.py — switch all imports to `synesthetic_schemas`.

Actions
- For each file above, update:
  - Imports: use `from synesthetic_schemas import <Type>` or `from synesthetic_schemas.<module> import <Type>` to avoid name clashes.
  - Annotations: update function parameters and `response_model=...` to the new imports.
  - Any calls to `.model_validate()` and `.model_dump()` continue to work (Pydantic v2), but confirm field names/aliases are unchanged between local and external models.

Validation
- rg queries for router usage should show only `synesthetic_schemas` types in `response_model=` and payloads for the migrated models:
  - `rg -n "response_model=.*(Tone|Shader|Haptic|Control|Modulation|SynestheticAsset|RuleBundle)" app/routers`
  - `rg -n "\\b(schemas\\.|from app\\.schemas)" app` should be empty except local-only modules.

T4. Deprecate and remove old local schema files (after all usages replaced)
- Candidates for removal from `app/schemas/`:
  - control.py
  - tone.py
  - shader.py
  - haptic.py
  - modulation.py
  - synesthetic_asset.py
  - rule_bundle.py
- Keep (remain local):
  - base_schema.py, compute_shader.py, vectors.py, embedding.py, patch_index.py, patch.py, lab.py, mcp/, error.py
  - ShaderLib Pydantic types (if any) remain local; not present in external package.
- Actions
  - After refs are updated and tests pass, delete the candidate files and prune exports in `app/schemas/__init__.py` accordingly.
- Validation
  - `rg -n "from app\\.schemas\\.(control|tone|shader|haptic|modulation|synesthetic_asset|rule_bundle)" app` → empty
  - `pytest` via `./codex.sh`


### G3 — Versioning & Validation

T5. Implement runtime schema version check
- Current: no version/header checks detected (`rg 'version.json|x-schema-version' app` → empty).
- Source of truth: `libs/synesthetic-schemas/version.json` (e.g., `{ "schemaVersion": "0.7.3" }`).
- Minimal implementation (KISS):
  - Add `app/schema_version.py` with a function to read the version at startup and store a module-level constant `SCHEMA_VERSION`.
  - Add a lightweight dependency or middleware in `app/main.py` that:
    - Reads `X-Schema-Version` request header (optional for backwards-compat if absent),
    - If present and mismatched with `SCHEMA_VERSION`, return `409 Conflict` with a short error model (reuse existing error response type),
    - Apply only to routers/endpoints that accept synesthetic_schemas models (tones, shaders, haptics, controls, modulations, synesthetic assets, rule bundles).
  - Expose a GET endpoint `/schema/version` returning `{ "schema_version": SCHEMA_VERSION }` for client discovery.
- Tests (follow-up once implemented):
  - Happy path: header matches → 2xx; Mismatch → 409; Missing header → 2xx (if optional) or 409 (if strict) per chosen policy.


### G4 — CI & Build

T6. Update CI workflow to clone submodules
- Current: `.github/workflows/` directory exists but has no workflow files; nothing configures submodules.
- Action: ensure CI uses submodules (when a workflow is added):
  - actions/checkout@v4 step must include: `with: { submodules: 'recursive' }`.
  - Alternatively, add a step: `git submodule update --init --recursive`.
- Also confirm local runner scripts continue to install the path dependency:
  - `pip install -r requirements.txt` already includes `-e ./libs/synesthetic-schemas/python`.


## Model Mapping (local → external)
- Provided by external package (migrate):
  - app/schemas/control.py → synesthetic_schemas.control: Control, Mapping, ComboType, ActionType
  - app/schemas/tone.py → synesthetic_schemas.tone: Tone and nested types
  - app/schemas/shader.py → synesthetic_schemas.shader: Shader, UniformDef, InputParameter
  - app/schemas/haptic.py → synesthetic_schemas.haptic: Haptic, DeviceConfig, HapticParameter
  - app/schemas/modulation.py → synesthetic_schemas.modulation: Modulation, ModulationItem
  - app/schemas/synesthetic_asset.py → synesthetic_schemas.synesthetic_asset: SynestheticAsset and nested types
  - app/schemas/rule_bundle.py → synesthetic_schemas.rule_bundle: RuleBundle, Rule
- Local-only (retain locally for now):
  - compute_shader.py, vectors.py, embedding.py, patch_index.py, patch.py, lab.py, mcp/, error.py, base_schema.py
  - ShaderLib Pydantic types (if any) remain local; not present in external package.


## Deterministic To‑Do List

1) Update imports to `synesthetic_schemas`
- Files: controls.py, factory.py, load_examples.py, file_diagnostics.py, utils/uniform_params.py, utils/example_validation.py, tones.py, rule_bundles.py, patches.py, search.py, embeddings.py, synesthetic_assets.py, services/asset_utils.py, scripts/export_schemas.py
- Done when: `rg "from app\\.schemas" app` and `rg "from app import .*\\bschemas\\b" app` return no matches outside local-only modules.

2) Update FastAPI endpoint type hints/response_model
- Replace local types with `synesthetic_schemas` equivalents where available.
- Done when: routers only reference `synesthetic_schemas` types for migrated models; local-only models remain.

3) Prune local schema files and exports
- Remove migrated files under `app/schemas/` and update `app/schemas/__init__.py` accordingly.
- Done when: no imports reference the removed modules; tests pass.

4) Add runtime schema version check
- Implement loader + dependency/middleware and `/schema/version` endpoint.
- Done when: mismatch yields 409; version is observable.

5) Ensure CI is submodule-aware
- When adding CI, configure checkout with `submodules: 'recursive'`.


## Post‑migration Validation
- `./codex.sh` → all unit/integration tests pass (SQLite runner).
- Manual: verify `GET /docs` works and schemas in OpenAPI match `synesthetic_schemas` models.
- Greps:
  - `rg "from app\\.schemas" app` → none (except allowed local-only modules)
  - `rg -n "from app import .*\\bschemas\\b" app` → none (except allowed local-only modules)
  - `rg -n "synesthetic_schemas" app | wc -l` → non-zero


## Notes & Risks
- Field/alias drift: confirm external models’ field names/aliases match the local ones; adjust serialization helpers in `app/services/asset_utils.py` if necessary.
- Partial coverage: embedding/patch-related endpoints remain on local models until external package adds equivalents.
- Tooling updates: scripts relying on local schemas must switch to `synesthetic_schemas` or be retired.

