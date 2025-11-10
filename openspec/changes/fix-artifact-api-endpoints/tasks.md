# Tasks: Fix Artifact API Endpoints

## 1. Verify Artifact Endpoints
- [x] Test GET /api/artifacts/43
- [x] Test GET /api/artifacts/45
- [x] Verify HTTP status codes
- [x] Verify JSON response format

## 2. Verify Data Structure
- [x] Check artifact 43 (chart) has chart_data
- [x] Check artifact 45 (signal) has signal_data
- [x] Verify MinIO URL in chart_data
- [x] Verify signal_data contains all required fields

## 3. Verify JSON Serialization
- [x] Test JSON serialization for artifact 43
- [x] Test JSON serialization for artifact 45
- [x] Verify no Decimal serialization errors
- [x] Verify nested JSON structures work

## 4. Test Image Endpoint
- [x] Test GET /api/artifacts/43/image
- [x] Verify image is accessible
- [x] Verify proper content-type headers

## 5. Documentation
- [x] Document API behavior
- [x] Verify all endpoints working correctly
- [x] Create OpenSpec proposal

