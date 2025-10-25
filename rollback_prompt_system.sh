#!/bin/bash
# Rollback Script for Configurable Prompt System

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${RED}"
echo "========================================"
echo " Rollback Configurable Prompt System"
echo "========================================"
echo -e "${NC}"

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
    echo ""
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo ""
fi

# Check for backup file
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <backup_file>${NC}"
    echo ""
    echo "Available backups:"
    ls -1 backup_*.sql 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}ERROR: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}WARNING: This will restore database from backup${NC}"
echo -e "${YELLOW}All changes since the backup will be LOST!${NC}"
echo ""
read -p "Are you sure you want to rollback? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

echo ""
echo "Starting rollback..."
echo ""

# Step 1: Create a backup before rollback (just in case)
echo "[1/4] Creating pre-rollback backup..."
PRE_ROLLBACK_BACKUP="pre_rollback_$(date +%Y%m%d_%H%M%S).sql"
pg_dump "$DATABASE_URL" > "$PRE_ROLLBACK_BACKUP" 2>/dev/null || {
    echo -e "${YELLOW}Warning: Could not create pre-rollback backup${NC}"
}
echo -e "${GREEN}✓ Pre-rollback backup: $PRE_ROLLBACK_BACKUP${NC}"

# Step 2: Drop new tables
echo ""
echo "[2/4] Dropping new tables..."
psql "$DATABASE_URL" << EOF
DROP TABLE IF EXISTS prompt_performance CASCADE;
DROP TABLE IF EXISTS prompt_templates CASCADE;

-- Remove columns from trading_signals if they exist
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS prompt_template_id;
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS prompt_version;
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS prompt_type;
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS outcome;
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS actual_r_multiple;
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS profit_loss;
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS exit_price;
ALTER TABLE IF EXISTS trading_signals DROP COLUMN IF EXISTS exit_time;
EOF
echo -e "${GREEN}✓ Tables dropped${NC}"

# Step 3: Restore from backup
echo ""
echo "[3/4] Restoring from backup..."
psql "$DATABASE_URL" < "$BACKUP_FILE"
echo -e "${GREEN}✓ Database restored${NC}"

# Step 4: Restart services
echo ""
echo "[4/4] Restarting services..."
if command -v docker-compose &> /dev/null; then
    docker-compose restart backend celery-worker celery-beat
    echo -e "${GREEN}✓ Services restarted${NC}"
else
    echo -e "${YELLOW}Warning: docker-compose not found${NC}"
fi

echo ""
echo -e "${GREEN}"
echo "========================================"
echo " Rollback Completed"
echo "========================================"
echo -e "${NC}"
echo ""
echo "Database has been restored to: $BACKUP_FILE"
echo "Pre-rollback backup saved as: $PRE_ROLLBACK_BACKUP"
echo ""

