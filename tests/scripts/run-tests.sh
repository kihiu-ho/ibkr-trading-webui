#!/bin/bash

# IBKR Trading Platform E2E Test Runner
# This script provides various test execution options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BROWSER="chromium"
HEADLESS="true"
WORKERS="1"
TEST_PATTERN=""
ENVIRONMENT="local"
UPDATE_SNAPSHOTS="false"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
IBKR Trading Platform E2E Test Runner

Usage: $0 [OPTIONS]

Options:
    -b, --browser BROWSER       Browser to use (chromium, firefox, webkit) [default: chromium]
    -h, --headless             Run in headless mode [default: true]
    -w, --workers NUMBER       Number of parallel workers [default: 1]
    -p, --pattern PATTERN      Test pattern to match (e.g., "@smoke", "@e2e")
    -e, --environment ENV      Environment (local, docker, ci) [default: local]
    -u, --update-snapshots     Update visual regression snapshots
    -d, --debug               Run in debug mode
    -r, --report              Show HTML report after tests
    --help                    Show this help message

Examples:
    $0                                    # Run all tests with default settings
    $0 -b firefox -w 2                   # Run with Firefox using 2 workers
    $0 -p "@smoke"                        # Run only smoke tests
    $0 -e docker                          # Run tests in Docker environment
    $0 -u                                 # Update visual regression snapshots
    $0 -d                                 # Run in debug mode
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -h|--headless)
            HEADLESS="true"
            shift
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -p|--pattern)
            TEST_PATTERN="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -u|--update-snapshots)
            UPDATE_SNAPSHOTS="true"
            shift
            ;;
        -d|--debug)
            HEADLESS="false"
            WORKERS="1"
            shift
            ;;
        -r|--report)
            SHOW_REPORT="true"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate browser choice
if [[ ! "$BROWSER" =~ ^(chromium|firefox|webkit)$ ]]; then
    print_error "Invalid browser: $BROWSER. Must be chromium, firefox, or webkit."
    exit 1
fi

# Setup environment variables
export BASE_URL="${BASE_URL:-http://localhost:8000}"
export HEADLESS="$HEADLESS"
export UPDATE_SNAPSHOTS="$UPDATE_SNAPSHOTS"

print_status "Starting IBKR Trading Platform E2E Tests"
print_status "Browser: $BROWSER"
print_status "Headless: $HEADLESS"
print_status "Workers: $WORKERS"
print_status "Environment: $ENVIRONMENT"

# Check if we're in the tests directory
if [[ ! -f "package.json" ]]; then
    print_error "Please run this script from the tests directory"
    exit 1
fi

# Install dependencies if needed
if [[ ! -d "node_modules" ]]; then
    print_status "Installing dependencies..."
    npm install
fi

# Install Playwright browsers if needed
if [[ ! -d "node_modules/@playwright/test" ]]; then
    print_status "Installing Playwright browsers..."
    npx playwright install
fi

# Function to run tests locally
run_local_tests() {
    print_status "Running tests locally..."
    
    # Check if application is running
    if ! curl -f "$BASE_URL/api/health" > /dev/null 2>&1; then
        print_warning "Application not running at $BASE_URL"
        print_status "Please start the application first:"
        print_status "cd .. && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
        exit 1
    fi
    
    # Build test command
    TEST_CMD="npx playwright test"
    
    if [[ -n "$TEST_PATTERN" ]]; then
        TEST_CMD="$TEST_CMD --grep=\"$TEST_PATTERN\""
    fi
    
    TEST_CMD="$TEST_CMD --project=$BROWSER --workers=$WORKERS"
    
    if [[ "$HEADLESS" == "false" ]]; then
        TEST_CMD="$TEST_CMD --headed"
    fi
    
    if [[ "$UPDATE_SNAPSHOTS" == "true" ]]; then
        TEST_CMD="$TEST_CMD --update-snapshots"
    fi
    
    print_status "Executing: $TEST_CMD"
    eval $TEST_CMD
}

# Function to run tests in Docker
run_docker_tests() {
    print_status "Running tests in Docker environment..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    
    # Run tests using docker-compose
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    
    # Cleanup
    docker-compose -f docker-compose.test.yml down
}

# Function to run CI tests
run_ci_tests() {
    print_status "Running tests in CI mode..."
    export CI=true
    
    TEST_CMD="npx playwright test --project=$BROWSER --workers=$WORKERS --reporter=github"
    
    if [[ -n "$TEST_PATTERN" ]]; then
        TEST_CMD="$TEST_CMD --grep=\"$TEST_PATTERN\""
    fi
    
    print_status "Executing: $TEST_CMD"
    eval $TEST_CMD
}

# Main execution
case $ENVIRONMENT in
    local)
        run_local_tests
        ;;
    docker)
        run_docker_tests
        ;;
    ci)
        run_ci_tests
        ;;
    *)
        print_error "Invalid environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Show report if requested
if [[ "$SHOW_REPORT" == "true" ]]; then
    print_status "Opening test report..."
    npx playwright show-report
fi

print_success "Tests completed successfully!"
