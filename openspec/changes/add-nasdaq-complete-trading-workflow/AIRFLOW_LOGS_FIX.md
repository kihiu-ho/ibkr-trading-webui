# Airflow Task Instance Logs Fix

## Issue
Task instance log endpoints were returning empty responses:
- `/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-09T04:20:51.002466+00:00/taskInstances/extract_stock_data/logs/1`
- `/api/airflow/dags/ibkr_stock_data_workflow/dagRuns/manual__2025-11-08T08:41:41+00:00/taskInstances/validate_data/logs/1`

## Root Cause
The Airflow proxy router was missing a route handler for task instance logs. The endpoint pattern `/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}` was not implemented.

## Solution
Added a new route handler `task_instance_logs` that:
1. **Proxies requests** to Airflow API `/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}`
2. **URL-encodes dag_run_id** to handle special characters (colons, plus signs, etc.)
3. **Adds `full_content=true` parameter** by default to get complete logs
4. **Handles both JSON and text responses** (Airflow v1 vs v2 format)
5. **Detects empty logs** and returns appropriate messages
6. **Includes comprehensive error handling** with proper logging

## Implementation Details

### Route Definition
```python
@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}')
async def task_instance_logs(
    dag_id: str, 
    dag_run_id: str, 
    task_id: str, 
    try_number: int,
    request: Request
)
```

### Key Features
1. **URL Encoding**: Uses `urllib.parse.quote()` to properly encode `dag_run_id` for Airflow API
2. **Full Content**: Automatically adds `full_content=true` parameter to get complete logs
3. **Response Format Detection**: Handles both JSON (Airflow v2+) and text (Airflow v1) responses
4. **Empty Log Detection**: Checks if log content is empty and returns appropriate message
5. **Error Handling**: 
   - 404: Logs not found
   - 504: Request timeout
   - 500: Other errors with detailed logging

### Response Formats

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

#### Error (404):
```json
{
  "error": "Logs not found",
  "message": "No logs available for task {task_id} in DAG run {dag_run_id}",
  "empty": true
}
```

## Testing
After server restart, the endpoints should now:
1. Properly proxy requests to Airflow API
2. Return log content when available
3. Return appropriate messages when logs are empty
4. Handle errors gracefully

## Files Modified
- `backend/app/routes/airflow_proxy.py` - Added `task_instance_logs` route handler

## Next Steps
1. Restart the backend server to apply changes
2. Test the log endpoints with the provided URLs
3. Verify logs are returned correctly
4. Check backend logs for any errors or warnings

