# Airflow Task Instance Logs - Testing Guide

## Issue
Task instance log endpoints were returning 404 (Not Found):
- `/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-09T04:20:51.002466+00:00/taskInstances/extract_stock_data/logs/1`
- `/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-08T08:41:41+00:00/taskInstances/validate_data/logs/1`

## Solution Implemented
Added route handler for task instance logs in `backend/app/routes/airflow_proxy.py`:
```python
@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}')
```

## Testing Steps

### 1. Restart Backend Server
The new route needs to be loaded. Restart the backend service:

**If using Docker Compose:**
```bash
docker-compose restart backend
# or
docker-compose up -d --force-recreate backend
```

**If running directly:**
```bash
# Stop the server (Ctrl+C) and restart
python -m uvicorn backend.main:app --reload
```

### 2. Test the Endpoint
Run the test script:
```bash
./scripts/test_airflow_logs.sh
```

Or test manually:
```bash
curl "http://localhost:8000/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-09T04:20:51.002466+00:00/taskInstances/extract_stock_data/logs/1"
```

### 3. Expected Responses

#### Success (with logs):
```json
{
  "content": "log content here...",
  "continuation_token": "..."
}
```

#### Success (empty logs):
```json
{
  "content": "",
  "message": "No logs available for this task instance",
  "empty": true
}
```

#### Error (404 - route not found):
```json
{
  "detail": "Not Found"
}
```
**Action**: Restart the backend server

#### Error (404 - logs not found):
```json
{
  "error": "Logs not found",
  "message": "No logs available for task extract_stock_data in DAG run manual__2025-11-09T04:20:51.002466+00:00",
  "empty": true
}
```
**Action**: Check if the task instance actually has logs in Airflow

### 4. Verify Route Registration
Check backend logs for route registration:
```bash
docker-compose logs backend | grep -i "route\|airflow\|task.*log"
```

Or check if the route is accessible:
```bash
curl "http://localhost:8000/api/airflow/health"
```

## Troubleshooting

### Issue: 404 Not Found
**Possible causes:**
1. Server hasn't been restarted
2. Route not properly registered
3. URL path doesn't match route pattern

**Solutions:**
1. Restart the backend server
2. Check `backend/main.py` to ensure `airflow_proxy.router` is included
3. Verify the route pattern matches the URL format

### Issue: Empty Logs
**Possible causes:**
1. Task instance doesn't have logs (task not executed, failed early, logs cleared)
2. Airflow log directory is empty
3. Task instance ID or try_number is incorrect

**Solutions:**
1. Check Airflow UI for the task instance logs
2. Verify the task actually ran
3. Check Airflow logs directory: `reference/airflow/logs/`

### Issue: Connection Error
**Possible causes:**
1. Airflow webserver is not accessible
2. Network connectivity issues
3. Authentication failed

**Solutions:**
1. Check Airflow health: `curl http://localhost:8080/health`
2. Verify Airflow credentials in `backend/app/routes/airflow_proxy.py`
3. Check Docker network connectivity

## Route Details

### Route Pattern
```
/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}
```

### Parameters
- `dag_id`: DAG identifier (e.g., `ibkr_stock_data_workflow`)
- `dag_run_id`: DAG run ID (e.g., `manual__2025-11-09T04:20:51.002466+00:00`)
- `task_id`: Task identifier (e.g., `extract_stock_data`)
- `try_number`: Try number (e.g., `1`)

### URL Encoding
The `dag_run_id` contains special characters (`+`, `:`) that are automatically handled by FastAPI. The route handler URL-encodes the `dag_run_id` when making requests to Airflow API.

## Files Modified
- `backend/app/routes/airflow_proxy.py` - Added `task_instance_logs` route handler

## Next Steps
1. Restart backend server
2. Test the endpoints
3. Verify logs are returned correctly
4. Check backend logs for any errors

