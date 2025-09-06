#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default mode
FIX_MODE=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --fix) FIX_MODE=true ;;
        -f) FIX_MODE=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

echo -e "${BLUE}🔍 Linting Python code...${NC}"

if [ "$FIX_MODE" = true ]; then
    echo -e "${YELLOW}🔧 Auto-fixing mode enabled${NC}"

    # Install additional tools if not present
    echo -e "${BLUE}📦 Ensuring auto-fix tools are available...${NC}"
    pip install autopep8 autoflake > /dev/null 2>&1 || true

    # Format with black first
    echo -e "${BLUE}🖤 Formatting code with Black...${NC}"
    black app tests > /dev/null

    # Remove unused imports with autoflake
    echo -e "${BLUE}🗑️  Removing unused imports...${NC}"
    autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive app/ tests/ . || true
    
    # Auto-fix common issues with autopep8 (more aggressive)
    echo -e "${BLUE}🔧 Auto-fixing whitespace and formatting issues...${NC}"
    autopep8 --in-place --aggressive --aggressive --max-line-length=120 --recursive app/ tests/ . || true
    
    # Remove trailing whitespace from all Python files (more thorough)
    echo -e "${BLUE}🧹 Removing trailing whitespace...${NC}"
    find app/ tests/ -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} \; 2>/dev/null || true
    find . -maxdepth 1 -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} \; 2>/dev/null || true
    
    echo -e "${GREEN}✅ Auto-fixes applied${NC}"
fi

# Check formatting with black
echo -e "${BLUE}📏 Checking formatting with Black...${NC}"
black --check app tests || true

# Run flake8 to check for remaining issues
echo -e "${BLUE}📊 Running flake8 check...${NC}"
if flake8 --statistics; then
    echo -e "${GREEN}✅ No style issues found!${NC}"
else
    echo -e "${YELLOW}⚠️  Linting issues found above${NC}"

    if [ "$FIX_MODE" = false ]; then
        echo -e "\n${BLUE}💡 Tip: Run './lint.sh --fix' to auto-fix many of these issues${NC}"
    fi
fi

# Run mypy type checking
echo -e "${BLUE}🔎 Running mypy type checks...${NC}"
mypy --config-file .mypy.ini app tests || true

echo -e "\n${BLUE}📋 Usage:${NC}"
echo "  ./lint.sh          - Check for linting issues"
echo "  ./lint.sh --fix    - Auto-fix issues and then check"
echo "  ./lint.sh -f       - Short form of --fix"