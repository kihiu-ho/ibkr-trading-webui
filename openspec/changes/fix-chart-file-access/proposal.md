# Fix Chart File Access Between Containers

## Problem

Chart images stored in Airflow container's `/tmp/` directory are not accessible from the backend container, causing 404 errors:
```
Chart file not found in any location. Tried: [PosixPath('/tmp/NVDA_1D_20251109_050012.png'), ...]
```

**Root Cause**: 
- Charts are generated in Airflow container at `/tmp/`
- Backend container tries to access files but they're in a different container
- No shared volume exists between Airflow and backend for chart files
- MinIO uploads are not working (MinIO package not installed in Airflow)

## Solution

1. **Add Shared Volume**: Create a shared volume for charts between Airflow and backend containers
2. **Update Chart Storage**: Modify DAGs to save charts to the shared volume instead of `/tmp/`
3. **Update Chart Images Endpoint**: Update `chart_images.py` to check the shared volume
4. **Ensure MinIO Uploads**: Document that MinIO package needs to be installed (already in Dockerfile, requires rebuild)

## Impact

- **Backend**: Can access chart files from shared volume
- **Airflow**: Charts saved to persistent shared location
- **Frontend**: Chart images will display correctly
- **No Breaking Changes**: Existing MinIO URLs will still work

## Implementation Notes

- Shared volume path: `/app/charts` or `/opt/airflow/charts`
- Charts should be saved to shared volume in DAGs
- Fallback to MinIO URLs if available
- Graceful error handling for missing files

