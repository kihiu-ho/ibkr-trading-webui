# Fix Old Artifact Chart Access

## Problem

Old artifacts (created before the fix) have `image_path` pointing to `/tmp/` files that no longer exist:
- Artifacts have `image_path` like `/tmp/NVDA_1W_20251109_050013.png`
- Files were saved to `/tmp/` which is ephemeral and files are deleted
- These artifacts don't have `chart_data.minio_url` set
- The endpoint tries to find files but they don't exist in any location

## Root Cause

1. **Old artifacts**: Created before shared volume and MinIO upload were implemented
2. **Missing files**: Files in `/tmp/` were deleted or never persisted
3. **No MinIO URLs**: Old artifacts don't have `chart_data.minio_url` set
4. **File search logic**: Endpoint searches for exact filename but files might have different names

## Solution

1. **Improve file search**: Search for files by filename pattern (symbol + timeframe) instead of exact path
2. **Handle missing files gracefully**: Return a helpful error message for old artifacts without files
3. **Update artifact metadata**: Optionally update old artifacts to reference available files
4. **Prioritize MinIO URLs**: Ensure new artifacts always have `chart_data.minio_url` set

## Impact

- **Backend**: Better handling of old artifacts without files
- **Frontend**: Clearer error messages for missing charts
- **No Breaking Changes**: Existing functionality preserved

## Implementation Notes

- Search for files by filename pattern (symbol_timeframe_*.png)
- Return descriptive error messages for missing files
- Document that old artifacts may not have accessible files

