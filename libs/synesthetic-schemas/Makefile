SHELL := /bin/bash

# Require Poetry-managed Python for reproducibility
ifeq (,$(shell command -v poetry 2>/dev/null))
$(error Poetry is required. Install Poetry or run 'nix develop')
endif

PY := poetry run python

.PHONY: schema-lint normalize normalize-check codegen-py codegen-ts codegen-check validate preflight preflight-fix bump-version audit

normalize:
	@$(PY) scripts/normalize_schemas.py

normalize-check:
	@$(PY) scripts/normalize_schemas.py --check

schema-lint:
	@$(PY) scripts/schema_lint.py

codegen-py:
	@poetry run bash codegen/gen_py.sh

codegen-ts:
	@bash codegen/gen_ts.sh

codegen-check:
	@bash scripts/ensure_codegen_clean.sh

validate:
	@PYTHONPATH=python/src $(PY) scripts/validate_examples.py --strict --dir examples

preflight: normalize-check schema-lint codegen-check validate
	@echo "preflight OK"

# Preflight that also writes normalization first (auto-fix drift)
preflight-fix:
	@$(MAKE) normalize
	@$(MAKE) preflight

# Bump schema version and normalize schemas
# Usage: make bump-version VERSION=0.7.1
bump-version:
	@if [[ -z "$(VERSION)" ]]; then echo "Usage: make bump-version VERSION=X.Y.Z" >&2; exit 2; fi
	@$(PY) scripts/bump_version.py --set "$(VERSION)"
	@$(PY) scripts/update_docs_frontmatter.py --version "$(VERSION)"

audit:
	@$(PY) scripts/ssot_audit.py --spec meta/prompts/ssot.audit.json
