SHELL := bash

.PHONY: poetry-use-311 poetry-install poetry-lock sync-reqs

# Ensure Poetry is present and the env uses Python 3.11+
poetry-use-311:
	@command -v poetry >/dev/null 2>&1 || { \
		echo "Poetry not found. Install: python3 -m pip install --user poetry"; \
		exit 2; \
	}
	@poetry env use 3.11 >/dev/null 2>&1 || true
	@poetry run python -c 'import sys; v=sys.version_info[:2];\
	 assert v>=(3,11), "Poetry env Python < 3.11. Fix with: poetry env use 3.11";\
	 print(f"Poetry Python: {sys.version.split()[0]}")'

# Install deps into the Poetry environment
poetry-install: poetry-use-311
	@poetry install

# Generate/refresh the lockfile
poetry-lock: poetry-use-311
	@poetry lock

# Sync requirements.txt from Poetry lock (for Docker/CI)
sync-reqs: poetry-lock
	@poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev
	@# Normalize local path dependency to a relative editable path for Docker builds
	@awk '{ if ($$0 ~ /libs\/synesthetic-schemas\/python/) { print "-e ./libs/synesthetic-schemas/python" } else { print } }' requirements.txt > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt
	@echo "requirements.txt exported and normalized (path deps -> -e ./libs/synesthetic-schemas/python)"
