# Complete IBKR Trading Workflow - Implementation Tasks

## Phase 1: Planning & Design (2 days)

### 1.1 Project Setup
- [ ] 1.1.1 Review and validate OpenSpec documentation
- [ ] 1.1.2 Create project timeline and milestones
- [ ] 1.1.3 Set up development branch: `feature/complete-workflow`
- [ ] 1.1.4 Document architectural decisions

### 1.2 Codebase Analysis
- [ ] 1.2.1 Inventory all existing modules and files
- [ ] 1.2.2 Identify modules to keep, enhance, or remove
- [ ] 1.2.3 Map dependencies between modules
- [ ] 1.2.4 Create removal checklist for unused code

### 1.3 Database Design
- [ ] 1.3.1 Design new tables: `symbols`, `user_sessions`, `portfolio_snapshots`, `workflow_lineage`
- [ ] 1.3.2 Design schema enhancements for `strategies`, `strategy_executions`
- [ ] 1.3.3 Plan data migration from old to new schema
- [ ] 1.3.4 Create database migration scripts

### 1.4 API Design
- [ ] 1.4.1 Design all new API endpoints (symbols, lineage, portfolio)
- [ ] 1.4.2 Define request/response schemas
- [ ] 1.4.3 Document API contracts
- [ ] 1.4.4 Plan API versioning strategy

---

## Phase 2: Core Workflow Implementation (5 days)

### 2.1 User Authentication (Step 1)
- [ ] 2.1.1 Enhance IBKR authentication service
- [ ] 2.1.2 Implement session management with `user_sessions` table
- [ ] 2.1.3 Create session expiry and renewal logic
- [ ] 2.1.4 Add authentication middleware to all protected routes
- [ ] 2.1.5 Test multi-user session handling

### 2.2 Symbol Search Service (Step 2)
- [ ] 2.2.1 Create `backend/services/symbol_search.py`
- [ ] 2.2.2 Implement IBKR symbol search integration
- [ ] 2.2.3 Create `symbols` table migration
- [ ] 2.2.4 Implement symbol caching logic (Redis + DB)
- [ ] 2.2.5 Create API endpoints: `/api/symbols/search`, `/api/symbols/{conid}`
- [ ] 2.2.6 Create Pydantic schemas for symbol data
- [ ] 2.2.7 Enhance `symbols.html` with search UI
- [ ] 2.2.8 Add symbol search JavaScript component
- [ ] 2.2.9 Test symbol search with various queries

### 2.3 Indicator Configuration (Step 3)
- [ ] 2.3.1 Enhance `backend/services/indicator_service.py`
- [ ] 2.3.2 Define all available indicators (RSI, MACD, ATR, SMA, EMA, BB, SuperTrend)
- [ ] 2.3.3 Implement indicator parameter validation
- [ ] 2.3.4 Create API endpoints for indicator CRUD
- [ ] 2.3.5 Enhance `indicators.html` with configuration UI
- [ ] 2.3.6 Add indicator preview/validation in frontend
- [ ] 2.3.7 Test all indicator configurations

### 2.4 Strategy Creation (Step 5)
- [ ] 2.4.1 Create `backend/services/strategy_service.py`
- [ ] 2.4.2 Implement strategy creation with all components (symbol, indicators, prompt, schedule, risk)
- [ ] 2.4.3 Add strategy CRUD API endpoints
- [ ] 2.4.4 Enhance `strategies` table with new fields
- [ ] 2.4.5 Create database migration for strategy enhancements
- [ ] 2.4.6 Enhance `strategies.html` with comprehensive creation wizard
- [ ] 2.4.7 Add strategy validation logic
- [ ] 2.4.8 Test strategy creation end-to-end

### 2.5 Scheduled Execution (Step 6)
- [ ] 2.5.1 Create `backend/tasks/strategy_execution.py`
- [ ] 2.5.2 Implement Celery task: `execute_strategy`
- [ ] 2.5.3 Create Celery Beat schedule loader
- [ ] 2.5.4 Implement dynamic schedule updates
- [ ] 2.5.5 Add cron expression parser and validator
- [ ] 2.5.6 Test scheduled execution with various cron patterns
- [ ] 2.5.7 Implement execution retry logic
- [ ] 2.5.8 Add execution logging and monitoring

---

## Phase 3: LLM Integration & Signals (3 days)

### 3.1 Chart Generation (Step 7)
- [ ] 3.1.1 Enhance `backend/services/chart_generator.py`
- [ ] 3.1.2 Implement multi-timeframe chart generation (daily, weekly)
- [ ] 3.1.3 Add indicator overlays to charts (mplfinance)
- [ ] 3.1.4 Implement chart upload to MinIO
- [ ] 3.1.5 Add chart metadata storage
- [ ] 3.1.6 Test chart generation with various indicator combinations
- [ ] 3.1.7 Optimize chart rendering performance

### 3.2 LLM Signal Generation (Step 8)
- [ ] 3.2.1 Create `backend/services/signal_generator.py`
- [ ] 3.2.2 Integrate with existing prompt system (Phases 1-14)
- [ ] 3.2.3 Implement strategy-specific prompt loading
- [ ] 3.2.4 Implement Jinja2 context building for LLM
- [ ] 3.2.5 Enhance `backend/services/llm_service.py` for chart analysis
- [ ] 3.2.6 Implement signal parsing from LLM response
- [ ] 3.2.7 Add signal validation and confidence scoring
- [ ] 3.2.8 Store signals in `trading_signals` table
- [ ] 3.2.9 Link signals to prompt templates for traceability
- [ ] 3.2.10 Test LLM signal generation with various market conditions

### 3.3 Strategy Executor (Core Engine)
- [ ] 3.3.1 Create `backend/services/strategy_executor.py`
- [ ] 3.3.2 Implement complete execution workflow (Steps 1-8)
- [ ] 3.3.3 Add robust error handling for each step
- [ ] 3.3.4 Implement execution state management
- [ ] 3.3.5 Add execution result recording
- [ ] 3.3.6 Test executor with mock data
- [ ] 3.3.7 Test executor with live IBKR connection

---

## Phase 4: Order Management (4 days)

### 4.1 Order Placement Service (Step 9)
- [ ] 4.1.1 Create `backend/services/order_manager.py`
- [ ] 4.1.2 Implement buy order placement
- [ ] 4.1.3 Implement position size calculation
- [ ] 4.1.4 Implement risk management checks
- [ ] 4.1.5 Add order validation (price, quantity, available capital)
- [ ] 4.1.6 Enhance IBKR service for order placement
- [ ] 4.1.7 Store orders in `orders` table
- [ ] 4.1.8 Test order placement with paper trading account

### 4.2 Position Management (Step 10)
- [ ] 4.2.1 Create `backend/services/position_manager.py`
- [ ] 4.2.2 Implement sell order placement
- [ ] 4.2.3 Implement stop-loss monitoring
- [ ] 4.2.4 Implement take-profit monitoring
- [ ] 4.2.5 Add position tracking and updates
- [ ] 4.2.6 Create Celery task for position monitoring
- [ ] 4.2.7 Test position management lifecycle

### 4.3 Order Status Tracking (Step 11)
- [ ] 4.3.1 Create `backend/tasks/order_monitoring.py`
- [ ] 4.3.2 Create `backend/services/order_tracker.py`
- [ ] 4.3.3 Implement order status polling from IBKR
- [ ] 4.3.4 Implement order fill detection
- [ ] 4.3.5 Implement order cancellation/rejection handling
- [ ] 4.3.6 Add position updates on order fill
- [ ] 4.3.7 Record trades on order completion
- [ ] 4.3.8 Update signal outcomes for performance tracking
- [ ] 4.3.9 Add order status notifications
- [ ] 4.3.10 Test order tracking lifecycle

### 4.4 Portfolio Service (Step 12)
- [ ] 4.4.1 Create `backend/services/portfolio_service.py`
- [ ] 4.4.2 Implement portfolio value calculation
- [ ] 4.4.3 Implement P&L calculation (realized and unrealized)
- [ ] 4.4.4 Create `portfolio_snapshots` table migration
- [ ] 4.4.5 Implement portfolio snapshot recording
- [ ] 4.4.6 Calculate portfolio statistics (win rate, avg P&L, etc.)
- [ ] 4.4.7 Create API endpoints for portfolio data
- [ ] 4.4.8 Test portfolio updates with sample trades

---

## Phase 5: Lineage Tracking (3 days)

### 5.1 Lineage Tracker Service (Step 13)
- [ ] 5.1.1 Create `backend/services/lineage_tracker.py`
- [ ] 5.1.2 Implement `LineageTracker` class with `record_step()` method
- [ ] 5.1.3 Create `workflow_lineage` table migration
- [ ] 5.1.4 Implement lineage storage in database
- [ ] 5.1.5 Implement lineage retrieval methods
- [ ] 5.1.6 Create SQLAlchemy model: `LineageRecord`
- [ ] 5.1.7 Test lineage recording for all workflow steps

### 5.2 Integrate Lineage into Strategy Executor
- [ ] 5.2.1 Add lineage tracking to all steps in `StrategyExecutor`
- [ ] 5.2.2 Record input data before each step
- [ ] 5.2.3 Record output data after each step
- [ ] 5.2.4 Record step duration
- [ ] 5.2.5 Record errors and exceptions
- [ ] 5.2.6 Add execution_id to `strategy_executions` table
- [ ] 5.2.7 Test lineage tracking with complete workflow execution

### 5.3 Lineage API
- [ ] 5.3.1 Create `backend/api/lineage.py`
- [ ] 5.3.2 Implement endpoint: `GET /api/lineage/execution/{execution_id}`
- [ ] 5.3.3 Implement endpoint: `GET /api/lineage/execution/{execution_id}/step/{step_name}`
- [ ] 5.3.4 Implement endpoint: `GET /api/lineage/strategy/{strategy_id}/recent`
- [ ] 5.3.5 Implement endpoint: `GET /api/lineage/step/{step_name}/statistics`
- [ ] 5.3.6 Create Pydantic schemas for lineage data
- [ ] 5.3.7 Test all lineage API endpoints

### 5.4 Lineage Viewer Frontend
- [ ] 5.4.1 Create `frontend/templates/lineage.html`
- [ ] 5.4.2 Create `frontend/static/js/lineage-viewer.js`
- [ ] 5.4.3 Create `frontend/static/css/lineage.css`
- [ ] 5.4.4 Implement strategy selector dropdown
- [ ] 5.4.5 Implement execution selector dropdown
- [ ] 5.4.6 Implement step card visualization
- [ ] 5.4.7 Implement input/output display
- [ ] 5.4.8 Implement step detail modal
- [ ] 5.4.9 Add error highlighting and display
- [ ] 5.4.10 Add duration and performance metrics
- [ ] 5.4.11 Test lineage viewer UI with sample data

### 5.5 Dashboard Integration
- [ ] 5.5.1 Add "View Lineage" button to strategy cards
- [ ] 5.5.2 Add lineage link to signals page
- [ ] 5.5.3 Add lineage summary to execution history
- [ ] 5.5.4 Add "Lineage" to sidebar navigation
- [ ] 5.5.5 Test navigation to lineage viewer

---

## Phase 6: Cleanup & Refactoring (3 days)

### 6.1 Remove Unused Modules
- [ ] 6.1.1 Remove `workflows/` directory and related code
- [ ] 6.1.2 Remove `decisions/` directory and related code
- [ ] 6.1.3 Remove redundant `analysis.html` page
- [ ] 6.1.4 Remove extra logs pages
- [ ] 6.1.5 Clean up unused imports across codebase
- [ ] 6.1.6 Remove unused database tables
- [ ] 6.1.7 Update all references to removed modules
- [ ] 6.1.8 Test application after removals

### 6.2 Database Migration
- [ ] 6.2.1 Create master migration script for all new tables
- [ ] 6.2.2 Create data migration script (old → new schema)
- [ ] 6.2.3 Test migration on development database
- [ ] 6.2.4 Create rollback scripts
- [ ] 6.2.5 Document migration process

### 6.3 Code Refactoring
- [ ] 6.3.1 Refactor existing services to use new workflow
- [ ] 6.3.2 Consolidate duplicate code
- [ ] 6.3.3 Improve error handling consistency
- [ ] 6.3.4 Add type hints to all new code
- [ ] 6.3.5 Run linter and fix all issues
- [ ] 6.3.6 Optimize database queries
- [ ] 6.3.7 Add logging to all critical paths

### 6.4 Frontend Cleanup
- [ ] 6.4.1 Update sidebar navigation (remove old pages, add new ones)
- [ ] 6.4.2 Update dashboard to reflect new workflow
- [ ] 6.4.3 Remove unused JavaScript files
- [ ] 6.4.4 Remove unused CSS styles
- [ ] 6.4.5 Consolidate frontend components
- [ ] 6.4.6 Test all frontend pages

---

## Phase 7: Frontend Implementation (4 days)

### 7.1 Orders Page
- [ ] 7.1.1 Create `frontend/templates/orders.html`
- [ ] 7.1.2 Create `frontend/static/js/orders.js`
- [ ] 7.1.3 Implement order list view
- [ ] 7.1.4 Implement order detail view
- [ ] 7.1.5 Add order status filtering
- [ ] 7.1.6 Add real-time order status updates (WebSocket or polling)
- [ ] 7.1.7 Add order cancellation functionality
- [ ] 7.1.8 Test orders page

### 7.2 Portfolio Page
- [ ] 7.2.1 Create `frontend/templates/portfolio.html`
- [ ] 7.2.2 Create `frontend/static/js/portfolio.js`
- [ ] 7.2.3 Implement portfolio summary dashboard
- [ ] 7.2.4 Implement position list view
- [ ] 7.2.5 Add portfolio statistics display (win rate, P&L, etc.)
- [ ] 7.2.6 Add portfolio history chart
- [ ] 7.2.7 Add portfolio refresh button
- [ ] 7.2.8 Test portfolio page

### 7.3 Enhanced Dashboard
- [ ] 7.3.1 Update `dashboard.html` with new workflow overview
- [ ] 7.3.2 Add portfolio summary widget
- [ ] 7.3.3 Add recent signals widget
- [ ] 7.3.4 Add active strategies widget
- [ ] 7.3.5 Add recent orders widget
- [ ] 7.3.6 Add quick action buttons
- [ ] 7.3.7 Test dashboard

### 7.4 Strategy Wizard
- [ ] 7.4.1 Create multi-step strategy creation wizard
- [ ] 7.4.2 Step 1: Symbol search and selection
- [ ] 7.4.3 Step 2: Indicator configuration
- [ ] 7.4.4 Step 3: Prompt selection
- [ ] 7.4.5 Step 4: Schedule configuration
- [ ] 7.4.6 Step 5: Risk parameters
- [ ] 7.4.7 Step 6: Review and submit
- [ ] 7.4.8 Add progress indicator
- [ ] 7.4.9 Add validation at each step
- [ ] 7.4.10 Test wizard flow

---

## Phase 8: Testing & Documentation (3 days)

### 8.1 Unit Tests
- [ ] 8.1.1 Write tests for `symbol_search.py`
- [ ] 8.1.2 Write tests for `strategy_service.py`
- [ ] 8.1.3 Write tests for `strategy_executor.py`
- [ ] 8.1.4 Write tests for `order_manager.py`
- [ ] 8.1.5 Write tests for `position_manager.py`
- [ ] 8.1.6 Write tests for `portfolio_service.py`
- [ ] 8.1.7 Write tests for `lineage_tracker.py`
- [ ] 8.1.8 Achieve 80%+ test coverage
- [ ] 8.1.9 Run all tests and fix failures

### 8.2 Integration Tests
- [ ] 8.2.1 Test complete workflow end-to-end (mock IBKR)
- [ ] 8.2.2 Test strategy execution with paper trading account
- [ ] 8.2.3 Test order placement and tracking
- [ ] 8.2.4 Test portfolio updates
- [ ] 8.2.5 Test lineage tracking
- [ ] 8.2.6 Test error scenarios and recovery
- [ ] 8.2.7 Test concurrent strategy executions
- [ ] 8.2.8 Test database transaction integrity

### 8.3 Performance Testing
- [ ] 8.3.1 Load test API endpoints
- [ ] 8.3.2 Test chart generation performance
- [ ] 8.3.3 Test LLM API response times
- [ ] 8.3.4 Test database query performance
- [ ] 8.3.5 Optimize slow queries
- [ ] 8.3.6 Test Celery worker throughput
- [ ] 8.3.7 Verify end-to-end workflow completes in < 5 minutes

### 8.4 User Acceptance Testing
- [ ] 8.4.1 Create test scenarios for each workflow step
- [ ] 8.4.2 Test with different user roles
- [ ] 8.4.3 Test error messages and user feedback
- [ ] 8.4.4 Test UI responsiveness
- [ ] 8.4.5 Test mobile compatibility
- [ ] 8.4.6 Gather and address feedback

### 8.5 Documentation
- [ ] 8.5.1 Write user guide for complete workflow
- [ ] 8.5.2 Document all API endpoints (OpenAPI/Swagger)
- [ ] 8.5.3 Write developer setup guide
- [ ] 8.5.4 Document database schema
- [ ] 8.5.5 Write troubleshooting guide
- [ ] 8.5.6 Create video walkthrough (optional)
- [ ] 8.5.7 Update README.md
- [ ] 8.5.8 Archive OpenSpec change to `changes/archive/`

---

## Phase 9: Deployment (2 days)

### 9.1 Pre-Deployment
- [ ] 9.1.1 Run full test suite
- [ ] 9.1.2 Run linter and fix all issues
- [ ] 9.1.3 Review all code changes
- [ ] 9.1.4 Create deployment checklist
- [ ] 9.1.5 Backup production database
- [ ] 9.1.6 Test database migration on staging

### 9.2 Deployment
- [ ] 9.2.1 Deploy database migrations
- [ ] 9.2.2 Deploy backend code
- [ ] 9.2.3 Deploy frontend code
- [ ] 9.2.4 Restart Celery workers
- [ ] 9.2.5 Restart Celery Beat
- [ ] 9.2.6 Verify all services are running
- [ ] 9.2.7 Run smoke tests

### 9.3 Post-Deployment
- [ ] 9.3.1 Monitor application logs for errors
- [ ] 9.3.2 Monitor Celery task execution
- [ ] 9.3.3 Verify scheduled strategies are executing
- [ ] 9.3.4 Check database performance
- [ ] 9.3.5 Verify IBKR connectivity
- [ ] 9.3.6 Monitor LLM API usage
- [ ] 9.3.7 Set up alerting for critical errors

### 9.4 Rollback Plan
- [ ] 9.4.1 Document rollback procedure
- [ ] 9.4.2 Test rollback on staging
- [ ] 9.4.3 Keep backup of previous version
- [ ] 9.4.4 Monitor for 48 hours post-deployment

---

## Summary Statistics

**Total Tasks**: ~250
**Estimated Duration**: 20 working days (4 weeks)
**Critical Path**: Strategy Executor → Order Management → Lineage Tracking
**Dependencies**: 
- Existing Prompt System (Complete ✅)
- IBKR Gateway (Exists ✅)
- Database (Exists ✅)
- Celery (Exists ✅)

**Key Milestones**:
1. ✅ Phase 1 Complete: Design finalized
2. ⏳ Phase 2 Complete: Core workflow operational
3. ⏳ Phase 3 Complete: LLM signals generating
4. ⏳ Phase 4 Complete: Orders placing successfully
5. ⏳ Phase 5 Complete: Lineage tracking functional
6. ⏳ Phase 6 Complete: Codebase cleaned
7. ⏳ Phase 7 Complete: Frontend complete
8. ⏳ Phase 8 Complete: All tests passing
9. ⏳ Phase 9 Complete: Production deployment

---

## Notes

- All tasks should be completed in order within each phase
- Tasks marked with ⚠️ are high-risk and require extra attention
- Cross-phase dependencies are noted in task descriptions
- Update this file as tasks are completed
- Use `- [x]` to mark completed tasks

