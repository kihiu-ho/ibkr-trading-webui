# Fix Chart Image API Endpoint

## Problem

Chart image API endpoint `/api/artifacts/{id}/image` was returning 404 errors for old artifacts:
- Old artifacts have `image_path` pointing to `/tmp/` files that no longer exist
- Files were saved to ephemeral `/tmp/` directory and deleted
- Endpoint couldn't find files even when they exist in `/app/charts` with different names
- Error messages were not helpful for debugging

## Root Cause

1. **Old artifacts**: Created before shared volume and MinIO upload were implemented
2. **Missing files**: Files in `/tmp/` were deleted or never persisted
3. **No pattern matching**: Endpoint only searched for exact filename matches
4. **Poor error messages**: Generic 404 errors didn't explain the issue

## Solution

1. **Pattern matching**: Search for files by symbol and timeframe pattern when exact file doesn't exist
2. **Better error messages**: Return helpful error messages explaining old artifacts
3. **MinIO URL priority**: Check `chart_data.minio_url` first before searching local files
4. **Filename mapping**: Map `chart_type` (daily/weekly) to timeframe code (1D/1W) for pattern matching

## Impact

- **Backend**: Better handling of old artifacts without files
- **Frontend**: Clearer error messages for missing charts
- **API**: More robust file search logic
- **No Breaking Changes**: Existing functionality preserved

## Implementation Notes

- Search for files by filename pattern: `{symbol}_{timeframe_code}_*.png`
- Map chart_type to timeframe code: `daily` → `1D`, `weekly` → `1W`
- Return descriptive error messages for missing files
- Prioritize MinIO URLs from `chart_data.minio_url`

