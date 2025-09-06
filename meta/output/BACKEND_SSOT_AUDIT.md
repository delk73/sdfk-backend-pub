# Backend Interrogation — synesthetic_schemas Integration

- Objective: Audit SDFK Backend for clean SSOT (synesthetic-schemas) integration with CRUD-only scope, stable response envelopes, version header policy, schema pruning, and CI parity.
- Constraints: KISS, deterministic, Python 3.11, no DB migrations.

## B1. Patch/Preview Removal (CRUD-only)

- Findings:
  - No `/patches` router; file `app/routers/patches.py` removed.
  - No preview/apply endpoints in `app/routers/synesthetic_assets.py`; only CRUD + nested read remain.
  - Patch storage helpers removed from `app/main.py`; no `get_ring_buffer_patch_storage`.
  - Tests referencing preview/apply updated/disabled accordingly; ring buffer fixture removed.
- Verification:
  - Search: `rg -n "patch|preview|ring_buffer|get_ring_buffer" app tests`
  - Result: Only docstrings/comments remain; no functional references.

## B2. SSOT Requests & Envelope Responses

- Findings:
  - Requests validate via SSOT models:
    - SynestheticAsset create: `app/routers/synesthetic_assets.py` imports `synesthetic_schemas.synesthetic_asset.SynestheticAsset`.
    - Controls, Tones, Shaders, Haptics, Modulations: factories use SSOT create schemas via `app/routers/factory.py` and router-specific modules (`app/routers/shaders.py`).
  - Responses preserve IDs and use `.model_dump(mode="json")` in formatters:
    - `app/services/asset_utils.py` uses SSOT models for nested serialization and dumps with `mode="json"` (fixes enum serialization).
    - Ensures list-typed fields are `[]`, not `null`, to satisfy response validation.
    - Nested asset formatting omits nested component IDs (e.g., drops `shader_id` inside `shader`).
- Verification:
  - Search: `rg -n "from synesthetic_schemas" app/routers app/services`
  - Search: `rg -n "model_dump\(mode=\"json\"\)" app`

## B3. Version Header Consistency

- Findings:
  - `X-Schema-Version` optional dependency added to all routers (controls, tones, shaders, shader_libs, embeddings, search, protobuf-assets, synesthetic-assets). Absent header allowed; mismatched header → 409 Conflict.
  - `/schema/version` endpoint returns the version from `libs/synesthetic-schemas/version.json`.
- Verification:
  - Search: `rg -n "X-Schema-Version" app`

## B4. Local Schema Pruning

- Findings:
  - Local request models replaced by SSOT across routers.
  - Local response wrappers retained to preserve API IDs and shapes (e.g., `ShaderAPIResponse`, `SynestheticAssetResponse`, `NestedSynestheticAssetResponse`).
  - Remaining local schemas are wrappers, error/embedding models, and MCP/compute-related definitions.
- Verification:
  - Search: `rg -n "from app\\.schemas" app/routers app/services | rg -v "mcp|error|embedding|patch_index|compute_shader|ShaderLib"`

## B5. Contracts & Test Parity

- Findings:
  - Response payloads stabilized with IDs; nested responses validated by `NestedSynestheticAssetResponse`.
  - Normalization added to CRUD factory to ensure list fields are arrays (not null) for Tone/Haptic/Modulation.
  - Protobuf asset export fixed to pass `modulations` list (not the Modulation row) into the exporter.
- Status:
  - Local SQLite suite: expected to pass after changes; full Docker `./test.sh` should pass after environment is available.
- Notes:
  - If any failures persist, re-check nested response list fields and ensure control bundle mappings use arrays for `keys`, `mouseButtons`, `wheel` coercions.

## B6. CI & Docs Hygiene

- Findings:
  - Docs should reflect CRUD-only endpoints; preview/apply removed.
  - README/docs mention `X-Schema-Version` policy and `/schema/version`.
  - CI should ensure submodules are present (recursive checkout) before tests.
- Verification:
  - Searches to run in CI: `rg -n "/patch" docs/api/endpoints.md`, `rg -n "schemaVersion" README.md docs`, `rg -n "submodules:.*recursive" .github/workflows`.

## Summary

- CRUD-only enforcement complete; patch infrastructure removed.
- Requests validate against `synesthetic-schemas`.
- Responses keep IDs; nested payloads conform and serialize with `.model_dump(mode="json")`.
- Version header dependency consistent; `/schema/version` available.
- Local schemas pruned to wrappers.
- Test parity addressed through payload normalization and exporter fix.
- Action Items:
  - Run `./codex.sh` and `./test.sh` in CI to confirm green.
  - Update docs to remove patch references and document version policy if not already.

