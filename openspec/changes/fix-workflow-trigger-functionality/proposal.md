# Fix Workflow Trigger Functionality

## Why

The `ibkr_trading_signal_workflow` trigger functionality is not working properly from the UI:
1. Users report that the workflow "cannot be triggered" despite the trigger button being visible
2. Trigger requests may succeed but workflow runs remain in "queued" state indefinitely
3. No clear feedback to users about why workflow is queued or blocked
4. Missing error handling for trigger failures
5. No indication of active runs blocking new triggers (due to `max_active_runs=1`)

The workflow has `max_active_runs=1` which means if one run is active, new triggers will be queued but may appear as if they're not working.

## What Changes

### 1. Enhanced Trigger Error Handling
- **File**: `frontend/templates/airflow_monitor.html`
- **Issue**: Generic error messages don't explain why trigger failed
- **Fix**: 
  - Add detailed error handling for common scenarios:
    - DAG is paused
    - DAG has import errors
    - Maximum active runs reached (workflow already running)
    - Airflow API unavailable
    - Permission errors
  - Display user-friendly error messages with actionable suggestions
- **Impact**: Users understand why trigger failed and how to fix it

### 2. Trigger Status Feedback
- **File**: `frontend/templates/airflow_monitor.html`
- **Issue**: No immediate feedback after triggering
- **Fix**:
  - Show loading state during trigger request
  - Display success message with run ID and status
  - Show queued status if workflow is waiting due to max_active_runs
  - Auto-refresh DAG list after successful trigger
  - Highlight newly triggered run in the runs table
- **Impact**: Users get immediate confirmation that trigger was successful

### 3. Active Run Detection and Warnings
- **File**: `frontend/templates/airflow_monitor.html`
- **Issue**: Users don't know if an active run is blocking new triggers
- **Fix**:
  - Check for active/running DAG runs before allowing trigger
  - Display warning if max_active_runs limit would block new trigger
  - Show active run information (run ID, start time, duration)
  - Provide option to cancel active run before triggering new one
  - Disable trigger button with tooltip explaining why (if blocked)
- **Impact**: Users understand when and why triggers are blocked

### 4. Backend Trigger Validation
- **File**: `backend/app/routes/airflow_proxy.py`
- **Issue**: Backend doesn't validate trigger conditions before forwarding to Airflow
- **Fix**:
  - Check DAG status before triggering (paused, import errors)
  - Check active runs count vs max_active_runs limit
  - Return meaningful error messages for blocked triggers
  - Validate DAG exists and is accessible
- **Impact**: Better error handling and user feedback

### 5. Workflow Run Status Monitoring
- **File**: `frontend/templates/airflow_monitor.html`
- **Issue**: Queued runs may appear stuck with no explanation
- **Fix**:
  - Monitor queued runs and display status
  - Show estimated wait time if run is queued due to max_active_runs
  - Auto-refresh queued runs to show when they start
  - Display clear indicators for queued vs running vs failed states
- **Impact**: Users understand workflow status and don't think it's broken

### 6. Trigger Confirmation Dialog Enhancement
- **File**: `frontend/templates/airflow_monitor.html`
- **Issue**: Generic confirmation doesn't warn about potential blocking
- **Fix**:
  - Enhanced confirmation dialog showing:
    - Current active runs count
    - Estimated wait time if run will be queued
    - Option to cancel active run first
    - DAG configuration summary
  - Allow users to proceed with queued trigger or cancel
- **Impact**: Informed decisions about when to trigger workflows

## Impact

- **Affected specs**: `airflow-integration`, `frontend-workflow-visualization`
- **Affected code**:
  - `frontend/templates/airflow_monitor.html` - Enhanced trigger UI and error handling
  - `backend/app/routes/airflow_proxy.py` - Added trigger validation
  - JavaScript in airflow_monitor.html - Improved trigger logic and feedback

## Testing

1. **Trigger with no active runs**: Verify workflow triggers immediately and shows success
2. **Trigger with active run**: Verify workflow is queued with clear status message
3. **Trigger with paused DAG**: Verify error message explains DAG is paused
4. **Trigger with import errors**: Verify error message explains import errors
5. **Trigger with API error**: Verify error message explains connection issue
6. **Auto-refresh after trigger**: Verify DAG list updates and new run appears
7. **Active run detection**: Verify warning appears when active run blocks trigger
8. **Cancel active run**: Verify option to cancel active run before triggering new one

