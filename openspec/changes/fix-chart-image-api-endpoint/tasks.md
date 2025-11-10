# Tasks: Fix Chart Image API Endpoint

## 1. Improve File Search Logic
- [x] Add pattern matching for files by symbol and timeframe
- [x] Map chart_type to timeframe code (daily -> 1D, weekly -> 1W)
- [x] Search for files matching pattern when exact file doesn't exist
- [x] Use most recent matching file if multiple found

## 2. Improve Error Messages
- [x] Return helpful error messages for old artifacts
- [x] Explain that files may have been deleted from /tmp/
- [x] Document that new artifacts use /app/charts and MinIO

## 3. Prioritize MinIO URLs
- [x] Check chart_data.minio_url first before searching local files
- [x] Use MinIO URL if available, regardless of image_path value

## 4. Testing
- [ ] Test with old artifacts (ID 5, etc.)
- [ ] Test with new artifacts
- [ ] Test with artifacts that have MinIO URLs
- [ ] Verify error messages are helpful
- [ ] Test API endpoints until success

