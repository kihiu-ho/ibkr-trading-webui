#!/bin/bash

# Test Report Generator for IBKR Trading Platform
# Generates comprehensive test reports with coverage analysis

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the tests directory
if [[ ! -f "package.json" ]]; then
    print_error "Please run this script from the tests directory"
    exit 1
fi

print_status "Generating comprehensive test report..."

# Create reports directory
mkdir -p test-results/reports

# Generate HTML report
print_status "Generating HTML test report..."
npx playwright show-report --host 0.0.0.0 --port 9323 &
REPORT_PID=$!

# Wait a moment for the server to start
sleep 2

# Generate static HTML report
print_status "Creating static HTML report..."
curl -s "http://localhost:9323" > test-results/reports/test-report.html

# Kill the report server
kill $REPORT_PID 2>/dev/null || true

# Generate test summary
print_status "Generating test summary..."
cat > test-results/reports/test-summary.md << EOF
# IBKR Trading Platform E2E Test Report

## Test Execution Summary

**Generated:** $(date)
**Environment:** ${BASE_URL:-http://localhost:8000}

## Test Categories

### 🔐 Authentication Tests
- IBKR paper trading login flow
- Session management
- Connection stability

### 📊 Dashboard Tests
- Workflow statistics display
- Active executions monitoring
- Recent results visualization
- Real-time updates

### 🎯 Strategy Management Tests
- Strategy creation and editing
- Parameter validation
- Execution triggering
- Status management

### 🔄 Workflow Execution Tests
- Real-time monitoring
- Step-by-step tracking
- Control operations (pause/resume/stop)
- Error handling

### 🔍 Lineage Tracking Tests
- Rich step visualizations
- Input/output data display
- Execution history
- Interactive details

### 🎨 Visual Regression Tests
- UI component consistency
- Chart visualizations
- Responsive design
- Dark mode compatibility

### [object Object]ntegration Tests
- Request/response validation
- Error handling
- Performance benchmarks
- WebSocket functionality

## Test Results

EOF

# Add test results if available
if [[ -f "test-results/results.json" ]]; then
    print_status "Processing test results..."
    node -e "
    const fs = require('fs');
    const results = JSON.parse(fs.readFileSync('test-results/results.json', 'utf8'));
    
    console.log('**Total Tests:** ' + results.stats.total);
    console.log('**Passed:** ' + results.stats.passed);
    console.log('**Failed:** ' + results.stats.failed);
    console.log('**Skipped:** ' + results.stats.skipped);
    console.log('**Success Rate:** ' + ((results.stats.passed / results.stats.total) * 100).toFixed(1) + '%');
    console.log('**Duration:** ' + (results.stats.duration / 1000).toFixed(1) + 's');
    " >> test-results/reports/test-summary.md
fi

# Generate coverage report if available
if [[ -f "coverage/lcov.info" ]]; then
    print_status "Generating coverage report..."
    npx nyc report --reporter=html --report-dir=test-results/reports/coverage
fi

# Create test artifacts index
print_status "Creating artifacts index..."
cat > test-results/reports/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>IBKR Trading Platform Test Reports</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        .link { display: inline-block; margin: 10px; padding: 10px 20px; background: #007cba; color: white; text-decoration: none; border-radius: 4px; }
        .link:hover { background: #005a87; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 IBKR Trading Platform Test Reports</h1>
        <p>Generated on $(date)</p>
    </div>
    
    <div class="section">
        <h2>📊 Test Reports</h2>
        <a href="test-report.html" class="link">HTML Test Report</a>
        <a href="../html-report/index.html" class="link">Playwright Report</a>
        <a href="test-summary.md" class="link">Test Summary</a>
    </div>
    
    <div class="section">
        <h2>📈 Coverage Reports</h2>
        <a href="coverage/index.html" class="link">Code Coverage</a>
    </div>
    
    <div class="section">
        <h2>🖼️ Visual Artifacts</h2>
        <a href="../screenshots/" class="link">Screenshots</a>
        <a href="../videos/" class="link">Test Videos</a>
        <a href="../traces/" class="link">Execution Traces</a>
    </div>
    
    <div class="section">
        <h[object Object]ategories</h2>
        <ul>
            <li><strong>Authentication:</strong> IBKR login and session management</li>
            <li><strong>Dashboard:</strong> Overview and statistics display</li>
            <li><strong>Strategies:</strong> Strategy management and execution</li>
            <li><strong>Workflows:</strong> Execution monitoring and control</li>
            <li><strong>Lineage:</strong> Step tracking and visualization</li>
            <li><strong>Visual:</strong> UI consistency and responsiveness</li>
            <li><strong>API:</strong> Integration and performance testing</li>
        </ul>
    </div>
</body>
</html>
EOF

print_success "Test report generated successfully!"
print_status "Report location: test-results/reports/index.html"
print_status "Open the report with: open test-results/reports/index.html"
