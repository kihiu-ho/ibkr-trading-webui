## 1. Fix Artifact Endpoint
- [x] 1.1 Fix empty artifact response issue
- [x] 1.2 Ensure all artifact fields are properly serialized
- [x] 1.3 Add error handling for missing artifacts

## 2. Fix Decimal JSON Serialization
- [x] 2.1 Convert Decimal to float/string before JSON serialization
- [x] 2.2 Fix artifact storage to handle Decimal types
- [x] 2.3 Update artifact model to_dict() to handle Decimal fields

## 3. Upload Charts to MinIO
- [x] 3.1 Upload chart PNGs to MinIO in workflow
- [x] 3.2 Store MinIO URLs in artifacts instead of local paths
- [x] 3.3 Update frontend to display MinIO chart URLs

## 4. Testing
- [x] 4.1 Test artifact endpoint returns complete data
- [x] 4.2 Test Decimal serialization doesn't cause errors
- [x] 4.3 Test chart upload to MinIO
- [x] 4.4 Test chart display in artifacts page

