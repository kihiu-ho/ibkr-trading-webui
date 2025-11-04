#!/bin/bash

# Quick check for Airflow & MLflow environment configuration

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

# Load .env file
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi

source .env

# Function to check a variable
check_var() {
    local var_name=$1
    local var_value=$2
    local is_url=$3
    
    if [ -z "$var_value" ] || [ "$var_value" = "postgresql+psycopg2://user:password@host:port/dbname?sslmode=require" ]; then
        echo -e "${YELLOW}⚠ $var_name is not set or using placeholder${NC}"
        return 1
    else
        if [ "$is_url" = "true" ]; then
            # Mask password in URL
            local masked_value=$(echo "$var_value" | sed -E 's|(://[^:]+:)[^@]+(@)|\1****\2|')
            echo -e "${GREEN}✓ $var_name is set${NC}"
            echo "  ${masked_value}"
        else
            echo -e "${GREEN}✓ $var_name is set${NC}"
        fi
        return 0
    fi
}

# Check DATABASE_URL (shared by all services)
echo "Checking shared database configuration..."
echo ""
check_var "DATABASE_URL" "$DATABASE_URL" true
DB_OK=$?

echo ""
echo "All services (Backend, Airflow, MLflow) use the same DATABASE_URL."
echo "Each service creates its own tables in the shared database."

echo ""
echo "──────────────────────────────────────────────────────────"
echo ""

# Check Airflow specific config
echo "Checking Airflow configuration..."
echo ""
check_var "_AIRFLOW_WWW_USER_USERNAME" "$_AIRFLOW_WWW_USER_USERNAME" false
check_var "_AIRFLOW_WWW_USER_PASSWORD" "$_AIRFLOW_WWW_USER_PASSWORD" false

echo ""
echo "──────────────────────────────────────────────────────────"
echo ""

# Check MLflow specific config
echo "Checking MLflow configuration..."
echo ""
check_var "MLFLOW_TRACKING_URI" "$MLFLOW_TRACKING_URI" false
check_var "MLFLOW_S3_ENDPOINT_URL" "$MLFLOW_S3_ENDPOINT_URL" false

echo ""
echo "──────────────────────────────────────────────────────────"
echo ""

# Check MinIO (required for MLflow artifacts)
echo "Checking MinIO configuration (for MLflow artifacts)..."
echo ""
check_var "AWS_ACCESS_KEY_ID" "$AWS_ACCESS_KEY_ID" false
check_var "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET_ACCESS_KEY" false

echo ""
echo "══════════════════════════════════════════════════════════"
echo ""

# Final verdict
if [ $DB_OK -eq 0 ]; then
    echo -e "${GREEN}✓ All required environment variables are configured!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ${GREEN}./start-webapp.sh${NC}"
    echo "  2. Services will auto-create their tables on first run"
    echo ""
else
    echo -e "${YELLOW}⚠ DATABASE_URL needs configuration${NC}"
    echo ""
    echo "Configure DATABASE_URL in .env file, then run:"
    echo "  ${GREEN}./setup-databases-quick.sh${NC}"
    echo ""
fi

echo ""
