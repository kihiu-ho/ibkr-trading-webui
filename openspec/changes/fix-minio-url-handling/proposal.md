# Fix MinIO URL Handling in Chart Images Endpoint

## Problem

Chart images stored in MinIO are not being displayed because:
1. Artifacts have `image_path` set to local paths (e.g., `/tmp/TSLA_1W_20251109_050013.png`) instead of MinIO URLs
2. `chart_data` may contain `minio_url` but the endpoint doesn't check it
3. The endpoint only checks if `image_path` starts with 'http', missing MinIO URLs stored in `chart_data`

## Root Cause

When charts are uploaded to MinIO:
- The `minio_url` is stored in `chart_data.minio_url`
- But `image_path` is still set to the local path
- The endpoint doesn't check `chart_data.minio_url` as a fallback

## Solution

1. **Update chart_images.py**: Check `chart_data.minio_url` if `image_path` is a local path
2. **Prioritize MinIO URLs**: Use MinIO URL from `chart_data` if available, even if `image_path` is local
3. **Fallback chain**: Check MinIO URL first, then local file paths

## Impact

- **Backend**: Chart images endpoint will correctly use MinIO URLs
- **Frontend**: Charts will display correctly from MinIO
- **No Breaking Changes**: Existing local paths will still work as fallback

## Implementation Notes

- Check `chart_data.minio_url` before trying local file paths
- Use MinIO URL if available, regardless of `image_path` value
- Maintain backward compatibility with local paths

