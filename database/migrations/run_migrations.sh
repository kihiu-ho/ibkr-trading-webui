#!/bin/bash

# IBKR Trading WebUI - Database Migration Runner
# This script runs all database migrations in order

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE} Database Migration Runner${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Load environment variables from .env file
if [ -f "../../.env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source ../../.env
    set +a
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
else
    echo -e "${RED}ERROR: .env file not found${NC}"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL is not set${NC}"
    exit 1
fi

# Extract database connection details from DATABASE_URL
# DATABASE_URL format: postgresql+psycopg2://user:pass@host:port/dbname?params
DB_URL_NO_DRIVER=$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg2:\/\///')
DB_URL_NO_DRIVER=$(echo "$DB_URL_NO_DRIVER" | sed 's/postgresql+psycopg:\/\///')
DB_URL_NO_DRIVER=$(echo "$DB_URL_NO_DRIVER" | sed 's/postgresql:\/\///')

# Use psql with DATABASE_URL
PSQL_CMD="psql $DATABASE_URL"

echo ""
echo "Running migrations..."
echo ""

# Get list of migration files
MIGRATION_FILES=$(ls -1 [0-9][0-9][0-9]_*.sql 2>/dev/null | sort)

if [ -z "$MIGRATION_FILES" ]; then
    echo -e "${RED}No migration files found${NC}"
    exit 1
fi

# Run each migration
MIGRATION_COUNT=0
for migration_file in $MIGRATION_FILES; do
    echo -n "Running migration: $migration_file ... "
    
    if $PSQL_CMD -f "$migration_file" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        MIGRATION_COUNT=$((MIGRATION_COUNT + 1))
    else
        echo -e "${RED}✗ Failed${NC}"
        echo ""
        echo -e "${RED}Migration failed: $migration_file${NC}"
        echo "Trying to get error details..."
        $PSQL_CMD -f "$migration_file"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN} All migrations completed successfully!${NC}"
echo -e "${GREEN} Total migrations run: $MIGRATION_COUNT${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verify critical tables exist
echo "Verifying tables..."
TABLES=("workflow_lineage" "symbols" "user_sessions" "portfolio_snapshots")

for table in "${TABLES[@]}"; do
    if $PSQL_CMD -c "\dt $table" | grep -q "$table"; then
        echo -e "${GREEN}✓${NC} Table '$table' exists"
    else
        echo -e "${RED}✗${NC} Table '$table' NOT found"
    fi
done

echo ""
echo -e "${BLUE}Migration complete!${NC}"

