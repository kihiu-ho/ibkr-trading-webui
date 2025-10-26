# IBKR Trading Platform E2E Tests

Comprehensive end-to-end testing suite for the IBKR Trading Platform using Playwright test automation framework.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- IBKR Paper Trading Account
- Docker (optional, for containerized testing)

### Installation

```bash
# Install test dependencies
cd tests
npm install

# Install Playwright browsers
npx playwright install

# Copy environment configuration
cp .env.example .env
# Edit .env with your IBKR paper trading credentials
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests with specific browser
npm run test -- --project=chromium

# Run in headed mode for debugging
npm run test:headed

# Run specific test categories
npm run test -- --grep="@smoke"    # Smoke tests
npm run test -- --grep="@e2e"      # End-to-end tests
npm run test -- --grep="@visual"   # Visual regression tests
npm run test -- --grep="@api"      # API integration tests

# Update visual regression snapshots
npm run update-snapshots

# Generate test report
npm run test:report
```

## 📋 Test Categories

### 🔐 Authentication Tests (`@auth`)
- IBKR paper trading login flow
- Session management and persistence
- Connection stability and reconnection
- Error handling for invalid credentials

### 📊 Dashboard Tests (`@dashboard`)
- Workflow statistics display
- Active executions monitoring
- Recent results visualization
- Real-time updates and WebSocket connections

### 🎯 Strategy Management Tests (`@strategies`)
- Strategy creation and editing
- Parameter validation and business rules
- Execution triggering and monitoring
- Status management (active/inactive)
- Search and filtering functionality

### 🔄 Workflow Execution Tests (`@workflows`)
- Real-time execution monitoring
- Step-by-step progress tracking
- Control operations (pause/resume/stop)
- Error handling and recovery
- WebSocket real-time updates

### 🔍 Lineage Tracking Tests (`@lineage`)
- Rich step visualizations
- Input/output data display
- Execution history and navigation
- Interactive step details
- Visual regression for charts and graphs

### 🎨 Visual Regression Tests (`@visual`)
- UI component consistency
- Chart and graph visualizations
- Responsive design across viewports
- Dark mode compatibility
- Accessibility compliance

### 🔗 API Integration Tests (`@api`)
- Request/response validation
- Error handling and status codes
- Performance benchmarks
- Concurrent request handling
- WebSocket functionality

## 🏗️ Test Architecture

### Page Object Model
```
tests/
├── page-objects/           # Page object models
│   ├── BasePage.ts        # Base page with common functionality
│   ├── DashboardPage.ts   # Dashboard interactions
│   ├── StrategiesPage.ts  # Strategy management
│   ├── WorkflowsPage.ts   # Workflow monitoring
│   ├── LineagePage.ts     # Lineage visualization
│   └── IBKRAuthPage.ts    # Authentication flows
├── fixtures/              # Test fixtures and utilities
│   ├── api-mocks.ts       # API response mocking
│   ├── test-data.ts       # Test data generation
│   └── test-fixtures.ts   # Custom Playwright fixtures
└── e2e/                   # Test specifications
    ├── auth.setup.ts      # Authentication setup
    ├── dashboard.spec.ts  # Dashboard tests
    ├── strategies.spec.ts # Strategy tests
    ├── workflows.spec.ts  # Workflow tests
    ├── lineage.spec.ts    # Lineage tests
    └── end-to-end-workflow.spec.ts # Complete workflows
```

### Test Data Management
- **Faker.js**: Generate realistic test data
- **API Mocking**: Consistent responses for reliable testing
- **Test Fixtures**: Reusable test setup and teardown
- **Environment Variables**: Configuration for different environments

## [object Object]onfiguration

### Environment Variables
```bash
# Application
BASE_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000/api

# IBKR Credentials (Paper Trading)
IBKR_USERNAME=loginhiuhiu250
IBKR_PASSWORD=qazwsX321
IBKR_PAPER_TRADING=true

# Test Configuration
HEADLESS=true
SLOW_MO=0
TIMEOUT=30000
WORKERS=1

# Visual Testing
VISUAL_THRESHOLD=0.2
UPDATE_SNAPSHOTS=false

# Mocking
MOCK_LLM_RESPONSES=true
MOCK_MARKET_DATA=true
MOCK_IBKR_API=false
```

### Playwright Configuration
- **Multi-browser testing**: Chromium, Firefox, WebKit
- **Parallel execution**: Configurable worker processes
- **Visual regression**: Automated screenshot comparison
- **Trace collection**: Full execution traces for debugging
- **Video recording**: Test execution videos on failure

## 🐳 Docker Support

### Running Tests in Docker
```bash
# Build and run tests
docker-compose -f docker-compose.test.yml up --build

# Run specific test suite
docker-compose -f docker-compose.test.yml run playwright-tests npx playwright test --grep="@smoke"
```

### CI/CD Integration
- **GitHub Actions**: Automated test execution on PR/push
- **Parallel execution**: Matrix strategy across browsers
- **Visual regression**: Automated snapshot comparison
- **Test reporting**: HTML reports and artifacts
- **Slack notifications**: Test results and failures

## [object Object]est Reporting

### HTML Reports
```bash
# Generate and view HTML report
npm run test:report

# Generate comprehensive report with coverage
./scripts/generate-test-report.sh
```

### Test Artifacts
- **Screenshots**: Visual evidence of test execution
- **Videos**: Full test execution recordings
- **Traces**: Detailed execution traces for debugging
- **Coverage**: Code coverage reports
- **Performance**: Load time and API response metrics

## 🔍 Debugging

### Debug Mode
```bash
# Run in debug mode (headed, slow motion)
npm run test:debug

# Debug specific test
npx playwright test --debug --grep="specific test name"

# Generate and inspect traces
npx playwright show-trace test-results/trace.zip
```

### Common Issues
1. **Application not running**: Ensure backend is started on port 8000
2. **IBKR credentials**: Verify paper trading account credentials
3. **Visual regression failures**: Update snapshots if UI changes are intentional
4. **Timeout errors**: Increase timeout for slow operations
5. **WebSocket issues**: Check real-time connection stability

## 🚦 Test Execution Strategies

### Smoke Tests
```bash
# Quick validation of core functionality
npm run test -- --grep="@smoke"
```

### Full Regression
```bash
# Complete test suite across all browsers
npm run test -- --project=chromium --project=firefox --project=webkit
```

### Visual Regression
```bash
# UI consistency validation
npm run test:visual
```

### Performance Testing
```bash
# Load time and API performance
npm run test -- --grep="@performance"
```

## 📈 Continuous Integration

The test suite integrates with GitHub Actions for:
- **Automated execution** on code changes
- **Cross-browser testing** with parallel execution
- **Visual regression detection** with diff reporting
- **Performance monitoring** with trend analysis
- **Test result publishing** with detailed reports

## 🤝 Contributing

1. **Test Structure**: Follow the page object model pattern
2. **Naming Convention**: Use descriptive test names with appropriate tags
3. **Data Management**: Use test fixtures for consistent data setup
4. **Visual Testing**: Include visual regression tests for UI changes
5. **Documentation**: Update README for new test categories or setup changes

## 📚 Resources

- [Playwright Documentation](https://playwright.dev/)
- [Page Object Model Best Practices](https://playwright.dev/docs/pom)
- [Visual Testing Guide](https://playwright.dev/docs/test-snapshots)
- [CI/CD Integration](https://playwright.dev/docs/ci)
