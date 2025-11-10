# Logs Endpoint 404 Fix

## Issue
The logs endpoint is still returning 404 even though the route is correctly defined:
```
GET /api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-09T04%3A37%3A41.707316%2B00%3A00/taskInstances/extract_stock_data/logs/1
```

## Root Cause Analysis

The route is correctly defined in `backend/app/routes/airflow_proxy.py`:
```python
@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}')
```

And it's placed before the less specific route:
```python
@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances')
```

## Possible Causes

1. **Server Not Restarted**: The backend server needs to be restarted to load the new route
2. **Route Caching**: FastAPI may have cached the old route structure
3. **URL Encoding Issue**: The `+` character in the URL-encoded dag_run_id might need special handling

## Solution

### Step 1: Restart Backend Server
```bash
docker-compose restart backend
# or if running directly
# Stop and restart the uvicorn process
```

### Step 2: Verify Route Registration
After restart, check if the route is registered:
```bash
curl http://localhost:8000/api/airflow/debug/routes
```

This will show all registered routes and help verify the logs route is present.

### Step 3: Test the Endpoint
```bash
curl "http://localhost:8000/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-09T04%3A37%3A41.707316%2B00%3A00/taskInstances/extract_stock_data/logs/1"
```

## Debug Logging Added

Added debug logging to the endpoint to help diagnose issues:
```python
logger.info(f"Task instance logs endpoint called: dag_id={dag_id}, dag_run_id={dag_run_id}, task_id={task_id}, try_number={try_number}")
```

Check backend logs after restart to see if the endpoint is being called.

## Expected Behavior After Restart

1. Route should match correctly
2. Debug log should appear in backend logs
3. Request should be proxied to Airflow API
4. Logs should be returned (or appropriate error message if logs don't exist)

## If Still Not Working

If the endpoint still returns 404 after restart:

1. Check backend logs for any route registration errors
2. Verify the route is in the debug/routes output
3. Check if there are any middleware or other routes intercepting the request
4. Verify FastAPI version compatibility

