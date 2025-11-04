#!/bin/bash

# Quick setup helper for Airflow & MLflow
# All services now use the same DATABASE_URL (no separate databases needed!)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Airflow & MLflow Configuration Check                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo ""
    echo "Please create a .env file with DATABASE_URL configured."
    echo "See env.example for a template."
    exit 1
fi

# Load .env file
source .env 2>/dev/null || true

echo "Checking configuration..."
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "postgresql+psycopg2://user:password@host:port/dbname?sslmode=require" ]; then
    echo -e "${RED}✗ DATABASE_URL is not configured${NC}"
    echo ""
    echo "Please configure DATABASE_URL in your .env file:"
    echo ""
    echo "  DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname?sslmode=require"
    echo ""
    echo "See DATABASE_SETUP.md for detailed instructions."
    exit 1
fi

# Mask password in URL for display
MASKED_URL=$(echo "$DATABASE_URL" | sed -E 's|(://[^:]+:)[^@]+(@)|\1****\2|')

echo -e "${GREEN}✓ DATABASE_URL is configured${NC}"
echo "  ${MASKED_URL}"
echo ""

# Extract connection details for display
if [[ $DATABASE_URL =~ postgresql\+psycopg2://([^:]+):([^@]+)@([^/]+)/([^?]+) ]]; then
    USER="${BASH_REMATCH[1]}"
    HOST="${BASH_REMATCH[3]}"
    DB="${BASH_REMATCH[4]}"
    
    echo "  Database: $DB"
    echo "  Host: $HOST"
    echo "  User: $USER"
fi

echo ""
echo "────────────────────────────────────────────────────────"
echo ""
echo -e "${GREEN}✓ Configuration Complete!${NC}"
echo ""
echo "All services (Backend, Airflow, MLflow) will use the same database."
echo ""
echo "The services will create their own tables:"
echo "  • Backend: Uses existing tables"
echo "  • Airflow: Creates tables with 'alembic_version', 'dag_', 'task_', etc."
echo "  • MLflow: Creates tables with 'mlflow_' prefix"
echo ""
echo "No separate database creation needed!"
echo ""
echo "────────────────────────────────────────────────────────"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Verify configuration:"
echo "   ${GREEN}./scripts/check-env-airflow-mlflow.sh${NC}"
echo ""
echo "2. Start all services:"
echo "   ${GREEN}./start-webapp.sh${NC}"
echo ""
echo "3. Access services:"
echo "   • Backend API:  http://localhost:8000"
echo "   • Airflow UI:   http://localhost:8080 (username: airflow, password: airflow)"
echo "   • MLflow UI:    http://localhost:5500"
echo ""
echo "────────────────────────────────────────────────────────"
echo ""
echo -e "${GREEN}Ready to start!${NC}"
echo ""
