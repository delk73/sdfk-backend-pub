#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Compose command (override if needed)
COMPOSE=${COMPOSE:-"docker compose"}

# Defaults
DEBUG=false
AGENTS_DEBUG=false
SPECIFIC_EXAMPLE=""
AGENT_MODE=""

# Load .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

usage() {
  echo "Usage: ./test.sh [-d|--debug] [-a|--agents] [-e7|--example7] [-e|--example FILENAME] [--agents-debug]"
  echo "  -d, --debug         Show detailed debug information during import"
  echo "  -a, --agents        Test all examples using the generic agent system"
  echo "  -e7, --example7     Test Example7 using the generic agent system"
  echo "  -e, --example       Test specific example file using the agent system"
  echo "  --agents-debug      Enable verbose agent debugging output"
  echo "  -h, --help          Show this help message"
  echo ""
  echo "Examples:"
  echo "  ./test.sh -a"
  echo "  ./test.sh -e SynestheticAsset_Example1.json"
  echo "  ./test.sh -a --agents-debug"
}

# Arg parse
while [[ "$#" -gt 0 ]]; do
  case $1 in
    -d|--debug) DEBUG=true ;;
    -a|--agents) AGENT_MODE="all" ;;
    -e7|--example7) AGENT_MODE="example7" ;;
    -e|--example) SPECIFIC_EXAMPLE="$2"; shift ;;
    --agents-debug) AGENTS_DEBUG=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown parameter: $1"; usage; exit 1 ;;
  esac
  shift
done

# Fail if Pydantic v1 artifacts remain
if git grep -nE 'pydantic\.v1|root_validator|parse_obj|\.dict\(|\.json\(' app/shaderlib app/routers/shader_libs.py >/dev/null; then
  echo "Forbidden Pydantic v1 usage found" >&2
  exit 1
fi

# Fail if legacy Automata/GridControl terms remain
if git grep -nEi '\bautomata\b|\bgrid[_-]?control\b' app tests docs >/dev/null; then
  echo "Legacy GridControl/Automata reference found" >&2
  exit 1
fi

# Ensure rule_bundle is referenced in app/
if ! git grep -n 'rule_bundle' app >/dev/null; then
  echo "Missing rule_bundle reference in app/" >&2
  exit 1
fi

# ------------- Helpers for data ownership/cleanup -------------

# Try to wipe a bind-mounted path from inside a service container as root
# Usage: wipe_bind_mount_via_container <service> <container_path>
wipe_bind_mount_via_container() {
  local svc="$1"
  local cpath="$2"
  # Remove regular and dotfiles, ignore if empty
  $COMPOSE run --rm -u root "$svc" sh -lc \
    "rm -rf \"$cpath\"/* \"$cpath\"/.[!.]* \"$cpath\"/..?* 2>/dev/null || true"
}

# Wipe a host directory, fallback to sudo if needed
# Usage: wipe_dir_host <path>
wipe_dir_host() {
  local p="$1"
  if [ ! -d "$p" ]; then
    return 0
  fi
  rm -rf "$p" 2>/dev/null && return 0
  if command -v sudo >/dev/null 2>&1; then
    sudo rm -rf "$p"
  else
    echo -e "${YELLOW}Warning: could not remove ${p}; consider running with sudo${NC}"
  fi
}

# Ensure local bind mount dirs exist and are usable by containers
setup_data_dirs() {
  # Postgres
  if [ ! -d "./data/postgres" ]; then
    mkdir -p ./data/postgres
    # 999:999 is common for postgres image
    if command -v sudo >/dev/null 2>&1; then
      sudo chown -R 999:999 ./data/postgres || true
      sudo chmod 700 ./data/postgres || true
    else
      chmod 777 ./data/postgres || true
    fi
  fi

  # Redis
  if [ ! -d "./data/redis" ]; then
    mkdir -p ./data/redis
    if command -v sudo >/dev/null 2>&1; then
      sudo chown -R 999:999 ./data/redis || true
      sudo chmod 700 ./data/redis || true
    else
      chmod 777 ./data/redis || true
    fi
  fi
}

# ------------- Main tasks -------------

cleanup() {
  echo -e "${YELLOW}Stopping and removing containers...${NC}"
  $COMPOSE down --remove-orphans || true

  echo -e "${YELLOW}Wiping bind-mounted data (container-first)...${NC}"
  # These paths are the usual locations inside official images; adjust if needed
  wipe_bind_mount_via_container db "/var/lib/postgresql/data" || true
  wipe_bind_mount_via_container redis "/data" || true

  echo -e "${YELLOW}Wiping host data directories (fallback)...${NC}"
  wipe_dir_host "./data/postgres"
  wipe_dir_host "./data/redis"

  echo -e "${YELLOW}Cleaning Python caches...${NC}"
  find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find . -type f -name "*.pyc" -delete 2>/dev/null || true
  find . -type f -name "*.pyo" -delete 2>/dev/null || true
  find . -type f -name "*.pyd" -delete 2>/dev/null || true

  echo -e "${GREEN}Cleanup complete.${NC}"
}

build_and_test() {
  echo "Checking if Docker is running..."
  if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
  fi

  # Keep requirements.txt in sync with pyproject/poetry if possible
  if command -v poetry >/dev/null 2>&1; then
    echo "Syncing requirements.txt from Poetry (best-effort)..."
    if poetry env use 3.11 >/dev/null 2>&1; then
      poetry lock >/dev/null 2>&1 || true
      poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev >/dev/null 2>&1 || true
      # Normalize local path dependency to relative editable path for Docker context
      if [ -f requirements.txt ]; then
        awk '{ if ($$0 ~ /libs\/synesthetic-schemas\/python/) { print "-e ./libs/synesthetic-schemas/python" } else { print } }' requirements.txt > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt || true
      fi
    else
      echo -e "${YELLOW}Poetry found but Python 3.11 not selected; skipping sync.${NC}"
    fi
  fi

  echo "Building containers..."
  $COMPOSE build

  echo "Setting up data directories..."
  setup_data_dirs

  echo "Configuring sysctl for Redis (best effort)..."
  if command -v sudo >/dev/null 2>&1; then
    sudo sysctl -w vm.overcommit_memory=1 || true
    sudo sysctl -w net.core.somaxconn=1024 || true
  else
    sysctl -w vm.overcommit_memory=1 2>/dev/null || true
    sysctl -w net.core.somaxconn=1024 2>/dev/null || true
  fi

  echo "Starting services..."
  $COMPOSE down --remove-orphans || true
  $COMPOSE up -d

  echo "Waiting for database to be ready..."
  until $COMPOSE exec -T db pg_isready -U postgres > /dev/null 2>&1; do
    echo "Waiting for database..."
    sleep 2
  done

  echo "Checking database initialization..."
  TABLES_EXIST="$($COMPOSE exec -T db psql -U postgres -d sdfk -c '\dt' 2>/dev/null || true)"
  if ! echo "$TABLES_EXIST" | grep -q 'synesthetic_assets' || ! echo "$TABLES_EXIST" | grep -q 'mcp_command_log'; then
    echo "Database schema incomplete. Creating/updating schema..."
    $COMPOSE exec -T web python -c 'from app.models import engine, Base; Base.metadata.create_all(bind=engine)'
  fi

  echo "Waiting for web service..."
  max_retries=30
  retry_count=0
  while ! $COMPOSE exec -T web python -c "from app.models import engine; engine.connect()" >/dev/null 2>&1; do
    if [ $retry_count -ge $max_retries ]; then
      echo -e "${RED}Error: Web service failed to start within 30 seconds${NC}"
      exit 1
    fi
    sleep 1
    retry_count=$((retry_count+1))
  done

#########################################################################
### STRICT SSOT GUARDRAIL: assert DB backend is Postgres (noise-safe) ###
#########################################################################
echo "Asserting web uses Postgres…"

# Run a tiny Python snippet that disables logging, then prints only the backend.
OUT="$($COMPOSE exec -T web python - <<'PY' 2>/dev/null
import logging, sys
logging.disable(logging.CRITICAL)         # silence app loggers
from app.models import engine
sys.stdout.write(engine.url.get_backend_name())
PY
)"

# Extract just a known backend token in case anything leaks to stdout.
BACKEND="$(echo "$OUT" | grep -Eo 'postgresql|sqlite|mysql|mariadb|oracle' | head -n1)"

if [ "$BACKEND" != "postgresql" ] || [ -z "$BACKEND" ]; then
  echo -e "${RED}Web is not using Postgres (got: ${OUT:-<empty>}). Failing strict run.${NC}"
  exit 1
fi
########################################################################


  echo "Dumping strict (Postgres) runtime artifacts…"
  $COMPOSE exec -T web python - <<'PY'
import json, os
from fastapi.routing import APIRoute
from app.main import app

os.makedirs("/app/docs", exist_ok=True)

with open("/app/docs/_openapi.postgres.json", "w") as f:
    json.dump(app.openapi(), f, indent=2, sort_keys=True)

rows = []
for r in app.routes:
    if isinstance(r, APIRoute):
        methods = ",".join(sorted(getattr(r, "methods", []) or []))
        func = r.endpoint
        mod  = getattr(func, "__module__", "?")
        name = getattr(func, "__name__", "?")
        resp = "-"
        if getattr(r, "response_model", None):
            try:
                resp = getattr(r.response_model, "__name__", "-")
            except Exception:
                resp = str(r.response_model)
        rows.append((r.path, methods, mod, name, resp))

rows.sort(key=lambda t: (t[0], t[1]))
with open("/app/docs/_routes.postgres.md", "w") as f:
    print("# Runtime Routes (Postgres strict)\n", file=f)
    print("Method(s) | Path | Handler | ResponseModel", file=f)
    print("---|---|---|---", file=f)
    for path, methods, mod, name, resp in rows:
        print(f"{methods} | {path} | {mod}:{name} | {resp}", file=f)
PY

  # Compare without failing the build under set -e
  if [ -f docs/_openapi.json ]; then
    echo "Comparing OpenAPI (local vs strict)…"
    if ! diff -u docs/_openapi.json docs/_openapi.postgres.json; then
      echo -e "${YELLOW}OpenAPI diff detected (review).${NC}"
    fi
  fi
  if [ -f docs/_routes.md ]; then
    echo "Comparing routes (local vs strict)…"
    if ! diff -u docs/_routes.md docs/_routes.postgres.md; then
      echo -e "${YELLOW}Route diff detected (review).${NC}"
    fi
  fi
  #######################################################################
  ### END STRICT SSOT GUARDRAILS                                      ###
  #######################################################################

  echo "Loading example data..."
  if [ "$DEBUG" = true ]; then
    IMPORT_RESULT="$($COMPOSE exec -T web python -m app.load_examples 2>&1 || true)"
  else
    IMPORT_RESULT="$($COMPOSE exec -T web python -c "
import logging
logging.basicConfig(level=logging.INFO)
from app.load_examples import load_examples
success, errors = load_examples()
if errors:
    print('\\nErrors encountered:')
    for error in errors:
        print(f'\\n- File: {error.filename}')
        print(f'  Type: {error.error_type}')
        print(f'  Details: {error.message}')
if not success:
    raise SystemExit(1)
" 2>&1 || true)"
  fi

  if echo "$IMPORT_RESULT" | grep -qi "Errors encountered" || echo "$IMPORT_RESULT" | grep -qi "Traceback"; then
    echo -e "${RED}Failed to load example data${NC}"
    echo -e "${YELLOW}Error details:${NC}"
    echo "$IMPORT_RESULT"
    echo "Running with debug output for more details..."
    $COMPOSE exec -T web python -m app.load_examples || true
  else
    echo -e "${GREEN}Example data loaded successfully${NC}"
  fi

  echo "Services ready:"
  echo "  - API: http://localhost:8000"
  echo "  - API Docs: http://localhost:8000/docs"
  echo "  - Database: postgresql://localhost:5432"

  echo "Running tests..."
  if [ -n "$AGENT_MODE" ] || [ -n "$SPECIFIC_EXAMPLE" ]; then
    run_agent_diagnostics
  fi
  PYTEST_TARGETS="tests/unit tests/routers"
  if [ "$RUN_SLOW" = "1" ] || [ -n "$SERVER_URL" ]; then
    PYTEST_TARGETS="tests"
  fi
  if [ -d "./features" ]; then
    $COMPOSE exec -T web pytest $PYTEST_TARGETS features/
  else
    $COMPOSE exec -T web pytest $PYTEST_TARGETS
  fi
}

check_imports() {
  echo -e "\n${BLUE}Checking Import Status:${NC}"

  # Do not re-seed in summary to avoid inflating counts; run importer explicitly when needed.

  echo -e "\n${YELLOW}ShaderLib:${NC}"
  SHADER_LIBS="$($COMPOSE exec -T web curl -s http://localhost:8000/shader_libs/ || true)"
  echo "$SHADER_LIBS" | jq -r '.[] | "  - " + .name' 2>/dev/null || echo "  jq not available or no data"
  SHADER_LIB_COUNT=$(echo "$SHADER_LIBS" | jq 'length' 2>/dev/null || echo 0)
  echo -e "${BLUE}Total: $SHADER_LIB_COUNT${NC}"

  echo -e "\n${YELLOW}Shaders:${NC}"
  SHADERS="$($COMPOSE exec -T web curl -s http://localhost:8000/shaders/ || true)"
  echo "$SHADERS" | jq -r '.[] | "  - " + .name' 2>/dev/null || echo "  jq not available or no data"
  SHADER_COUNT=$(echo "$SHADERS" | jq 'length' 2>/dev/null || echo 0)
  echo -e "${BLUE}Total: $SHADER_COUNT${NC}"

  echo -e "\n${YELLOW}Tones:${NC}"
  TONES="$($COMPOSE exec -T web curl -s http://localhost:8000/tones/ || true)"
  echo "$TONES" | jq -r '.[] | "  - " + .name' 2>/dev/null || echo "  jq not available or no data"
  TONE_COUNT=$(echo "$TONES" | jq 'length' 2>/dev/null || echo 0)
  echo -e "${BLUE}Total: $TONE_COUNT${NC}"

  echo -e "\n${YELLOW}Controls:${NC}"
  CONTROLS="$($COMPOSE exec -T web curl -s http://localhost:8000/controls/ || true)"
  echo "$CONTROLS" | jq -r '.[] | "  - " + .name' 2>/dev/null || echo "  jq not available or no data"
  CONTROL_COUNT=$(echo "$CONTROLS" | jq 'length' 2>/dev/null || echo 0)
  echo -e "${BLUE}Total: $CONTROL_COUNT${NC}"

  echo -e "\n${YELLOW}Synesthetic Assets:${NC}"
  ASSETS="$($COMPOSE exec -T web curl -s http://localhost:8000/synesthetic-assets/ || true)"
  echo "$ASSETS" | jq -r '.[] | "  - " + .name' 2>/dev/null || echo "  jq not available or no data"
  ASSET_COUNT=$(echo "$ASSETS" | jq 'length' 2>/dev/null || echo 0)
  echo -e "${BLUE}Total: $ASSET_COUNT${NC}"

  echo -e "\n${YELLOW}Haptics:${NC}"
  HAPTICS="$($COMPOSE exec -T web curl -s http://localhost:8000/haptics/ || true)"
  echo "$HAPTICS" | jq -r '.[] | "  - " + .name' 2>/dev/null || echo "  jq not available or no data"
  HAPTIC_COUNT=$(echo "$HAPTICS" | jq 'length' 2>/dev/null || echo 0)
  echo -e "${BLUE}Total: $HAPTIC_COUNT${NC}"

  TOTAL_COUNT=$((SHADER_LIB_COUNT + SHADER_COUNT + TONE_COUNT + CONTROL_COUNT + ASSET_COUNT + HAPTIC_COUNT))
  echo -e "\n${GREEN}Total imported items: $TOTAL_COUNT${NC}"
  echo -e "\n${BLUE}==========================================${NC}"
}

show_import_errors() {
  echo -e "\n${RED}Checking for import errors:${NC}"
  $COMPOSE exec -T web python -m app.load_examples || true
  echo -e "\n${BLUE}==========================================${NC}"
}

test_mcp_logging() {
  echo -e "\n${YELLOW}Testing MCP Command Logging Infrastructure:${NC}"

  echo -n "  - Testing MCP model imports... "
  MCP_IMPORT_TEST="$($COMPOSE exec -T web python -c "
from app.models import MCPCommandLog
from app.schemas.mcp import CreateAssetRequest, UpdateParamRequest, ApplyModulationRequest, ValidateAssetRequest
from app.services.mcp_logger import log_mcp_command, update_mcp_log
print('SUCCESS')
" 2>&1 || true)"
  if echo "$MCP_IMPORT_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}ok${NC}"
  else
    echo -e "${RED}fail${NC}"
    echo "    Error: $MCP_IMPORT_TEST"
    return 1
  fi

  echo -n "  - Checking MCP command log table... "
  TABLE_CHECK="$($COMPOSE exec -T db psql -U postgres -d sdfk -c '\dt mcp_command_log' 2>/dev/null | grep -c 'mcp_command_log' || true)"
  if [[ "$TABLE_CHECK" =~ ^[0-9]+$ ]] && [ "$TABLE_CHECK" -gt 0 ]; then
    echo -e "${GREEN}ok${NC}"
  else
    echo -e "${RED}fail${NC}"
    echo "    Error: mcp_command_log table not found"
    return 1
  fi

  echo -n "  - Testing MCP command logging... "
  LOG_TEST="$($COMPOSE exec -T web python -c "
from app.services.mcp_logger import log_mcp_command
from app.models.db import get_db
db = next(get_db())
try:
    log_id = log_mcp_command(
        command_type='test_command',
        payload={'test':'data','name':'Test Asset'},
        status='success',
        request_id='test_request_123',
        asset_id='test_asset_456',
        db=db
    )
    if log_id:
        print('SUCCESS')
    else:
        print('ERROR: None')
finally:
    db.close()
" 2>&1 || true)"
  if echo "$LOG_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}ok${NC}"
  else
    echo -e "${RED}fail${NC}"
    echo "    Error: $LOG_TEST"
    return 1
  fi

  echo -n "  - Testing MCP request model validation... "
  VALIDATION_TEST="$($COMPOSE exec -T web python -c "
from app.schemas.mcp import CreateAssetRequest, UpdateParamRequest, ApplyModulationRequest, ValidateAssetRequest
create_req = CreateAssetRequest(
    name='Test Asset',
    tone={'name':'Test Tone','synth':{'type':'Tone.Synth'}},
    shader={'name':'Test Shader','fragment_shader':'void main() {}'},
    tags=['test']
)
update_req = UpdateParamRequest(asset_id='asset_123', path='shader.u_time', value=1.5)
modulation_req = ApplyModulationRequest(
    asset_id='asset_123',
    modulation_id='test_mod',
    definition={'id':'test_mod','target':'shader.u_r','type':'additive'}
)
validate_req = ValidateAssetRequest(asset_blob={'name':'Test','shader':{'fragment_shader':'void main() {}'}})
print('SUCCESS')
" 2>&1 || true)"
  if echo "$VALIDATION_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}ok${NC}"
  else
    echo -e "${RED}fail${NC}"
    echo "    Error: $VALIDATION_TEST"
    return 1
  fi

  echo -n "  - Testing MCP asset router ping... "
  PING_TEST="$($COMPOSE exec -T web curl -s http://localhost:8000/mcp/asset/ping 2>/dev/null | jq -r '.status' 2>/dev/null || echo 'ERROR')"
  if [ "$PING_TEST" = "MCP asset router live" ]; then
    echo -e "${GREEN}ok${NC}"
  else
    echo -e "${RED}fail${NC}"
    echo "    Error: MCP ping endpoint failed or returned: $PING_TEST"
    return 1
  fi

  echo -e "\n${GREEN}MCP Command Logging Infrastructure: all tests passed.${NC}"
  echo -e "${BLUE}==========================================${NC}"
  return 0
}

run_agent_diagnostics() {
  echo -e "\n${BLUE}Running Agent-Based Example Diagnostics${NC}"
  case "$AGENT_MODE" in
    "all")
      echo -e "${YELLOW}Running comprehensive agent tests for all examples...${NC}"
      run_all_examples_with_agents
      ;;
    "example7")
      echo -e "${YELLOW}Running agent test for Example7...${NC}"
      run_single_example_agent_test "SynestheticAsset_Example7.json"
      ;;
    "")
      ;;
  esac

  if [ -n "$SPECIFIC_EXAMPLE" ]; then
    echo -e "${YELLOW}Running agent test for specific example: $SPECIFIC_EXAMPLE${NC}"
    run_single_example_agent_test "$SPECIFIC_EXAMPLE"
  fi
}

run_all_examples_with_agents() {
  echo -e "\n${BLUE}Testing all examples with generic agent system...${NC}"
  if [ "$AGENTS_DEBUG" = true ]; then
    $COMPOSE exec -T web python run_agent_tests.py --debug
  else
    $COMPOSE exec -T web python run_agent_tests.py
  fi
}

run_single_example_agent_test() {
  local example_file="$1"
  echo -e "\n${BLUE}Running agent test for: $example_file${NC}"
  AGENT_OUTPUT="$($COMPOSE exec -T web python -c "
import asyncio
import json
import sys
from tests.agents.orchestration_agent import OrchestrationAgent
from tests.agents.config_agent import ConfigAgent

async def test_example():
    example_file = '$example_file'
    agents_debug = '$AGENTS_DEBUG' == 'true'
    try:
        print('Loading configuration for', example_file)
        config_agent = ConfigAgent(example_file)
        await config_agent.start()
        if not config_agent.asset:
            print('ERROR: failed to load asset configuration')
            return 'error'
        asset = config_agent.asset
        validation_issues = []
        if hasattr(asset,'shader') and asset.shader:
            if getattr(asset.shader,'fragment_shader',None):
                pass
            else:
                validation_issues.append('Missing shader fragment code')
            if getattr(asset.shader,'uniforms',None):
                pass
            else:
                validation_issues.append('No shader uniforms defined')
        if hasattr(asset,'control_parameters') and asset.control_parameters:
            param_names=[]
            for param in asset.control_parameters:
                if hasattr(param,'parameter'):
                    param_names.append(param.parameter)
                elif isinstance(param,dict):
                    param_names.append(param.get('parameter','unknown'))
            duplicates = [n for n in set(param_names) if param_names.count(n)>1]
            if duplicates:
                validation_issues.append('Duplicate parameters: '+str(duplicates))
        if example_file.startswith('SynestheticAsset_'):
            orchestration_agent = OrchestrationAgent(example_file)
            _ = await orchestration_agent.run(steps=5, dt=0.1)
        await config_agent.stop()
        if validation_issues:
            for issue in validation_issues:
                print('WARNING:', issue)
            return 'warning'
        return 'success'
    except Exception as e:
        if agents_debug:
            import traceback; traceback.print_exc()
        return 'error'

try:
    result = asyncio.run(test_example())
    print('RESULT:', result)
except Exception:
    print('RESULT: error')
" 2>&1)"
  if echo "$AGENT_OUTPUT" | grep -q "RESULT: success"; then
    echo -e "  ${GREEN}AGENT TEST PASSED${NC}"
  elif echo "$AGENT_OUTPUT" | grep -q "RESULT: warning"; then
    echo -e "  ${YELLOW}AGENT TEST PASSED WITH WARNINGS${NC}"
  else
    echo -e "  ${RED}AGENT TEST FAILED${NC}"
  fi
  echo -e "${BLUE}Test output:${NC}"
  echo "$AGENT_OUTPUT" | grep -v "RESULT:" | sed 's/^/  /'
}

test_state_mirror_functionality() {
  echo -e "\n${BLUE}Testing State Mirror Agent Functionality${NC}"
  echo -n "  - Testing state mirroring and broadcasting... "
  MIRROR_TEST="$($COMPOSE exec -T web python -c "
import asyncio
from tests.agents.state_mirror_agent import StateMirrorAgent
async def test_mirror():
    agent = StateMirrorAgent()
    await agent.start({'value': 0})
    captured = []
    agent.subscribe(lambda s: captured.append(s.copy()))
    agent.update('value', 1)
    agent.update('another_value', 42)
    await agent.stop()
    assert agent.state['value'] == 1
    assert agent.state['another_value'] == 42
    assert len(captured) == 2
    assert captured[-1]['value'] == 1
    assert captured[-1]['another_value'] == 42
    return True
try:
    ok = asyncio.run(test_mirror())
    print('SUCCESS' if ok else 'ERROR')
except Exception as e:
    print('ERROR:', e)
" 2>&1)"
  if echo "$MIRROR_TEST" | grep -q "SUCCESS"; then
    echo -e "${GREEN}ok${NC}"
  else
    echo -e "${RED}fail${NC}"
    echo "    Error: $MIRROR_TEST"
    return 1
  fi
  return 0
}

# ------------- Entry -------------

echo -e "${BLUE}SDFK Backend Test Runner${NC}"
if [ "$DEBUG" = true ]; then
  echo -e "${YELLOW}Debug mode: detailed import information will be shown${NC}"
else
  echo -e "${YELLOW}Normal mode: import details hidden (use --debug for verbose output)${NC}"
fi
if [ -n "$AGENT_MODE" ] || [ -n "$SPECIFIC_EXAMPLE" ]; then
  echo -e "${BLUE}Agent diagnostics mode enabled${NC}"
  if [ "$AGENTS_DEBUG" = true ]; then
    echo -e "${YELLOW}Verbose agent debugging enabled${NC}"
  fi
fi
echo -e "${YELLOW}This will reset the database and run all tests${NC}"

cleanup
build_and_test
check_imports
test_mcp_logging
if [ -n "$AGENT_MODE" ] || [ -n "$SPECIFIC_EXAMPLE" ]; then
  test_state_mirror_functionality
fi
echo -e "${GREEN}All done.${NC}"
