# Repository Truth Audit — SSOT Interrogation v1.6g+

**Role**  
You are a blunt, accuracy-obsessed repo auditor. No speculation. Deterministic output only.

**Objective**  
Interrogate the repository and write a complete SSOT audit to `docs/SSOT_AUDIT.md`. Overwrite the file. Do not print the report to stdout.

---

## Authoritative Inputs (only these)
- Code: `app/{models,schemas,routers,services,utils}/**`
- Runtime artifacts (canonical context from this run; do not regenerate):
  - `docs/_routes.md` (enumerated APIRoute table)
  - `docs/_openapi.json` (OpenAPI schema dump)
- Config: `.env.example`, `app/config.py`
- Protos (if present): `protos/**`
- Scripts: `local.sh`, `codex.sh`, `test.sh` (if present)
- Scripts/Tests for ENV discovery: `preflight.sh`, `run_*.sh`, `tests/**` (ENV keys only)

---

## Grounding Rules
1. **Routes (authoritative):** Build the route table *from* `_routes.md`; fill response models strictly from `_openapi.json`. Do not regenerate either.
2. **Entities:**  
   - ORM models: classes under `app/models/**` that are SQLAlchemy models.  
   - API schemas: `pydantic.BaseModel` classes under `app/schemas/**` **after Helper Filter**.  
   - “Used in Routes” is derived solely from the response/request model names you resolved from `_openapi.json` for the routes listed in `_routes.md`.
3. **Config lineage:** collect from `.env.example`, `app/config.py`, `os.getenv`/`environ.get` in `app/**`, and the listed scripts/tests.
4. **Strict unknowns:** if something cannot be resolved, write exactly `missing` (entities/config) or `None` (response model). Never invent names or suffixes.  
   - **Gating:** A response model name must exactly match a class name present in `_openapi.json`. If Codex produces a name not in that file (e.g., `RuleBundleSchema-Output`), replace it with `None` and optionally annotate drift in the Field Drift Report.  
5. **Deterministic ordering:** Entities A–Z; Routes sorted by **Path ASC** then **Methods ASC** (methods comma-sorted); ENV keys A–Z. No HTML in table cells.

---

## Static Reasoning Allowances (what you *can* figure out)
- Map ORM↔schema entities (normalize variants: `X`, `XBase`, `XCreate`, `XUpdate`, `XResponse` ⇒ entity **X**; list concrete schema class names in the cell).
- Compute field drift between model vs schema groups (presence, requiredness/nullability, type bucket).
- Detect routers that contribute zero runtime routes (router modules under `app/routers/**` with no entries in `_routes.md`).
- You may not regenerate routes/OpenAPI or guess missing types; unknowns collapse to `missing`/`None`.

---

## Parsing & Resolution Specs (deterministic)
**`_routes.md` table**  
- Expect header: `Method(s) | Path | Handler | ResponseModel`.  
- Data row regex (single line per row):  
  `(?P<methods>[A-Z,]+)\s*\|\s*(?P<path>/\S*)\s*\|\s*(?P<handler>[\w\.]+:[\w]+(?:\s*;\s*[\w\.]+:[\w]+)*)\s*\|\s*(?P<resp>[^|]+)`  
- Canonicalize: Methods comma-sorted; one row per **Path**; if multiple methods per path, keep **method order** consistent between `Handler` and `Response Model` columns using `;` as the separator.

**`_openapi.json` response model resolution**  
- For each `(method, path)` from `_routes.md`:  
  - Prefer `responses["200"].content[*].schema`.  
  - If `$ref` present, the class name is the tail of the `$ref`.  
  - If `type: array` with `items.$ref`, render as `List[Class]`.  
  - If unresolvable or missing: write `None`.  
- Use **exact** class names present in `_openapi.json`. Never invent or suffix (no `-Output`, `-Result`, etc.). Any mismatch = `None`.

---

## Helper Filter (strict)
Exclude schemas with names matching:
`*Request|*Response|*Result|*Error*|*Detail*|*Status|*Query|*Params|*Spec|*Config|*Option*|*Patch*|*Nested*|*Preview*|*Candidate*`
**unless** that exact class name appears in the **Route Reality Check** response model column. Excluded helpers must not appear in the Entity Map.

---

## Proto? Flag
Set to `Yes` **only if** the entity is backed by a `.proto` under `protos/**` **or** that entity is used by `/protobuf-*` routes in `_routes.md`. Otherwise `No`.

---

## Config Status Rules (canonical)
- `OK`: key is **declared** (in `.env.example` or `app/config.py`) **and** **used** (referenced via `os.getenv`/`environ.get`/Settings).  
- `Declared-not-used`: declared but never referenced.  
- `Used-not-declared`: referenced in code/tests/scripts but not declared.  
- `Duplicate/Conflicting`: duplicates with different defaults or conflicting declarations.

Statuses must use this exact casing.

---

## Field Drift Report (strict)
- For entities that have both model and schema group (post-normalization), list diffs:  
  - presence (`missing in model` / `missing in schema`),  
  - requiredness/nullability drift,  
  - type class drift in buckets `{vector|uuid|datetime|json|dict|list|str|int|float|bool}`.  
- Max 15 items/entity; first 15 A–Z, then append `… (+N more)`.

---

## Report Format (exact headers, in order)
1. `## SSOT Candidates`  
   *(No bullets or prose. Leave empty **or** write the single fixed line `Inputs: code, routes snapshot, openapi snapshot, config.`)*
2. `## Entity Map (Parity Matrix)`  
   **Columns:** `Entity | ORM Model (file:Class) | API Schema(s) (file:Class) | Used in Routes (paths) | Proto? | Status`
3. `## Field Drift Report`
4. `## Route Reality Check`  
   **Columns:** `Method(s) | Path | Handler (from _routes.md) | Response Model (from _openapi.json)`
5. `## Config Lineage Sanity`  
   **Columns:** `ENV Key | Purpose | Used In (files) | Status`
6. `## Orphans & Dead Code`
7. `## Drift Risk Score`  
   Single line: `Score: N (1–5) — <one-clause justification>`
8. `## Decision & Rationale`  
   Emit exactly three lines, no extras:  
   - `Counts: models=X, schema-groups=Y, used-in-routes=Z, field-drifts=K, routes=M, env-keys=E, helpers-excluded=H.`  
   - `SSOT: <API-first|DB-first|Mixed/None>.`  
   - `Basis: <one sentence referencing concrete counts only>.`
9. `## Cleanup Plan (Task/Validation Pairs)`  
   Output **exactly four** pairs:  
   - `Task: <surgical change>`  
   - `Validation: <deterministic check>`

---

## Output Contract
- Overwrite `docs/SSOT_AUDIT.md`.  
- Do not print to stdout.  
- Deterministic: same repo + same `_routes.md` + same `_openapi.json` ⇒ identical output.

Begin now.
