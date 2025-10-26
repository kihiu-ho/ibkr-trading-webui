# Fix Service Startup Failures

## Why

Multiple Docker services (celery-worker, celery-beat, flower) are failing to start and continuously restarting due to Python import and syntax errors:

**Issue 1: Missing Decision Model**
```
ModuleNotFoundError: No module named 'backend.models.decision'
```
- Referenced in `backend/tasks/workflow_tasks.py` and `backend/api/dashboard.py`
- File `backend/models/decision.py` doesn't exist
- Causes all Celery services to crash on startup

**Issue 2: Invalid Async Syntax in Celery Task**
```
SyntaxError: 'await' outside async function
```
- In `backend/tasks/strategy_tasks.py` line 29
- Celery tasks are synchronous by default, but code uses `await`
- Prevents task module from loading

**Impact:**
- ❌ Celery Worker: Restarting continuously
- ❌ Celery Beat: Restarting continuously  
- ❌ Flower (monitoring): Restarting continuously
- ✓ Backend API: Running but with limited functionality
- ❌ Strategy execution: Not working
- ❌ Scheduled tasks: Not working

This completely breaks automated trading workflows and strategy execution.

## What Changes

### 1. Create Missing Decision Model
Add `backend/models/decision.py` with proper schema based on existing usage:
- Fields: strategy_id, code_id, type, current_price, target_price, stop_loss, profit_margin, r_coefficient, analysis_text
- Timestamps: created_at, updated_at
- Relationships: to Strategy and Code models
- Database table: `decisions`

### 2. Fix Async Syntax in Strategy Tasks
Replace synchronous Celery task that incorrectly uses `await`:
```python
# BEFORE (wrong)
def check_and_execute_strategies():
    service = StrategyService(db)
    due_strategies = await service.get_strategies_due_for_execution()  # ❌

# AFTER (correct)
def check_and_execute_strategies():
    service = StrategyService(db)
    due_strategies = service.get_strategies_due_for_execution()  # ✓
```

### 3. Register Decision Model in Models __init__
Add Decision to `backend/models/__init__.py` for proper imports and database initialization.

### 4. Add Health Check Improvements (Optional Enhancement)
- Add better error messages in startup script
- Detect specific failure reasons (import errors, syntax errors)
- Suggest fixes based on error patterns

## Impact

### Fixed Services
- ✅ Celery Worker: Will start successfully
- ✅ Celery Beat: Will start successfully
- ✅ Flower: Will start successfully
- ✅ Strategy Execution: Fully functional
- ✅ Scheduled Tasks: Working as expected

### Performance
- Services will start in <30 seconds (instead of infinite restart loop)
- No more resource waste from continuous crashes

### Affected Files
- **NEW**: `backend/models/decision.py` (new file)
- **MODIFIED**: `backend/models/__init__.py` (add Decision import)
- **MODIFIED**: `backend/tasks/strategy_tasks.py` (remove invalid await)
- **OPTIONAL**: `start-webapp.sh` (better error detection)

### Database
- **NEW TABLE**: `decisions` will be created on next startup
- No migration needed (SQLAlchemy auto-create with `Base.metadata.create_all()`)

### Breaking Changes
**None** - This fixes broken functionality, doesn't change any APIs or contracts.

### Benefits
1. **Working Services**: All Docker containers start successfully
2. **Complete Functionality**: Trading workflows and strategies work
3. **Better Reliability**: No more crash loops
4. **Clear Errors**: If issues occur, better debugging info
5. **Production Ready**: System is stable and functional

## Migration Path

### For Existing Users
1. Pull changes
2. Restart services: `docker-compose restart` or `./start-webapp.sh`
3. Decision table auto-creates on startup
4. All services start healthy

### Rollback Plan
- Extremely low risk (fixes bugs, doesn't change working code)
- If issues: `git revert` and restart
- No data loss (new table is additive)

## Testing Checklist

- [ ] All Docker services start without errors
- [ ] Celery worker connects and processes tasks
- [ ] Celery beat schedules tasks correctly
- [ ] Decision model can be queried from dashboard
- [ ] Strategy execution creates decision records
- [ ] No import errors in logs
- [ ] No syntax errors in logs

