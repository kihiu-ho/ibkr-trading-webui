# Tasks: Fix MinIO URL Handling in Chart Images Endpoint

## 1. Update Chart Images Endpoint
- [ ] Check `chart_data.minio_url` if `image_path` is a local path
- [ ] Prioritize MinIO URLs over local paths
- [ ] Add logging for MinIO URL detection

## 2. Testing
- [ ] Test with artifacts that have MinIO URLs in `chart_data`
- [ ] Test with artifacts that have MinIO URLs in `image_path`
- [ ] Test fallback to local paths if MinIO URL not available

