# Example Loader (SSOT)

Overview of the in-process loader that imports Synesthetic examples from the synesthetic-schemas submodule (SSOT) with deterministic behavior and idempotence.

Behavior

- Source: `libs/synesthetic-schemas/examples` by default (override with `EXAMPLES_DIR`).
- Validation: uses SSOT Pydantic v2 models; only top-level `$schemaRef` is ignored.
- Serialization: all POST bodies use `model_dump(mode="json")`.
- Idempotence: pre-checks by name via `GET /.../` and skips existing; otherwise treats 409 as skip.
- Scope: imports SynestheticAsset examples by default; standalone components are gated.
- Headers: sends `X-Schema-Version` unless disabled.

Environment Flags

- `EXAMPLES_DIR`: override example root (default SSOT path).
- `ONLY_ASSETS` (0|1, default 0): when 1, import only assets.
- `INCLUDE_COMPONENTS` (0|1, default 0): when 1, import ShaderLib/Shader/Tone/Haptic/Control/Modulation after assets.
- `INCLUDE_SKIP` (0|1, default 0): include files under any `*_skip` directory.
- `DRY_RUN` (0|1, default 0): validate/plan only; no POSTs or mirroring.
- `API_MODE` (`inproc`|`http`, default `inproc`): send through `TestClient` or HTTP (`API_BASE_URL`).
- `API_BASE_URL` (default `http://localhost:8000`): used when `API_MODE=http`.
- `DISABLE_SCHEMA_HEADER` (0|1, default 0): omit `X-Schema-Version` header.

Routes

- Assets: `POST /synesthetic-assets/nested`
- Optional components (gated):
  - ShaderLib: `POST /shader_libs/` (local model)
  - Shader: `POST /shaders/`
  - Tone: `POST /tones/`
  - Haptic: `POST /haptics/`
  - ControlBundle: `POST /controls/`
  - Modulation: `POST /modulations/`

Notes

- RuleBundle standalone import is omitted (no list endpoint/uniqueness) to keep idempotence simple.
- When `EXAMPLES_DIR` points to legacy `app/examples`, components are included by default to preserve existing tests.

Examples

- Dry run (plan only):
  - `DRY_RUN=1 python -m app.load_examples`
- Include components:
  - `INCLUDE_COMPONENTS=1 python -m app.load_examples`

