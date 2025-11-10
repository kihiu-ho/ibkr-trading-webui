# Fix Workflow Chart Generator and Celery Errors

## Why

The `ibkr_trading_signal_workflow` was failing during execution due to multiple errors:
1. Chart generation tasks failing with Plotly yref validation errors
2. Celery worker unable to start due to missing workflow_tasks module
3. Celery worker unable to start due to missing strategy_service module

These errors prevented the workflow from completing successfully and blocked Celery worker initialization.

## What Changes

### 1. Fixed Chart Generator Plotly yref Error
- **File**: `dags/utils/chart_generator.py`
- **Issue**: `add_max_min_avg()` function was passing invalid yref values ("Price", "SuperTrend", etc.) to Plotly annotations
- **Error**: `ValueError: Invalid value of type 'builtins.str' received for the 'yref' property of layout.annotation`
- **Fix**: 
  - Added `_primary_yref()` helper function to correctly map subplot row indices to Plotly y-axis references
  - Updated `add_max_min_avg()` to use `yref=_primary_yref(row)` instead of passing axis label strings
  - yref now correctly uses format: "y", "y1", "y3", "y5", etc. based on subplot row
- **Impact**: Chart generation tasks now complete successfully without Plotly validation errors

### 2. Fixed Missing workflow_tasks Module
- **File**: `backend/tasks/__init__.py`
- **Issue**: Importing non-existent `backend.tasks.workflow_tasks` module
- **Error**: `ModuleNotFoundError: No module named 'backend.tasks.workflow_tasks'`
- **Fix**: Removed the import statement from `__init__.py`
- **Impact**: Celery worker can now start without import errors

### 3. Temporarily Disabled strategy_tasks
- **File**: `backend/celery_app.py`
- **Issue**: `strategy_tasks` module imports `StrategyService` which doesn't exist
- **Error**: `ModuleNotFoundError: No module named 'backend.services.strategy_service'`
- **Fix**: 
  - Commented out `strategy_tasks` import
  - Commented out related Celery Beat schedule entries:
    - `check-and-execute-strategies`
    - `recalculate-strategy-schedules`
    - `cleanup-inactive-strategies-weekly`
- **Impact**: Celery worker and beat can start successfully
- **Note**: These tasks should be re-enabled once `strategy_service` is implemented

## Impact

- **Affected specs**: `airflow-integration`, `chart-generation`
- **Affected code**:
  - `dags/utils/chart_generator.py` - Fixed Plotly annotation yref values
  - `backend/tasks/__init__.py` - Removed non-existent module import
  - `backend/celery_app.py` - Temporarily disabled strategy tasks

## Testing

1. **Chart Generation**: Trigger `ibkr_trading_signal_workflow` and verify `generate_daily_chart` and `generate_weekly_chart` tasks complete successfully
2. **Celery Worker**: Verify Celery worker starts without import errors
3. **Celery Beat**: Verify Celery beat starts without import errors
4. **Workflow Execution**: Verify workflow completes end-to-end without errors

