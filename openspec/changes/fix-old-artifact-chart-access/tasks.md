# Tasks: Fix Old Artifact Chart Access

## 1. Improve File Search Logic
- [x] Update `chart_images.py` to search for files by filename pattern
- [x] Search for files matching symbol and timeframe
- [x] Handle cases where exact file doesn't exist
- [x] Map chart_type to timeframe code (daily -> 1D, weekly -> 1W)

## 2. Handle Missing Files Gracefully
- [x] Return helpful error messages for old artifacts
- [x] Document that old artifacts may not have accessible files
- [x] Add logging for missing file scenarios

## 3. Verify Database Storage
- [x] Verify artifacts are stored in PostgreSQL database
- [x] Verify database connection is configured correctly
- [x] Test artifact retrieval from database

## 4. Testing
- [x] Test with old artifacts (ID 5, etc.)
- [x] Verify error messages are helpful
- [x] Verify artifacts are stored in PostgreSQL database

## Summary

✅ **File Search**: Improved to search by filename pattern when exact file doesn't exist
✅ **Error Messages**: Added helpful error messages explaining old artifacts
✅ **Database Storage**: Verified artifacts are stored in PostgreSQL (5 chart artifacts found)
✅ **Pattern Matching**: Maps chart_type (daily/weekly) to timeframe code (1D/1W)

**Note**: Old artifacts (ID 5, etc.) reference files in `/tmp/` that no longer exist. These artifacts are stored in PostgreSQL but the files are gone. New artifacts will work correctly with files in `/app/charts` and MinIO URLs.
