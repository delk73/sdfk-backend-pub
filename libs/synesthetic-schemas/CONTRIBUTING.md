---
version: v0.7.3
lastReviewed: 2025-09-01
owner: delk73
---

# Contributing

Thanks for helping improve Synesthetic Schemas! This repo is the single source of truth (SSOT) for schemas and generated models. The pipeline is designed to be deterministic and CI‑mirrored.

## Quick Start

This project uses [Nix](https://nixos.org/) to provide a reproducible development environment.

1.  **Install Nix:** If you don't have Nix installed, you can install it by following the instructions at [https://nixos.org/download.html](https://nixos.org/download.html).

2.  **Enable Nix Flakes:** You'll need to enable the experimental "flakes" feature. Add the following line to your Nix configuration file (`~/.config/nix/nix.conf` or `/etc/nix/nix.conf`):
    ```
    experimental-features = nix-command flakes
    ```

3.  **Start the development shell:** Open a terminal in your project's root directory and run:
    ```bash
    nix develop
    ```
    This command will download and configure all the necessary dependencies.

4.  **Install project dependencies:** Once you are inside the Nix shell, run:
    ```bash
    npm install
    poetry install
    ```

## Preflight (must pass before pushing)

- Run the exact checks that CI runs:

```bash
./preflight.sh
```

This runs, in order: normalization check → schema lint → codegen drift check → example validation + round‑trip. If anything fails, fix locally and re‑run.

Tip: To auto‑rewrite schemas into canonical form first, use:

```bash
make preflight-fix
```

## Versioning Rules

- `version.json` is the single source of the schema version.
- Any change to canonical schemas must bump the version:

```bash
make bump-version VERSION=X.Y.Z
```

This updates `version.json` and normalizes all schemas to set `$schema`, `$id`, `x-schema-version`, and stable absolute `$ref`s.

## Examples

- Each example JSON must include a top‑level `$schemaRef`, e.g.:

```json
{ "$schemaRef": "jsonschema/synesthetic-asset.schema.json", ... }
```

- Validate examples with round‑trip:

```bash
PYTHONPATH=python/src python scripts/validate_examples.py --strict --dir examples
```

## Generated Code

- Generated outputs are committed:
  - Python models in `python/src/synesthetic_schemas/`
  - TypeScript declarations in `typescript/src/`
- Do not edit generated files by hand.
- To regenerate deterministically:

```bash
make codegen-py codegen-ts
```

CI enforces that the working tree is clean after codegen (`scripts/ensure_codegen_clean.sh`).

## Naming Hygiene

- Prefer a single canonical class/name per concept. Avoid dual‑class hedging in validators and tokens.
- Canonical names: `RuleBundle`, `ControlBundle`, `Control` (avoid `*Schema` and `ControlParameter` in titles, tokens, or validator lookups).

## Commit Hygiene

- Keep changes focused and minimal.
- Include a brief rationale in commit messages when changing schemas.

## Need Help?

Open an issue or start a draft PR describing the intent; maintainers will help align with the SSOT pipeline.
