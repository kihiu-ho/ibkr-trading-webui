## Why
1. **Empty Artifact Response**: Artifact endpoint `/api/artifacts/17` returns empty or incomplete data, preventing users from viewing artifact details.
2. **Charts Not in MinIO**: Chart images are stored in `/tmp/` (local paths) instead of MinIO, making them inaccessible after container restart and not visible in the artifacts page.
3. **JSON Serialization Error**: Artifact storage fails with "Object of type Decimal is not JSON serializable" error when storing artifacts with Decimal values (e.g., confidence scores).

## What Changes
- Fix artifact endpoint to properly serialize and return all artifact data
- Upload chart PNGs to MinIO and store MinIO URLs in artifacts
- Fix Decimal JSON serialization by converting Decimal to float/string before JSON serialization
- Ensure chart images are accessible via MinIO URLs in the artifacts page
- Add proper error handling for JSON serialization

## Impact
- Affected specs: `artifact-management`, `airflow-integration`
- Affected code:
  - `backend/api/artifacts.py` - Fix artifact retrieval and serialization
  - `backend/models/artifact.py` - Fix to_dict() to handle Decimal types
  - `dags/utils/artifact_storage.py` - Fix Decimal serialization in artifact storage
  - `dags/ibkr_trading_signal_workflow.py` - Upload charts to MinIO before storing artifacts
  - `frontend/templates/artifacts.html` - Display MinIO chart URLs

