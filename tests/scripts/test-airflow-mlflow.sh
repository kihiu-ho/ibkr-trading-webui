#!/bin/bash
# Test script for Airflow and MLflow integration

set -e

echo "🚀 Testing Airflow and MLflow Integration"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if docker-compose is available
print_info "Checking prerequisites..."
command -v docker-compose >/dev/null 2>&1
print_status $? "docker-compose is installed"

# Validate docker-compose.yml syntax
print_info "Validating docker-compose.yml syntax..."
docker-compose config > /dev/null
print_status $? "docker-compose.yml syntax is valid"

# Check if .env file exists
if [ ! -f .env ]; then
    print_info "No .env file found. Creating from env.example..."
    cp env.example .env
    echo "AIRFLOW_UID=$(id -u)" >> .env
    print_status 0 "Created .env file (please configure DATABASE_URL before full startup)"
fi

# Create required directories
print_info "Creating required directories..."
mkdir -p dags logs/airflow plugins
print_status $? "Created directories: dags/, logs/airflow/, plugins/"

# Test building individual images
print_info "Testing MLflow image build..."
docker-compose build mlflow-server > /dev/null 2>&1
print_status $? "MLflow image built successfully"

print_info "Testing Airflow image build..."
docker-compose build airflow-webserver > /dev/null 2>&1
print_status $? "Airflow image built successfully"

# Start core services for testing (Redis, PostgreSQL, MinIO)
print_info "Starting core services (Redis, PostgreSQL, MinIO)..."
docker-compose up -d redis postgres minio
sleep 10

# Check if services are running
print_info "Checking service health..."

docker-compose ps redis | grep "Up" > /dev/null
print_status $? "Redis is running"

docker-compose ps postgres | grep "Up" > /dev/null
print_status $? "PostgreSQL is running"

docker-compose ps minio | grep "Up" > /dev/null
print_status $? "MinIO is running"

# Start MinIO client to create buckets
print_info "Creating MinIO buckets..."
docker-compose up -d mc
sleep 5
print_status 0 "MinIO client setup complete"

# Start MLflow server
print_info "Starting MLflow server..."
docker-compose up -d mlflow-server
sleep 10

docker-compose ps mlflow-server | grep "Up" > /dev/null
print_status $? "MLflow server is running"

# Test MLflow accessibility
print_info "Testing MLflow server accessibility..."
curl -f http://localhost:5500 > /dev/null 2>&1
print_status $? "MLflow server is accessible at http://localhost:5500"

# Initialize Airflow
print_info "Initializing Airflow database..."
docker-compose up airflow-init
print_status $? "Airflow database initialized"

# Start Airflow services
print_info "Starting Airflow services..."
docker-compose up -d airflow-webserver airflow-scheduler airflow-worker airflow-triggerer
sleep 20

docker-compose ps airflow-webserver | grep "Up" > /dev/null
print_status $? "Airflow webserver is running"

docker-compose ps airflow-scheduler | grep "Up" > /dev/null
print_status $? "Airflow scheduler is running"

docker-compose ps airflow-worker | grep "Up" > /dev/null
print_status $? "Airflow worker is running"

docker-compose ps airflow-triggerer | grep "Up" > /dev/null
print_status $? "Airflow triggerer is running"

# Test Airflow accessibility
print_info "Testing Airflow web UI accessibility..."
sleep 30  # Give Airflow time to fully start
curl -f http://localhost:8080/health > /dev/null 2>&1
print_status $? "Airflow web UI is accessible at http://localhost:8080"

echo ""
echo "=========================================="
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "Services running:"
echo "  - MLflow UI:   http://localhost:5500"
echo "  - Airflow UI:  http://localhost:8080 (user: airflow / pass: airflow)"
echo "  - MinIO API:   http://localhost:9000"
echo "  - MinIO UI:    http://localhost:9001"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs:     docker-compose logs -f [service-name]"
echo ""

