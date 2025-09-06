#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  WARNING: This will completely reset all data${NC}"
echo -e "${YELLOW}⚠️  Are you sure you want to continue? [y/N]${NC}"
read -r response

if [[ ! "$response" =~ ^[yY]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo -e "${RED}🧨 Nuking SDFK backend data...${NC}"

# Stop all services
echo "🛑 Stopping services..."
docker compose down

# Remove all data
echo "🗑️  Removing all data..."
sudo rm -rf data/postgres/*
sudo rm -rf data/redis/*

# Drop and recreate the PostgreSQL database
echo "🗑️  Dropping and recreating PostgreSQL database..."
docker compose up -d db
until docker compose exec db pg_isready -U postgres; do
    echo -e "${YELLOW}Waiting for database...${NC}"
    sleep 2
done
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS sdfk;"
docker compose exec db psql -U postgres -c "CREATE DATABASE sdfk;"

echo -e "${GREEN}✅ PostgreSQL database reset complete.${NC}"

echo -e "${GREEN}✅ Nuke complete! All data has been reset.${NC}"
echo "Run './test.sh' to start fresh."
