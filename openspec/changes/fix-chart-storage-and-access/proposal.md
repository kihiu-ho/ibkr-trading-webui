# Fix Chart Storage and Access

## Problem

Chart images were not accessible from the backend container, causing 404 errors:
- Charts were stored in `/tmp/` on Airflow container (ephemeral, not accessible from backend)
- `CHARTS_DIR` environment variable was not set
- `/app/charts` shared volume had incorrect permissions
- Old artifacts had files in `/tmp/` that no longer exist

## Root Cause

1. **No shared volume**: Charts were saved to `/tmp/` which is not accessible from backend container
2. **Missing environment variable**: `CHARTS_DIR` was not set in Airflow environment
3. **Permission issues**: `/app/charts` directory was not writable by Airflow user
4. **MinIO URLs not prioritized**: Endpoint didn't check `chart_data.minio_url` first

## Solution

1. **Added shared volume**: Created `charts_data` volume mounted at `/app/charts` in both Airflow and backend
2. **Set CHARTS_DIR**: Added `CHARTS_DIR: "/app/charts"` to Airflow environment
3. **Fixed permissions**: Changed ownership of `/app/charts` to `airflow:root`
4. **Updated DAGs**: Modified all DAGs to use `ChartGenerator(output_dir='/app/charts')`
5. **Updated endpoint**: Modified `chart_images.py` to check `chart_data.minio_url` first

## Impact

- **Backend**: Can access chart files from shared volume
- **Airflow**: Charts saved to persistent shared location
- **Frontend**: Chart images will display correctly
- **MinIO**: Charts uploaded to MinIO will be accessible via URLs
- **No Breaking Changes**: Existing MinIO URLs will still work

## Implementation Notes

- Shared volume path: `/app/charts` (accessible from both containers)
- Charts saved to shared volume, then uploaded to MinIO
- MinIO URLs stored in `chart_data.minio_url`
- Endpoint checks MinIO URL first, then falls back to local paths

