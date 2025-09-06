#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🧹 Cleaning up SDFK backend services...${NC}"

# Stop services first
echo "📥 Stopping services..."
docker compose down

# Fix permissions only if needed, but preserve data
if [ -d "./data" ]; then
    echo "🔐 Checking permissions..."
    if [ "$(stat -c %U ./data)" != "$(whoami)" ]; then
        sudo chown -R $USER:$USER ./data
    fi
fi

echo -e "${GREEN}✨ Cleanup complete! Database data is preserved.${NC}"
echo "Run './test.sh' to restart the services."
