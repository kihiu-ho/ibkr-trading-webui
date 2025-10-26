# Implementation Tasks

## 1. Create Decision Model
- [x] 1.1 Create `backend/models/decision.py` file
- [x] 1.2 Define Decision class inheriting from Base
- [x] 1.3 Add table name `decisions`
- [x] 1.4 Add columns: id, strategy_id, code_id, type, current_price, target_price, stop_loss, profit_margin, r_coefficient, analysis_text
- [x] 1.5 Add timestamps: created_at, updated_at
- [x] 1.6 Add foreign key relationships to Strategy and Code
- [x] 1.7 Add indexes for common queries (strategy_id, created_at)

## 2. Register Decision Model
- [x] 2.1 Add Decision import to `backend/models/__init__.py`
- [x] 2.2 Add Decision to `__all__` list
- [x] 2.3 Verify Base includes Decision for table creation

## 3. Fix Strategy Tasks Async Issue
- [x] 3.1 Open `backend/tasks/strategy_tasks.py`
- [x] 3.2 Find line 29 with `await service.get_strategies_due_for_execution()`
- [x] 3.3 Remove `await` keyword (make synchronous call)
- [x] 3.4 Verify StrategyService method is synchronous (not async)
- [x] 3.5 If method is async, create synchronous wrapper or make it sync

## 4. Verify Imports and Dependencies
- [x] 4.1 Check all files importing Decision model
- [x] 4.2 Verify `backend/tasks/workflow_tasks.py` line 6 works
- [x] 4.3 Verify `backend/api/dashboard.py` line 10 works
- [x] 4.4 Test import chain doesn't have circular dependencies

## 5. Test Service Startup
- [x] 5.1 Stop all services: `docker-compose down`
- [x] 5.2 Start services: `docker-compose up -d`
- [x] 5.3 Check celery-worker logs: `docker logs ibkr-celery-worker`
- [x] 5.4 Check celery-beat logs: `docker logs ibkr-celery-beat`
- [x] 5.5 Check flower logs: `docker logs ibkr-flower`
- [x] 5.6 Check backend logs: `docker logs ibkr-backend`
- [x] 5.7 Verify all services show "Up" status: `docker-compose ps`

## 6. Test Database Schema
- [x] 6.1 Connect to database
- [x] 6.2 Verify `decisions` table exists
- [x] 6.3 Verify all columns are present
- [x] 6.4 Verify foreign keys are correct
- [x] 6.5 Test insert/query operations

## 7. Test Functionality
- [x] 7.1 Access dashboard at http://localhost:8000/dashboard
- [x] 7.2 Verify "recent_decisions" stat loads without error
- [x] 7.3 Test strategy execution workflow
- [x] 7.4 Verify Decision records are created
- [x] 7.5 Check Celery tasks in Flower UI (http://localhost:5555)

## 8. Optional: Enhance Startup Script
- [x] 8.1 Add error pattern detection in `start-webapp.sh`
- [x] 8.2 Detect import errors and suggest fixes
- [x] 8.3 Detect syntax errors and suggest fixes
- [x] 8.4 Add service-specific health check messages

## 9. Documentation
- [x] 9.1 Update README if needed
- [x] 9.2 Document Decision model schema
- [x] 9.3 Add troubleshooting guide for service failures

## 10. Validation
- [x] 10.1 Run `openspec validate fix-service-startup-failures --strict`
- [x] 10.2 Ensure no regressions in existing functionality
- [x] 10.3 Verify all services remain healthy for 5+ minutes

