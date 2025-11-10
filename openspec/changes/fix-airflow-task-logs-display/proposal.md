## Why
The Airflow task instance logs endpoint returns log content, but when users click "View Logs" in the Airflow monitor, it opens a new tab showing raw JSON instead of formatted, readable logs. This makes debugging workflow issues difficult and provides a poor user experience.

## What Changes
- Add a formatted HTML page endpoint for displaying task logs in a readable format
- Update the frontend to display logs in a modal instead of opening a new tab
- Ensure logs are properly formatted with syntax highlighting and line numbers
- Handle empty logs gracefully with clear messaging
- Support streaming logs for long-running tasks

## Impact
- Affected specs: `airflow-integration`
- Affected code: 
  - `backend/app/routes/airflow_proxy.py` - Add formatted logs endpoint
  - `frontend/templates/airflow_monitor.html` - Update logs display to use modal
  - `frontend/static/js/` - Add logs modal component (if needed)

