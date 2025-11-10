# Tasks: Fix Chart Image Proxy and MinIO Upload

## 1. Create Chart Image Proxy Endpoint
- [x] Create `backend/api/chart_images.py` with proxy endpoint
- [x] Handle MinIO URLs (proxy requests)
- [x] Handle local file paths (search common locations)
- [x] Add proper error handling
- [x] Register router in `backend/main.py`

## 2. Update Frontend Templates
- [x] Update `frontend/templates/artifacts.html` to use proxy endpoint
- [x] Update `frontend/templates/artifact_detail.html` to use proxy endpoint
- [x] Add error handling for missing images

## 3. Verify MinIO Package Installation
- [ ] Verify `Dockerfile.airflow` includes `minio` package (already added)
- [ ] Document that container rebuild is required
- [ ] Test MinIO upload after rebuild

## 4. Testing
- [ ] Test chart image display via proxy endpoint
- [ ] Test MinIO URL proxying
- [ ] Test local file serving
- [ ] Test error handling for missing files

