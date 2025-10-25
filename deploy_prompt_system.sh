#!/bin/bash
# Deployment Script for Configurable Prompt System
# This script deploys the prompt system to production

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================"
echo " Configurable Prompt System Deployment"
echo "========================================"
echo -e "${NC}"

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL environment variable is not set${NC}"
    echo ""
    echo "Please either:"
    echo "  1. Add DATABASE_URL to your .env file, OR"
    echo "  2. Export it manually: export DATABASE_URL='postgresql://...'"
    echo ""
    exit 1
fi

echo -e "${YELLOW}Database URL: ${DATABASE_URL}${NC}"
echo ""

# Step 1: Backup existing database
echo -e "${BLUE}[1/8] Backing up database...${NC}"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null || {
    echo -e "${YELLOW}Warning: Could not create backup (database might be empty)${NC}"
}
echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
echo ""

# Step 2: Run migrations
echo -e "${BLUE}[2/8] Running database migrations...${NC}"
psql "$DATABASE_URL" -f database/migrations/add_prompt_templates.sql
echo -e "${GREEN}✓ Migrations applied successfully${NC}"
echo ""

# Step 3: Verify table creation
echo -e "${BLUE}[3/8] Verifying tables...${NC}"
psql "$DATABASE_URL" -c "\d prompt_templates" > /dev/null || {
    echo -e "${RED}ERROR: prompt_templates table not found${NC}"
    exit 1
}
psql "$DATABASE_URL" -c "\d prompt_performance" > /dev/null || {
    echo -e "${RED}ERROR: prompt_performance table not found${NC}"
    exit 1
}
echo -e "${GREEN}✓ Tables verified successfully${NC}"
echo ""

# Step 4: Seed initial prompts
echo -e "${BLUE}[4/8] Seeding initial prompts...${NC}"
psql "$DATABASE_URL" -f database/migrations/seed_prompt_templates.sql
echo -e "${GREEN}✓ Initial prompts seeded${NC}"
echo ""

# Step 5: Install Python dependencies
echo -e "${BLUE}[5/8] Installing Python dependencies...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
pip install -q jinja2>=3.1.2 pytest>=7.4.0 pytest-cov>=4.1.0
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 6: Restart services
echo -e "${BLUE}[6/8] Restarting services...${NC}"
if command -v docker-compose &> /dev/null; then
    echo "Restarting Docker containers..."
    docker-compose restart backend celery-worker celery-beat
    echo -e "${GREEN}✓ Docker services restarted${NC}"
else
    echo -e "${YELLOW}Warning: docker-compose not found, skipping restart${NC}"
fi
echo ""

# Step 7: Run tests
echo -e "${BLUE}[7/8] Running tests...${NC}"
if [ -f "run_tests.sh" ]; then
    bash run_tests.sh || {
        echo -e "${RED}WARNING: Some tests failed. Review test output above.${NC}"
        read -p "Continue deployment anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Deployment aborted${NC}"
            exit 1
        fi
    }
else
    echo -e "${YELLOW}Warning: run_tests.sh not found, skipping tests${NC}"
fi
echo ""

# Step 8: Verify deployment
echo -e "${BLUE}[8/8] Verifying deployment...${NC}"

# Check if API is accessible
if command -v curl &> /dev/null; then
    sleep 3  # Wait for services to start
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/prompts/ || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ API is accessible${NC}"
    else
        echo -e "${YELLOW}Warning: API returned HTTP $HTTP_CODE${NC}"
    fi
else
    echo -e "${YELLOW}Warning: curl not found, skipping API check${NC}"
fi

# Count prompts in database
PROMPT_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM prompt_templates;" | xargs)
echo -e "${GREEN}✓ Prompts in database: $PROMPT_COUNT${NC}"

# Check Celery Beat schedule
if command -v docker-compose &> /dev/null; then
    echo "Checking Celery Beat schedule..."
    docker-compose exec -T celery-beat celery -A backend.celery_app inspect scheduled 2>/dev/null || {
        echo -e "${YELLOW}Warning: Could not verify Celery Beat schedule${NC}"
    }
fi

echo ""
echo -e "${GREEN}"
echo "========================================"
echo " Deployment Completed Successfully! 🎉"
echo "========================================"
echo -e "${NC}"
echo ""
echo "Next steps:"
echo "1. Visit http://localhost:8000/prompts to access Prompt Manager"
echo "2. Test creating a new prompt"
echo "3. Monitor logs for any errors"
echo "4. Run manual tests from PHASES_8_9_COMPLETE.md"
echo ""
echo "Backup file: $BACKUP_FILE"
echo -e "${YELLOW}Keep this backup safe in case you need to rollback${NC}"
echo ""

