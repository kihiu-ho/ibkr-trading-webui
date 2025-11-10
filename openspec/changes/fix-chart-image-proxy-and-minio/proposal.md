# Fix Chart Image Proxy and MinIO Upload

## Problem

1. **404 errors for chart images**: Frontend tries to load local paths like `/tmp/TSLA_1D_20251109_050013.png` as URLs, causing 404 errors
2. **MinIO package not installed**: MinIO package is not available in Airflow container, preventing chart uploads
3. **Empty artifact responses**: Some artifact endpoints may appear empty due to serialization issues

## Solution

1. **Create chart image proxy endpoint**: Add `/api/artifacts/{id}/image` endpoint that:
   - Proxies MinIO URLs if `image_path` is a URL
   - Serves local files if `image_path` is a local path
   - Searches common locations for local files
   - Returns proper error messages if file not found

2. **Update frontend to use proxy**: Modify frontend templates to use the proxy endpoint instead of direct paths

3. **Ensure MinIO package is installed**: Verify Dockerfile.airflow includes minio package (already added, container needs rebuild)

## Impact

- **Frontend**: Chart images will display correctly via proxy endpoint
- **Backend**: New proxy endpoint for serving chart images
- **Airflow**: MinIO uploads will work after container rebuild

## Implementation Notes

- Chart image proxy handles both MinIO URLs and local file paths
- Frontend gracefully handles missing images with error messages
- MinIO package installation requires container rebuild

