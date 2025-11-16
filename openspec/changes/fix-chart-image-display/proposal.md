# Chart Image Display Fix

## Status
✅ **COMPLETE** - Backend MinIO authentication implemented, tested, and verified

## Problem Statement

Chart images stored in MinIO were not displaying in the frontend due to authentication requirements. The artifact data showed:
- `image_path`: "http://localhost:9000/trading-charts/charts/TSLA/daily/20251115_051322_1ebbc0f4.jpeg"
- `chart_data.minio_url`: Same MinIO URL
- `chart_data.local_path`: "/app/charts/TSLA_1D_20251115_051313.jpeg"

Direct browser access to MinIO URLs returned **403 Forbidden** because MinIO requires authenticated requests.

## Root Cause

1. **MinIO Authentication**: MinIO bucket `trading-charts` requires authenticated access
2. **Browser Limitations**: Browsers cannot add MinIO authentication headers to `<img>` tags
3. **Previous Implementation**: Backend tried to use plain HTTP requests without MinIO SDK authentication

## Solution Implemented

### Backend Proxy with MinIO SDK Authentication

Implemented authenticated MinIO proxy in `backend/api/chart_images.py`:

**Key Features:**
1. **MinIO Client Setup** (lines 18-30):
   ```python
   from minio import Minio
   minio_client = Minio(
       settings.MINIO_ENDPOINT,
       access_key=settings.MINIO_ACCESS_KEY,
       secret_key=settings.MINIO_SECRET_KEY,
       secure=settings.MINIO_SECURE
   )
   ```

2. **URL Parsing & Authentication** (lines 48-85):
   - Parse MinIO URL to extract bucket name and object path
   - Use `minio_client.get_object(bucket_name, object_name)` with credentials
   - Stream image data with proper content-type headers
   - Add cache headers (3600s) for performance

3. **Local File Fallback** (lines 86-178):
   - Search multiple common paths if MinIO fails
   - Check shared volume `/app/charts` (primary location)
   - Fall back to Airflow paths and temp directories

4. **Endpoint**: `/api/artifacts/{artifact_id}/image`
   - Accepts artifact ID
   - Queries database for image_path and chart_data
   - Prioritizes `chart_data.minio_url` over `image_path`
   - Returns image as `Response` with proper MIME type

### Frontend Integration

Frontend already properly configured in `artifact_detail.html`:
- Uses proxy endpoint: `<img :src="'/api/artifacts/' + artifact.id + '/image'" />`
- Shows loading spinner during fetch
- Error handling with retry button
- Displays both MinIO URL and local path for debugging
- "Open in new tab" link for testing

## Implementation Timeline

### Completed Steps

1. ✅ **MinIO SDK Integration** (Nov 15, 2025)
   - Added MinIO client initialization with authentication
   - Replaced HTTP requests with `minio_client.get_object()`
   
2. ✅ **URL Parsing** (Nov 15, 2025)
   - Extract bucket name and object path from URLs
   - Handle both `localhost:9000` and `minio:9000` endpoints
   
3. ✅ **Syntax Fixes** (Nov 15, 2025)
   - Fixed 4 syntax errors during implementation:
     - Indentation error (duplicate line)
     - SyntaxError (except statement placement)
     - ModuleNotFoundError (import path)
     - Final import path correction
   
4. ✅ **Backend Restart** (Nov 15, 2025)
   - Restarted backend 4 times to apply all fixes
   - Final status: Backend healthy and serving images

5. ✅ **Verification** (Nov 15, 2025)
   - Tested with artifact ID 7 (TSLA Daily Chart)
   - Confirmed JPEG image successfully served (312 KB)
   - Verified HTTP headers (200 OK, proper content-type, cache headers)

## Testing Results

### Backend Endpoint Test
```bash
curl -s http://localhost:8000/api/artifacts/7/image -o /tmp/test_chart_7.jpg
file /tmp/test_chart_7.jpg
```

**Result:**
```
/tmp/test_chart_7.jpg: JPEG image data, JFIF standard 1.01, 
    aspect ratio, density 1x1, baseline, precision 8, 
    1920x1080, components 3
-rw-r--r-- 1 he wheel 312K Nov 15 16:58 /tmp/test_chart_7.jpg
```

### HTTP Headers
```
HTTP/1.1 200 OK
content-disposition: inline; filename="chart-7.jpeg"
cache-control: public, max-age=3600
content-length: 319645
content-type: image/jpeg
```

### Artifact Data Verification
```json
{
  "id": 7,
  "name": "TSLA Daily Chart",
  "type": "chart",
  "symbol": "TSLA",
  "image_path": "http://localhost:9000/trading-charts/charts/TSLA/daily/20251115_051322_1ebbc0f4.jpeg",
  "chart_type": "daily",
  "chart_data": {
    "indicators": ["SMA_20", "SMA_50", "SMA_200", "Bollinger_Bands", 
                   "SuperTrend", "MACD", "RSI", "OBV", "ATR", "Volume"],
    "timeframe": "daily",
    "bars_count": 200,
    "minio_url": "http://localhost:9000/trading-charts/charts/TSLA/daily/20251115_051322_1ebbc0f4.jpeg",
    "local_path": "/app/charts/TSLA_1D_20251115_051313.jpeg"
  }
}
```

## Technical Details

### MinIO Authentication Flow

1. **Frontend Request**: Browser loads `<img src="/api/artifacts/7/image" />`
2. **Backend Receives**: FastAPI endpoint gets artifact ID
3. **Database Query**: Fetch artifact metadata including MinIO URL
4. **URL Parsing**: Extract bucket (`trading-charts`) and object path
5. **MinIO Authentication**: Use SDK client with access key/secret key
6. **Stream Response**: Return image bytes with proper headers
7. **Browser Display**: Image renders in frontend

### Configuration Requirements

**Environment Variables** (already configured):
```bash
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<configured>
MINIO_SECRET_KEY=<configured>
MINIO_SECURE=false
```

**Python Dependencies** (already installed):
- `minio>=7.0.0` (MinIO Python SDK)
- `fastapi`
- `sqlalchemy`

### Security Considerations

1. **Authentication**: MinIO credentials only stored in backend environment
2. **Authorization**: Backend validates artifact ownership before serving
3. **Cache Headers**: 1-hour cache reduces MinIO load
4. **Error Handling**: Generic error messages to avoid information disclosure

## Benefits

1. **Security**: Images protected behind MinIO authentication
2. **Performance**: Caching reduces repeated MinIO requests
3. **Reliability**: Fallback to local files if MinIO unavailable
4. **Debugging**: Frontend shows both MinIO URL and local path
5. **User Experience**: Seamless image display with loading states

## Known Issues & Future Improvements

### Current Limitations
- HEAD requests return 405 (FastAPI default for GET-only endpoints)
- No image thumbnail generation for list views
- No image optimization/resizing

### Future Enhancements
1. Add HEAD method support for better browser preflight
2. Generate thumbnails for artifacts list view
3. Implement progressive image loading
4. Add WebP format support for better compression
5. Cache images in Redis for faster repeated access

## Related Files

### Modified Files
- `backend/api/chart_images.py` - MinIO authentication implementation

### Dependencies
- `backend/config/settings.py` - MinIO configuration settings
- `backend/models/artifact.py` - Artifact database model
- `frontend/templates/artifact_detail.html` - Image display UI

### Test Files
- `openspec/changes/fix-chart-image-display/test-results.md` - Verification tests

## Rollback Procedure

If issues occur, revert to plain HTTP proxy:
1. Remove MinIO SDK import
2. Restore `requests.get()` implementation
3. Restart backend

**Note**: This will break chart display if MinIO requires authentication.

## References

- Original Issue: Chart images showing 403 Forbidden
- MinIO Python SDK: https://min.io/docs/minio/linux/developers/python/minio-py.html
- FastAPI Response Docs: https://fastapi.tiangolo.com/advanced/custom-response/
