# Tasks: Fix Chart Storage and Access

## 1. Docker Configuration
- [x] Add shared volume `charts_data` to docker-compose.yml
- [x] Mount volume at `/app/charts` in Airflow services
- [x] Mount volume at `/app/charts` in backend service
- [x] Add `CHARTS_DIR` environment variable to Airflow
- [x] Fix permissions on `/app/charts` directory

## 2. Code Updates
- [x] Update DAGs to use `ChartGenerator(output_dir='/app/charts')`
- [x] Update `chart_images.py` to check `chart_data.minio_url` first
- [x] Ensure `chart_data` stores `minio_url` in new artifacts

## 3. Testing
- [x] Verify Docker containers don't need rebuild (only restart needed)
- [x] Verify shared volume is accessible and writable
- [x] Verify CHARTS_DIR environment variable is set
- [x] Verify charts are being saved to /app/charts
- [x] Verify backend can access files in /app/charts
- [ ] Test chart image access via API with new artifacts (waiting for new DAG run)
- [ ] Test MinIO URL handling
- [ ] Verify charts display in frontend

## Summary

✅ **Docker Configuration**: No rebuild needed, only restart required
✅ **Shared Volume**: `/app/charts` is accessible and writable in both containers
✅ **Environment Variables**: `CHARTS_DIR` is set correctly
✅ **Chart Storage**: Charts are being saved to `/app/charts` (verified: 2 PNG files found)
✅ **File Access**: Backend can access files in `/app/charts`

**Next Steps**: 
- Wait for new DAG run to create artifacts with `chart_data.minio_url`
- Test API endpoints with new artifacts
- Verify MinIO uploads are working
