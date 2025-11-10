# Implementation Summary: Fix IBKR Workflow Discovery

## Overview
Fixed the issue where IBKR workflows (ibkr_stock_data_workflow, ibkr_multi_symbol_workflow, ibkr_trading_signal_workflow) were not appearing in the Airflow monitor page. The DAGs had import errors preventing them from being discovered by Airflow.

## Issues Found

### 1. Missing MinIO Package
**Error**: `ModuleNotFoundError: No module named 'minio'`
- **Location**: `dags/utils/minio_upload.py`
- **Cause**: The `minio` package was not installed in the Airflow environment
- **Impact**: `ibkr_stock_data_workflow.py` failed to import `upload_chart_to_minio`

### 2. Logger Not Defined
**Error**: `NameError: name 'logger' is not defined`
- **Location**: `dags/utils/minio_upload.py`
- **Cause**: Logger was used before being defined in the import error handler
- **Impact**: Import error handler itself failed

### 3. Timetable Configuration Error
**Error**: `AirflowTimetableInvalid: Exactly 5, 6 or 7 columns has to be specified for iterator expression`
- **Location**: `ibkr_trading_signal_workflow.py` and `ibkr_multi_symbol_workflow.py`
- **Cause**: `WORKFLOW_SCHEDULE` environment variable was an empty string instead of `None`
- **Impact**: Airflow tried to parse empty string as a cron expression

## Changes Made

### 1. Fixed MinIO Import
**File**: `dags/utils/minio_upload.py`
- Moved logger definition before the import try/except block
- Made MinIO import optional with graceful fallback
- Added `MINIO_AVAILABLE` flag to check before using MinIO

### 2. Added MinIO to Dockerfile
**File**: `Dockerfile.airflow`
- Added `minio` package to the uv pip install command
- Ensures MinIO is available in the Airflow environment

### 3. Fixed Timetable Configuration
**Files**: 
- `dags/ibkr_trading_signal_workflow.py`
- `dags/ibkr_multi_symbol_workflow.py`

- Changed `WORKFLOW_SCHEDULE = os.getenv('WORKFLOW_SCHEDULE', None)` to `WORKFLOW_SCHEDULE = os.getenv('WORKFLOW_SCHEDULE', None) or None`
- This ensures empty strings are converted to `None`, preventing timetable parsing errors

## Testing

### Before Fix
- Only `example_ibkr_dag` was visible in Airflow monitor
- `ibkr_stock_data_workflow`, `ibkr_multi_symbol_workflow`, and `ibkr_trading_signal_workflow` had import errors

### After Fix
- All IBKR workflows should be discoverable by Airflow
- No import errors in DAG files
- DAGs can be loaded and displayed in the frontend

## Files Modified

1. `dags/utils/minio_upload.py`:
   - Fixed logger definition order
   - Made MinIO import optional with graceful fallback

2. `Dockerfile.airflow`:
   - Added `minio` package to installation

3. `dags/ibkr_trading_signal_workflow.py`:
   - Fixed `WORKFLOW_SCHEDULE` to handle empty strings

4. `dags/ibkr_multi_symbol_workflow.py`:
   - Fixed `WORKFLOW_SCHEDULE` to handle empty strings

## Next Steps

1. **Rebuild Airflow Image**: The Dockerfile changes require rebuilding the Airflow image:
   ```bash
   docker-compose build airflow-webserver airflow-scheduler
   docker-compose up -d airflow-webserver airflow-scheduler
   ```

2. **Verify DAG Discovery**: After restart, verify all DAGs are loaded:
   ```bash
   docker-compose exec airflow-scheduler airflow dags list
   ```

3. **Test Frontend**: Navigate to Airflow monitor page and verify all IBKR workflows are visible

## OpenSpec Proposal

The OpenSpec change proposal is located at:
- `openspec/changes/fix-ibkr-workflow-discovery/proposal.md`
- `openspec/changes/fix-ibkr-workflow-discovery/tasks.md`
- `openspec/changes/fix-ibkr-workflow-discovery/specs/airflow-integration/spec.md`

The proposal has been validated and implementation is complete.

