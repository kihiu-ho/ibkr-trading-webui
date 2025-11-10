## Why
1. **Charts Not Stored in MinIO**: Charts are generated and stored in `/tmp/` but not uploaded to MinIO, so they're lost when containers restart. Charts need to be uploaded to MinIO and stored as artifacts with MinIO URLs.
2. **Artifacts Not Grouped**: Artifacts are displayed in a flat list. They should be grouped by symbol first, then by type (charts, LLM, signals, etc.) for better organization.
3. **LLM Analysis Bug**: The LLM analysis function has a `NameError: name 'bars' is not defined` at line 537, causing LLM analysis to fail for all symbols.

## What Changes
- Fix `NameError: bars is not defined` in LLM analysis function
- Upload charts to MinIO and store MinIO URLs in artifacts
- Update frontend to display artifacts grouped by symbol, then by type
- Ensure charts are properly stored as artifacts with MinIO URLs

## Impact
- Affected specs: `airflow-integration`, `artifact-management`
- Affected code:
  - `dags/ibkr_stock_data_workflow.py` - Fix LLM analysis bug, upload charts to MinIO
  - `dags/utils/artifact_storage.py` - Add MinIO upload functionality
  - `frontend/templates/airflow_monitor.html` - Group artifacts by symbol and type
  - `backend/api/artifacts.py` - Handle MinIO URLs in artifact storage

