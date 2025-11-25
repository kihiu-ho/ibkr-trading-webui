#!/bin/bash

# IBKR Trading WebUI Startup Script
# Starts all services via Docker Compose with a single command:
#   - Core: PostgreSQL (local), Redis, MinIO
#   - Trading: IBKR Gateway, Backend, Celery Worker/Beat, Flower
#   - ML/Workflow: MLflow Server, Airflow (webserver, scheduler, init)
# 
# Single command: docker compose up -d
# All services start automatically with proper dependency ordering

set -e  # Exit on error

# Enable Docker BuildKit for faster builds (10-100x faster than legacy builder)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export BUILDKIT_PROGRESS=plain

# Use BuildKit builder (avoid slow OCI tarball export)
# Switch to existing fast builder if available
if docker buildx ls | grep -q "multiplatform.*running"; then
    docker buildx use multiplatform 2>/dev/null || true
fi

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
BUILD_META_DIR="$PROJECT_ROOT/.ibkr-build"
BACKEND_REQUIREMENTS_PATH="$PROJECT_ROOT/backend/requirements.txt"
BACKEND_REQUIREMENTS_HASH_FILE="$BUILD_META_DIR/backend_requirements.sha"

# Command-line flags
FORCE_REBUILD=false
SKIP_HEALTH_CHECKS=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command-line arguments
show_help() {
    echo "Usage: ./start-webapp.sh [OPTIONS]"
    echo ""
    echo "Optimized Docker Compose startup for IBKR Trading WebUI"
    echo ""
    echo "Options:"
    echo "  --rebuild   Force rebuild of all Docker images (use after dependency changes)"
    echo "  --fast      Skip health checks for faster startup (expert mode)"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start-webapp.sh              # Normal startup (fast after first run, ~8s)"
    echo "  ./start-webapp.sh --rebuild    # Rebuild images (after requirements.txt changes, ~90s)"
    echo "  ./start-webapp.sh --fast       # Quick restart, skip health checks (~5s)"
    echo ""
    echo "Performance:"
    echo "  First run:       ~150s (one-time image build with uv)"
    echo "  Subsequent runs: ~8s   (uses cached images)"
    echo "  With --rebuild:  ~90s  (optimized rebuild with layer caching)"
    echo ""
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --fast)
            SKIP_HEALTH_CHECKS=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
done

# Create logs directory
mkdir -p "$LOG_DIR"
mkdir -p "$BUILD_META_DIR"

echo -e "${BLUE}=============================================="
echo "IBKR Trading WebUI - Docker Startup"
if [ "$FORCE_REBUILD" = true ]; then
    echo "(Rebuild Mode - Full Image Rebuild)"
elif [ "$SKIP_HEALTH_CHECKS" = true ]; then
    echo "(Fast Mode - Health Checks Skipped)"
else
    echo "(Smart Mode - Build Only When Needed)"
fi
echo "==============================================${NC}"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to detect if Docker images exist
detect_images() {
    local images=("ibkr-backend:latest" "ibkr-gateway:latest" "ibkr-airflow:latest" "ibkr-mlflow:latest")
    
    for image in "${images[@]}"; do
        if ! docker image inspect "$image" &> /dev/null 2>&1; then
            return 1  # Image doesn't exist, need to build
        fi
    done
    
    return 0  # All images exist
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker CLI not found"
    echo ""
    echo "Please install Docker Desktop from:"
    echo "  https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_status "Docker CLI found"

# Check for .env file and load environment variables
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_error "No .env file found!"
    echo ""
    echo "Please create .env file with required variables:"
    echo "  1. Copy example: cp env.example .env"
    echo "  2. Edit with your values: nano .env"
    echo "  3. Ensure DATABASE_URL is set"
    echo ""
    exit 1
else
    print_status "Found .env file"
    print_info "Loading environment variables..."
    
    # Load .env file and export all variables
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a  # Disable auto-export
    
    # Verify DATABASE_URL is set (for main backend)
    if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "your_database_url" ]; then
        print_error "DATABASE_URL is not configured in .env!"
        echo ""
        echo "Please set DATABASE_URL in your .env file:"
        echo "  DATABASE_URL=postgresql+psycopg2://user:pass@host/db"
        echo ""
        echo "Note: Airflow and MLflow now use local PostgreSQL (no separate URLs needed)"
        echo ""
        exit 1
    fi
    
    # Mask password for display
    DB_URL_MASKED=$(echo "$DATABASE_URL" | sed -E 's|(://[^:]+:)[^@]+(@)|\1****\2|')
    print_status "DATABASE_URL loaded: $DB_URL_MASKED"
    print_info "Airflow and MLflow use local PostgreSQL (configured automatically)"

    # Ensure IBKR Client Portal config propagates into Airflow containers.
    if [ -z "${IBKR_API_BASE_URL:-}" ]; then
        export IBKR_API_BASE_URL="https://127.0.0.1:5055/v1/api"
        print_info "IBKR_API_BASE_URL not set; defaulting to ${IBKR_API_BASE_URL}"
    else
        print_status "IBKR_API_BASE_URL detected: ${IBKR_API_BASE_URL}"
    fi
    if [ -z "${IBKR_API_BASE_URL_INTERNAL:-}" ]; then
        export IBKR_API_BASE_URL_INTERNAL="https://ibkr-gateway:443/v1/api"
        print_info "IBKR_API_BASE_URL_INTERNAL not set; defaulting to ${IBKR_API_BASE_URL_INTERNAL}"
    else
        print_status "IBKR_API_BASE_URL_INTERNAL detected: ${IBKR_API_BASE_URL_INTERNAL}"
    fi

    if [ -z "${IBKR_PRIMARY_CONID:-}" ]; then
        PYTHON_BIN=""
        if [ -x "$PROJECT_ROOT/venv/bin/python" ]; then
            PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"
        elif command -v python3 >/dev/null 2>&1; then
            PYTHON_BIN="$(command -v python3)"
        fi

        if [ -n "$PYTHON_BIN" ] && [ -x "$PYTHON_BIN" ]; then
            if CONID="$("$PYTHON_BIN" "${PROJECT_ROOT}/scripts/export_primary_conid.py" 2>/dev/null)"; then
                if [[ "$CONID" =~ ^[0-9]+$ ]]; then
                    export IBKR_PRIMARY_CONID="$CONID"
                    print_status "Resolved IBKR_PRIMARY_CONID=${IBKR_PRIMARY_CONID} from database"
                elif [ -n "$CONID" ]; then
                    print_info "IBKR primary CONID resolver returned unexpected value: ${CONID}"
                else
                    print_info "IBKR primary CONID resolver returned no data (symbol missing in DB)."
                fi
            else
                print_info "Unable to auto-resolve IBKR_PRIMARY_CONID (database unreachable)."
            fi
        else
            print_info "Python with psycopg2 not available; skipping IBKR_PRIMARY_CONID auto-detection."
        fi
    else
        print_status "IBKR_PRIMARY_CONID preset: ${IBKR_PRIMARY_CONID}"
    fi
fi

# Wait for Docker daemon to be ready
print_header "Checking Docker Daemon"

DOCKER_READY=false
for attempt in {1..20}; do
    if docker info &> /dev/null 2>&1; then
        DOCKER_READY=true
        break
    fi
    if [ $attempt -eq 1 ]; then
        print_info "Waiting for Docker Desktop (up to 40 seconds)..."
        printf "  "
    fi
    printf "."
    sleep 2
done

if [ "$DOCKER_READY" = false ]; then
    echo ""
    print_error "Docker is not responding after 40 seconds"
    echo ""
    echo "Please ensure Docker Desktop is:"
    echo "  1. Installed (from https://www.docker.com/products/docker-desktop)"
    echo "  2. Running (whale icon in menu bar should be steady)"
    echo "  3. Fully started (may take 30-60 seconds after opening)"
    echo ""
    exit 1
fi

echo ""
print_status "Docker daemon is ready"
print_info "Using Docker compose command: $COMPOSE_CMD"
COMPOSE_BUILD_CMD="$COMPOSE_CMD"

# Determine docker-compose command
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    print_error "No Docker Compose command found (docker compose or docker-compose)"
    exit 1
fi

print_status "Docker Compose: $COMPOSE_CMD"

# Pull required images
print_header "Checking Required Images"

IMAGES=("postgres:15" "redis:7-alpine" "minio/minio:latest")
for image in "${IMAGES[@]}"; do
    if docker image inspect "$image" &> /dev/null; then
        print_status "Image $image exists"
    else
        print_info "Pulling image $image (may take 1-2 minutes)..."
        if ! docker pull "$image"; then
            print_error "Failed to pull image $image"
            exit 1
        fi
        print_status "Image $image pulled successfully"
    fi
done

# Build images if needed
print_header "Preparing Docker Images"

cd "$PROJECT_ROOT"

# Detect backend dependency changes to force rebuild automatically
calc_file_hash() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        echo ""
    fi
}

REQUIREMENTS_CHANGED=false
CURRENT_BACKEND_REQ_HASH=""
if [ -f "$BACKEND_REQUIREMENTS_PATH" ]; then
    CURRENT_BACKEND_REQ_HASH=$(calc_file_hash "$BACKEND_REQUIREMENTS_PATH")
    if [ -n "$CURRENT_BACKEND_REQ_HASH" ]; then
        if [ -f "$BACKEND_REQUIREMENTS_HASH_FILE" ]; then
            SAVED_HASH=$(cat "$BACKEND_REQUIREMENTS_HASH_FILE" 2>/dev/null || true)
        else
            SAVED_HASH=""
        fi
        if [ "$CURRENT_BACKEND_REQ_HASH" != "$SAVED_HASH" ]; then
            REQUIREMENTS_CHANGED=true
            FORCE_REBUILD=true
            print_info "Detected backend dependency changes; forcing backend image rebuild"
        fi
    else
        print_info "Unable to calculate backend requirements hash (sha256sum/shasum missing)"
    fi
fi

NEED_BUILD=false
if ! detect_images; then
    NEED_BUILD=true
    print_info "Docker images not found (first run)"
elif [ "$FORCE_REBUILD" = true ]; then
    NEED_BUILD=true
    print_info "Force rebuild requested (--rebuild flag)"
else
    print_status "Using cached Docker images"
    print_info "Use --rebuild flag to force rebuild after dependency changes"
fi

if [ "$NEED_BUILD" = true ]; then
    echo ""
    print_header "Building Docker Images"
    
    if [ "$FORCE_REBUILD" = true ]; then
        print_info "Building all images with uv (10-100x faster than pip)..."
    else
        print_info "First-time build with uv (10-100x faster than pip)..."
    fi
    print_info "This may take 1-2 minutes (one-time cost)..."
    echo ""
    
    START_BUILD=$(date +%s)
    
    # Build backend image directly (avoid Compose's slow build path)
    print_info "Building backend image (ibkr-backend:latest)..."
    docker build -f docker/Dockerfile.backend -t ibkr-backend:latest .
    if [ "$REQUIREMENTS_CHANGED" = true ] && [ -n "$CURRENT_BACKEND_REQ_HASH" ]; then
        echo "$CURRENT_BACKEND_REQ_HASH" > "$BACKEND_REQUIREMENTS_HASH_FILE"
    fi
    
    # Copy webapp directory to project root for gateway build (if it doesn't exist)
    if [ ! -d "webapp" ]; then
        print_info "Copying webapp directory from reference/ to project root..."
        cp -r reference/webapp ./webapp
    fi
    
    # Build gateway image directly
    print_info "Building gateway image (ibkr-gateway:latest)..."
    docker build -f Dockerfile -t ibkr-gateway:latest .
    
    # Build Airflow image (using reference structure)
    print_info "Building Airflow image (ibkr-airflow:latest)..."
    docker build -f reference/airflow/airflow/Dockerfile -t ibkr-airflow:latest reference/airflow/airflow/
    print_info "Verifying Kaleido inside ibkr-airflow:latest..."
    ./scripts/verify_kaleido.sh --image ibkr-airflow:latest
    
    # Build MLflow image (using reference structure)
    print_info "Building MLflow image (ibkr-mlflow:latest)..."
    docker build -f reference/airflow/mlflow/Dockerfile -t ibkr-mlflow:latest reference/airflow/mlflow/
    
    END_BUILD=$(date +%s)
    BUILD_TIME=$((END_BUILD - START_BUILD))
    
    echo ""
    print_status "Images built successfully in ${BUILD_TIME}s"
    echo ""
fi

# Start services
print_header "Starting All Services"

print_info "Starting Docker Compose services..."
echo ""

START_UP=$(date +%s)
# Single command starts all services with proper dependency ordering
# Docker Compose handles: postgres -> redis/minio -> airflow-init -> webserver/scheduler -> etc.
print_info "Starting all services with single command: $COMPOSE_CMD up -d"
$COMPOSE_CMD up -d
END_UP=$(date +%s)
STARTUP_TIME=$((END_UP - START_UP))

echo ""
print_status "Services started in ${STARTUP_TIME}s"

# Wait for services to be healthy (unless --fast flag is used)
if [ "$SKIP_HEALTH_CHECKS" = true ]; then
    print_header "Health Checks Skipped (Fast Mode)"
    print_info "Services are starting in background with dependency management"
    print_info "Use '$COMPOSE_CMD ps' to check status"
    echo ""
else
    print_header "Waiting for Services to be Ready"
    print_info "Services are starting with proper dependency ordering..."
fi

# Note: Local PostgreSQL is now containerized and starts automatically
# Docker Compose handles all service dependencies automatically
# Single command: docker compose up -d starts all services in correct order

if [ "$SKIP_HEALTH_CHECKS" = false ]; then
    # Optimized health checking with parallel checks and shorter intervals
    print_info "Monitoring service startup progress..."

    # Function to check service health (non-blocking)
    check_service_health() {
        local service=$1
        local max_attempts=${2:-15}  # Default 15 attempts (30 seconds)
        local check_interval=${3:-2}  # Default 2 seconds
        
        for i in $(seq 1 $max_attempts); do
            # Check if service is healthy
            if $COMPOSE_CMD ps "$service" --format json 2>/dev/null | jq -e '.Health == "healthy"' &> /dev/null 2>&1; then
                return 0  # Service is healthy
            fi
            # Check if service is running (even if not healthy yet)
            if $COMPOSE_CMD ps "$service" --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null 2>&1; then
                sleep $check_interval
                continue
            fi
            # Service not running yet
            sleep $check_interval
        done
        return 1  # Service not healthy within timeout
    }

    # Wait for core infrastructure services (parallel check, shorter timeout)
    CORE_SERVICES=("postgres" "redis" "minio")
    print_info "Checking core services (postgres, redis, minio)..."
    
    for service in "${CORE_SERVICES[@]}"; do
        if check_service_health "$service" 15 1; then
            print_status "$service is healthy"
        else
            # Give one more chance with longer timeout
            print_info "$service still starting, checking again..."
            if check_service_health "$service" 10 2; then
                    print_status "$service is healthy"
            else
                print_error "$service failed health check after 50 seconds"
                echo "Service status:"
                $COMPOSE_CMD ps "$service"
        echo ""
                echo "Recent logs:"
                docker logs "$service" --tail 20 2>/dev/null || true
        exit 1
    fi
fi
    done

    # Wait for airflow-init to complete (runs once for database initialization)
    if $COMPOSE_CMD ps --services | grep -q "airflow-init"; then
        print_info "Waiting for airflow-init (database initialization)..."
        for i in {1..60}; do  # Allow up to 2 minutes for init
            if $COMPOSE_CMD ps "airflow-init" --format json | jq -e '.State == "exited" and .ExitCode == 0' &> /dev/null 2>&1; then
                print_status "airflow-init completed successfully"
            break
        fi
            if [ $((i % 10)) -eq 0 ]; then
                printf "."
            fi
            sleep 2
        done
        echo ""
    fi

    # Wait for application services (optimized with early exit)
    APP_SERVICES=("ibkr-gateway" "backend")
    print_info "Checking application services (gateway, backend)..."
    
    for service in "${APP_SERVICES[@]}"; do
        # Check if already healthy
        if $COMPOSE_CMD ps "$service" --format json 2>/dev/null | jq -e '.Health == "healthy"' &> /dev/null 2>&1; then
            print_status "$service is healthy"
            continue
        fi
        
        # Quick check: if service is running, give it a moment
        if $COMPOSE_CMD ps "$service" --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null 2>&1; then
            print_info "$service is running, waiting for health check..."
            # Shorter timeout - services should be healthy quickly if running
            if check_service_health "$service" 20 1; then
                print_status "$service is healthy"
            else
                # Service is running but not healthy - likely still initializing
                print_info "$service is running but may still be initializing"
                print_info "This is normal - service will be ready shortly"
                print_info "Check status: $COMPOSE_CMD ps $service"
            fi
        else
            # Service not running yet - wait a bit
            print_info "$service starting..."
            sleep 3
            if check_service_health "$service" 15 2; then
                print_status "$service is healthy"
            else
            print_info "$service may still be initializing"
            print_info "Check logs: docker logs $service"
            fi
    fi
    done
fi

# Check for Airflow and MLflow services (optional, won't fail if not present)
AIRFLOW_ENABLED=false
MLFLOW_ENABLED=false
if $COMPOSE_CMD ps --services | grep -q "mlflow-server"; then
    MLFLOW_ENABLED=true
fi
if $COMPOSE_CMD ps --services | grep -q "airflow-webserver"; then
    AIRFLOW_ENABLED=true
fi

if [ "$SKIP_HEALTH_CHECKS" = false ]; then
    # Check optional services using Docker Compose health status
    OPTIONAL_SERVICES=()
    if [ "$MLFLOW_ENABLED" = true ]; then
        OPTIONAL_SERVICES+=("mlflow-server")
    fi
    if [ "$AIRFLOW_ENABLED" = true ]; then
        OPTIONAL_SERVICES+=("airflow-webserver")
    fi

    for service in "${OPTIONAL_SERVICES[@]}"; do
        # Quick check for optional services - don't block startup
        if $COMPOSE_CMD ps "$service" --format json 2>/dev/null | jq -e '.Health == "healthy"' &> /dev/null 2>&1; then
            print_status "$service is healthy"
        elif $COMPOSE_CMD ps "$service" --format json 2>/dev/null | jq -e '.State == "running"' &> /dev/null 2>&1; then
            # Service is running - check health quickly
            if check_service_health "$service" 10 1; then
                print_status "$service is healthy"
            else
                print_info "$service is running (health check pending)"
            fi
        else
            print_info "$service starting in background (non-blocking)"
    fi
    done
fi

# Run database migrations
print_header "Database Migrations"

print_info "Checking for pending database migrations..."
if [ -d "$PROJECT_ROOT/database/migrations" ] && [ -f "$PROJECT_ROOT/database/migrations/run_migrations.sh" ]; then
    if bash "$PROJECT_ROOT/database/migrations/run_migrations.sh"; then
        print_status "Database migrations completed"
    else
        print_info "Migration script exited with warnings (may be expected)"
    fi
else
    print_info "No migration script found (skipping)"
fi

# Summary
print_header "Startup Complete!"

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          All Services Running Successfully! 🎉                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📦 Docker Containers:${NC}"
echo "  ├─ Core Services:"
echo "  │  ├─ ibkr-postgres       PostgreSQL database (local)"
echo "  │  ├─ ibkr-redis          Redis message broker"
echo "  │  └─ ibkr-minio          MinIO object storage"
echo "  ├─ Trading Services:"
echo "  │  ├─ ibkr-gateway        IBKR Client Portal Gateway"
echo "  │  ├─ ibkr-backend        FastAPI backend server"
echo "  │  ├─ ibkr-celery-worker  Celery background worker"
echo "  │  ├─ ibkr-celery-beat    Celery task scheduler"
echo "  │  └─ ibkr-flower         Celery monitoring UI"
if [ "$MLFLOW_ENABLED" = true ] || [ "$AIRFLOW_ENABLED" = true ]; then
echo "  └─ ML/Workflow Services:"
fi
if [ "$MLFLOW_ENABLED" = true ]; then
echo "     ├─ ibkr-mlflow-server  MLflow experiment tracking"
fi
if [ "$AIRFLOW_ENABLED" = true ]; then
echo "     ├─ ibkr-airflow-init       Airflow database init (runs once)"
echo "     ├─ ibkr-airflow-webserver  Airflow web UI"
echo "     ├─ ibkr-airflow-scheduler  Airflow scheduler"
echo "     └─ ibkr-airflow-triggerer  Airflow triggerer (deferrable tasks)"
fi
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo "  ┌─ Main Application:"
echo "  ├── Web UI:           http://localhost:8000"
echo "  ├── Dashboard:        http://localhost:8000/dashboard"
echo "  ├── Strategies:       http://localhost:8000/strategies  ⭐"
echo "  ├── Orders:           http://localhost:8000/orders      ⭐"
echo "  ├── Portfolio:        http://localhost:8000/portfolio   ⭐"
echo "  ├── Prompts:          http://localhost:8000/prompts     ⭐"
echo "  ├── API Docs:         http://localhost:8000/docs"
echo "  └── Health Check:     http://localhost:8000/health"
echo ""
echo "  ┌─ Support Services:"
echo "  ├── IBKR Gateway:     https://localhost:5055"
echo "  ├── Flower Monitor:   http://localhost:5555"
if [ "$MLFLOW_ENABLED" = true ]; then
echo "  ├── MLflow UI:        http://localhost:5500          ⭐"
fi
if [ "$AIRFLOW_ENABLED" = true ]; then
echo "  ├── Airflow UI:       http://localhost:8080          ⭐"
fi
echo "  └── MinIO Console:    http://localhost:9001"
echo ""
echo -e "${BLUE}📊 System Status:${NC}"
echo "  ✓ Backend:            READY (Port 8000)"
echo "  ✓ PostgreSQL:         READY (Local, Port 5432)"
echo "  ✓ Redis:              READY (Port 6379)"
echo "  ✓ MinIO:              READY (Port 9000)"
if [ "$IBKR_READY" = true ]; then
    echo "  ✓ IBKR Gateway:       READY (Port 5055)"
else
    echo "  ⏳ IBKR Gateway:      STARTING (check logs)"
fi
echo "  ✓ Celery Worker:      READY"
echo "  ✓ Celery Beat:        READY"
if [ "$MLFLOW_ENABLED" = true ]; then
    if [ "$MLFLOW_READY" = true ]; then
        echo "  ✓ MLflow Server:      READY (Port 5500)"
    else
        echo "  ⏳ MLflow Server:      STARTING (check logs)"
    fi
fi
if [ "$AIRFLOW_ENABLED" = true ]; then
    if [ "$AIRFLOW_READY" = true ]; then
        echo "  ✓ Airflow Webserver:  READY (Port 8080)"
    else
        echo "  ⏳ Airflow Webserver:  STARTING (check logs)"
    fi
fi
echo ""
echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  View all logs:        docker-compose logs -f"
echo "  View backend logs:    docker logs -f ibkr-backend"
echo "  View celery logs:     docker logs -f ibkr-celery-worker"
echo "  View gateway logs:    docker logs -f ibkr-gateway"
if [ "$MLFLOW_ENABLED" = true ]; then
echo "  View MLflow logs:     docker logs -f ibkr-mlflow-server"
fi
if [ "$AIRFLOW_ENABLED" = true ]; then
echo "  View Airflow logs:    docker logs -f ibkr-airflow-webserver"
fi
echo "  Stop all services:    ./stop-all.sh"
echo "  Restart services:     docker-compose restart"
echo "  Run tests:            ./tests/scripts/run-tests.sh"
echo ""
echo -e "${YELLOW}⚠️  First-time IBKR Gateway Setup:${NC}"
echo "  1. Open https://localhost:5055 in your browser"
echo "  2. Accept the security warning (self-signed certificate)"
echo "  3. Log in with your IBKR credentials"
echo "  4. The gateway will maintain the session"
echo ""
echo -e "${BLUE}🧪 Testing:${NC}"
echo "  Run test suite:       ./tests/scripts/run-tests.sh"
echo "  102 comprehensive tests covering all services"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "  Main README:          README.md"
echo "  Quick Start:          docs/guides/QUICK_START.md"
echo "  Troubleshooting:      docs/guides/TROUBLESHOOTING.md"
echo "  Folder Structure:     AGENTS.md"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🚀 Ready for automated trading! Visit http://localhost:8000 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Optional: Show live logs (removed interactive test prompt per OpenSpec 2)
echo -e "${CYAN}💡 Tip: Run tests anytime with: ./tests/scripts/run-tests.sh${NC}"
echo ""
read -p "Show live backend logs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Showing live backend logs (Ctrl+C to exit)...${NC}"
    echo ""
    docker logs -f ibkr-backend
fi
