#!/bin/bash
set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

DEBUG=false
AGENTS_ONLY=false
EXAMPLE7_ONLY=false
ASSET_EXAMPLE=""
SERVE=false
HOST="0.0.0.0"
PORT="8000"

while [[ "$#" -gt 0 ]]; do
  case $1 in
    -d|--debug) DEBUG=true ;;
    -a|--agents) AGENTS_ONLY=true ;;
    -e7|--example7) EXAMPLE7_ONLY=true ;;
    -e|--example) ASSET_EXAMPLE="$2"; shift ;;
    --serve) SERVE=true ;;
    --host) HOST="$2"; shift ;;
    --port) PORT="$2"; shift ;;
    -h|--help)
      cat <<EOF
Usage: ./codex.sh [options]
  -d, --debug         Enable debug output
  -a, --agents        Run only agent tests
  -e7, --example7     Run only Example7 agent tests
  -e, --example FILE  Run diagnostic for specific example file
  --serve             Initialize DB, load examples, then SERVE FastAPI (no tests)
  --host HOST         Host for --serve (default 0.0.0.0)
  --port PORT         Port for --serve (default 8000)
EOF
      exit 0 ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
  shift
done

TEST_DB=tests/data/test.db
export DATABASE_URL="sqlite:///${TEST_DB}?check_same_thread=False"
export TESTING=1
export GEMINI_API_KEY="${GEMINI_API_KEY:-dummy-key}"
export GEMINI_MODEL="${GEMINI_MODEL:-gemini-test-model}"

cleanup() {
  echo -e "${YELLOW}🧹 Cleaning environment...${NC}"
  rm -f "$TEST_DB"
  find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find . -type f -name '*.py[co]' -delete 2>/dev/null || true
}

setup_db() {
  echo -e "${BLUE}🔧 Initializing database...${NC}"
  mkdir -p "$(dirname "$TEST_DB")"
  python3 - <<'PY'
from app.models.db import Base, engine
Base.metadata.create_all(bind=engine)
PY
  echo -e "${GREEN}✅ Database ready${NC}"
}

load_examples() {
  echo -e "${BLUE}📥 Loading example data...${NC}"
  if [ "$DEBUG" = true ]; then
    python3 -m app.load_examples || true
  else
    python3 - <<'PY'
import logging
from app.load_examples import load_examples
logging.basicConfig(level=logging.INFO)
success, errors = load_examples()
if errors:
    print('\nErrors encountered:')
    for e in errors:
        print(f"- {e}")
if not success:
    exit(1)
PY
  fi
}

check_imports() {
  echo -e "${BLUE}📊 Checking Import Status:${NC}"
  python3 - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
endpoints = ["/shader_libs/", "/shaders/", "/tones/", "/controls/", "/synesthetic-assets/"]
for ep in endpoints:
    try:
        resp = client.get(ep)
        count = len(resp.json()) if resp.status_code == 200 else 'error'
        print(f"  • {ep.strip('/')}: {count}")
    except Exception as e:
        print(f"  • {ep.strip('/')}: error {e}")
PY
}

test_mcp_logging() {
  echo -e "${BLUE}🔧 Testing MCP Command Logging Infrastructure:${NC}"
  python3 - <<'PY'
from app.services.mcp_logger import log_mcp_command
from app.models.db import get_db
db = next(get_db())
try:
    log_id = log_mcp_command(
        command_type='test_command',
        payload={'test': 'data'},
        status='success',
        request_id='test_request',
        asset_id='test_asset',
        db=db
    )
    print('  • MCP logging test passed' if log_id else '  • MCP logging returned None')
finally:
    db.close()
PY
}

serve_api() {
  echo -e "${BLUE}🚀 Serving FastAPI on ${HOST}:${PORT}${NC}"
  # Ensure uvicorn is available via requirements.txt
  exec python3 -m uvicorn app.main:app --host "${HOST}" --port "${PORT}"
}

run_tests() {
  echo -e "${BLUE}🧪 Running tests...${NC}"
  if [ "$EXAMPLE7_ONLY" = true ]; then
    echo -e "${YELLOW}🎯 Running Example7-specific agent tests...${NC}"
    pytest tests/agents/test_example7_agent.py -v
  elif [ -n "$ASSET_EXAMPLE" ]; then
    echo -e "${YELLOW}🎯 Running diagnostic for asset: $ASSET_EXAMPLE${NC}"
    python3 lab/scripts/diagnose_asset.py "$ASSET_EXAMPLE"
  elif [ "$AGENTS_ONLY" = true ]; then
    pytest tests/agents/
  elif [ -d "./features" ]; then
    pytest tests/ features/
  else
    pytest tests/
  fi
}

echo -e "${BLUE}🧪 SDFK Backend Local Runner${NC}"
cleanup
setup_db
load_examples
check_imports
test_mcp_logging

if [ "$SERVE" = true ]; then
  serve_api
else
  run_tests
fi
