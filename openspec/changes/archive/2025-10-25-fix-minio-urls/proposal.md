# Fix MinIO URL Generation for Browser Access

## Why

Chart images are stored in MinIO, but the generated URLs use the internal Docker hostname `minio:9000`, which browsers cannot resolve. This causes:
- All chart thumbnails show placeholder images (ERR_NAME_NOT_RESOLVED)
- Charts cannot be viewed or downloaded from the frontend
- Poor user experience with broken images

Example broken URL: `http://minio:9000/trading-charts/charts/TSLA/...jpg`

The issue is that the backend needs to connect to MinIO using the internal Docker network (`minio:9000`), but browsers need to access MinIO using the external URL (`localhost:9000`).

## What Changes

### 1. Add Separate MinIO Public Endpoint
- Add `MINIO_PUBLIC_ENDPOINT` environment variable for browser-accessible URLs
- Default to `localhost:9000` for local development
- Allows different endpoints for internal (backend) and external (browser) access

### 2. Update MinIO Service
- Use `MINIO_ENDPOINT` for backend connections to MinIO
- Use `MINIO_PUBLIC_ENDPOINT` for generating browser-accessible URLs
- Maintain backward compatibility

### 3. Update Docker Compose
- Set both `MINIO_ENDPOINT` (internal) and `MINIO_PUBLIC_ENDPOINT` (external)
- Ensure frontend can access charts via localhost

## Impact

### Affected specs
- Modified: `specs/chart-viewing/spec.md` - Chart image URLs must be browser-accessible

### Affected code
- `backend/config/settings.py` - Add MINIO_PUBLIC_ENDPOINT setting
- `backend/services/minio_service.py` - Use public endpoint for URL generation
- `docker-compose.yml` - Add environment variable

### Breaking Changes
None - defaults maintain current behavior for non-Docker deployments

