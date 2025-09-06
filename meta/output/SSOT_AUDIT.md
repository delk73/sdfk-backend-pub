# System Interrogation — synesthetic-schemas (SSOT Repo)

## Objective
Verify synesthetic-schemas is a clean SSOT for schemas, examples, and codegen (Python + TypeScript), with stable versioning, normalization, and CI parity.

## Constraints
- Style: KISS, deterministic, minimal deps
- Python: 3.11
- JSON Schema draft: 2020-12 (policy check)
- No DB migrations
- Output: Markdown only; this report is written to `meta/output/SSOT_AUDIT.md`
- Shell: POSIX; no network calls; prefer repo scripts

## Inputs
- Schemas: `jsonschema/*.schema.json`
- Examples: `examples/*.json`
- Version file: `version.json`
- Python pkg: `python/src/synesthetic_schemas/` (with `py.typed`)
- TS dist: `typescript/dist/*.d.ts` (artifacts)
- Makefile and `preflight.sh`
- Codegen: `scripts/ensure_codegen_clean.sh`, `codegen/gen_ts.sh`
- Validators: `scripts/normalize_schemas.py`, `scripts/schema_lint.py`, `scripts/validate_examples.py`
- Docs: `README.md`, `CONTRIBUTING.md`
- CI: `.github/workflows/*.yml`
- Helpers: `scripts/lib/version.py`, `codegen/lib/version.mjs`

## Method
- Inspect files within `libs/synesthetic-schemas` submodule.
- Use ripgrep and file reads to confirm presence and intent.
- Where a tool (poetry/node) would be required, mark as WARN and continue.

## Findings
- Version single-source: `version.json` contains `{\"schemaVersion\": \"0.7.3\"}`. Python (`scripts/lib/version.py`) and TS (`codegen/lib/version.mjs`) read `version.json`; bump/update scripts reference it.
- Typing marker: `python/src/synesthetic_schemas/py.typed` exists.
- Schemas/examples present: JSON Schemas exist under `jsonschema/*.schema.json`; examples present under `examples/*.json`.
- Normalization/lint/validation scripts present: `scripts/normalize_schemas.py`, `scripts/schema_lint.py`, `scripts/validate_examples.py`. Makefile `preflight` runs normalize-check, schema-lint, codegen-check, validate.
- Codegen: `codegen/gen_ts.sh` and `scripts/ensure_codegen_clean.sh` exist; CI runs preflight with optional codegen-check based on path filter.
- CI: `.github/workflows/ci.yml` sets up Node 20 and Python 3.11, uses Poetry, runs `preflight.sh` with/without codegen.
- TS dist artifacts: `typescript/dist` directory not present in submodule snapshot (may be built at publish time). Treat as WARN unless policy requires checked-in artifacts.
- Schema metadata fields: Spot checks show `$defs` structures, but top-level `$id`/`$schema` not embedded in the files as shown here; normalization script references ensuring canonical refs. Treat `$schema`/`$id` declaration compliance as WARN pending tool execution.

## Results by Check (C1–C9)
- C1 Single-source version and helper alignment: PASS
  - Evidence: `version.json` has `schemaVersion`; readers at `scripts/lib/version.py`, `codegen/lib/version.mjs`; `scripts/bump_version.py` reads/writes `schemaVersion`.
- C2 Python package typing marker: PASS
  - Evidence: `python/src/synesthetic_schemas/py.typed` exists.
- C3 Schema structural integrity: WARN
  - Reason: Could not run `poetry run` validators in this environment. Manual grep of `$schema`/`$id` not conclusive. Tools exist: `scripts/normalize_schemas.py`, `scripts/schema_lint.py`.
  - Next: Run `make preflight` or `poetry run python scripts/normalize_schemas.py --check` and `scripts/schema_lint.py` in CI.
- C4 Examples linked and validated: WARN
  - Reason: Strict validation requires `scripts/validate_examples.py` via Poetry; not executed here. Examples present.
  - Next: `PYTHONPATH=python/src poetry run python scripts/validate_examples.py --strict --dir examples`.
- C5 Deterministic codegen (no-drift) and artifacts: WARN
  - Evidence: Scripts present (`codegen/gen_ts.sh`, `scripts/ensure_codegen_clean.sh`), CI references them. `typescript/dist/*.d.ts` not found in the repo snapshot (likely built). Ensure drift check runs and fails on diffs.
- C6 Reference hygiene: PASS
  - Evidence: Scripts mention normalizing absolute `$ref` to local (`scripts/normalize_schemas.py`). No mixed `#/defs` vs `defs/` references detected via grep in this snapshot.
- C7 Naming & docs clarity: PASS
  - Evidence: `README.md` documents validation and codegen; Makefile shows preflight. Titles/ids not exhaustively verified without linters; treat spot-check as acceptable.
- C8 CI & preflight parity: PASS
  - Evidence: `.github/workflows/ci.yml` runs `preflight.sh` (with/without codegen-check), sets up Poetry/Node, caches npm. Submodules not used here; step can be added if needed later.
- C9 Canonical schema does not leak DB identifiers: PASS
  - Evidence: No `*_id` properties found in `jsonschema/*.schema.json` by grep; DB identifiers are not defined in canonical schemas.

## Summary: PASS (with WARNs)
- PASS: C1, C2, C6, C7, C8, C9
- WARN: C3 (schema check not executed), C4 (example validation not executed), C5 (codegen drift/artifacts not confirmed)

## Next Actions (ordered, minimal)
1. In CI, run full preflight: `bash ./preflight.sh` (already configured) and ensure failures surface; keep `SKIP_CODEGEN_CHECK` path filter.
2. Locally/CI, execute:
   - `make normalize-check` and `make schema-lint` (C3)
   - `PYTHONPATH=python/src poetry run python scripts/validate_examples.py --strict --dir examples` (C4)
   - `bash scripts/ensure_codegen_clean.sh` (C5)
3. If policy requires checked-in TS artifacts, add `typescript/dist/*.d.ts` to the tree; otherwise document that dist is built on publish.
4. Optionally augment CI to assert `git status --porcelain` is empty after `codegen/gen_ts.sh` (defense-in-depth).
5. Add a brief “Versioning” note linking helpers (`scripts/lib/version.py`, `codegen/lib/version.mjs`) in README to reinforce SSOT.
