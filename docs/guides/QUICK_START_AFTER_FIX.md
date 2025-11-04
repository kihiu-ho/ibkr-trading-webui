# Quick Start - After MinIO URL Fix ✅

## What Was Fixed

**Problem**: Chart images not loading in browser  
**Cause**: URLs used internal Docker hostname `minio:9000`  
**Solution**: URLs now use `localhost:9000` (browser-accessible)

---

## Start the System

```bash
# Start all services
docker compose up -d

# Wait 30 seconds for services to initialize
sleep 30

# Check status
docker ps
```

---

## Verify the Fix

### 1. Run Automated Tests
```bash
./test_all_fixes_v2.sh
```

**Expected output**: All tests pass with ✓ green checkmarks

### 2. Test Chart Generation
```bash
# Generate a test chart
curl -X POST http://localhost:8000/api/charts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "indicator_ids": [1, 2],
    "period": 100,
    "frequency": "1D"
  }'
```

**Look for**:
```json
{
  "chart_url_jpeg": "http://localhost:9000/trading-charts/...",
  "chart_url_html": "http://localhost:9000/trading-charts/..."
}
```

✅ URLs should start with `http://localhost:9000`  
❌ NOT `http://minio:9000`

### 3. Test Image Access
```bash
# Copy the JPEG URL from above command and test
curl -I "http://localhost:9000/trading-charts/charts/TSLA/..."
```

**Expected**: `HTTP/1.1 200 OK`

---

## Use the Frontend

### Open Charts Page
```
http://localhost:8000/charts
```

### What You Should See
✅ **Chart thumbnails load** (no placeholder images)  
✅ **No console errors** (check browser DevTools)  
✅ **Charts are clickable** (opens fullscreen viewer)  
✅ **Download works** (saves file to disk)  

### Generate New Chart
1. Click "Generate New Chart" button
2. Enter symbol (e.g., AAPL, TSLA, NVDA)
3. Select indicators (MA, RSI, MACD, etc.)
4. Click "Generate Chart"
5. Wait 5-10 seconds
6. New chart appears in gallery
7. **Thumbnail loads immediately** ← This is the fix!

---

## Browser Console Check

### Before Fix ❌
```
GET http://minio:9000/trading-charts/... net::ERR_NAME_NOT_RESOLVED
```

### After Fix ✅
```
GET http://localhost:9000/trading-charts/... 200 OK
```

---

## If Old Charts Have Wrong URLs

Old charts generated before this fix may still have `minio:9000` URLs.

### Option 1: Delete and Regenerate
```bash
# Delete all charts
curl -X DELETE http://localhost:8000/api/charts/{id}

# Or delete via frontend UI (trash icon)
```

### Option 2: Database Update (Advanced)
```bash
docker exec -it ibkr-postgres psql -U postgres -d ibkr_trading -c "
UPDATE charts 
SET 
  chart_url_jpeg = REPLACE(chart_url_jpeg, 'http://minio:9000', 'http://localhost:9000'),
  chart_url_html = REPLACE(chart_url_html, 'http://minio:9000', 'http://localhost:9000');
"
```

---

## Architecture

### Network Flow
```
Browser
  ↓
  │ Loads page: http://localhost:8000/charts
  │
  ↓
Backend API
  │ Returns chart list with localhost:9000 URLs ✅
  │
  ↓
Browser
  │ Loads image: http://localhost:9000/trading-charts/...
  │
  ↓
MinIO (port 9000)
  │ Serves image: 200 OK ✅
  │
  ↓
Browser displays chart thumbnail ✅
```

### Backend Internal Communication
```
Backend
  ↓
  │ Connects to: minio:9000 (internal Docker network)
  │
  ↓
MinIO
  │ Accepts upload ✅
  │
  ↓
Backend
  │ Generates URL: http://localhost:9000/... (public URL)
  │ Saves to database ✅
```

---

## Configuration

### Environment Variables (Already Set)
```yaml
# docker-compose.yml
backend:
  environment:
    MINIO_ENDPOINT: "minio:9000"           # Internal connection
    MINIO_PUBLIC_ENDPOINT: "localhost:9000" # Browser-accessible URLs
```

### Settings (Already Configured)
```python
# backend/config/settings.py
MINIO_ENDPOINT: str = "localhost:9000"
MINIO_PUBLIC_ENDPOINT: str = "localhost:9000"
```

---

## Troubleshooting

### Problem: Images Still Not Loading

**1. Check Docker logs**
```bash
docker logs ibkr-backend --tail 50
```

**2. Verify MinIO is accessible**
```bash
curl http://localhost:9000/minio/health/live
```
Should return: `HTTP/1.1 200 OK`

**3. Check bucket policy**
```bash
docker exec ibkr-minio mc anonymous get myminio/trading-charts
```
Should return: `Access permission for 'myminio/trading-charts' is 'download'`

**4. Set bucket public if needed**
```bash
docker exec ibkr-minio mc alias set myminio http://localhost:9000 minioadmin minioadmin
docker exec ibkr-minio mc anonymous set download myminio/trading-charts
```

**5. Restart backend**
```bash
docker compose restart backend
```

### Problem: Wrong URL Format

**Check generated URL**
```bash
curl http://localhost:8000/api/charts | jq '.[0].chart_url_jpeg'
```

**Should be**: `"http://localhost:9000/trading-charts/..."`  
**Not**: `"http://minio:9000/trading-charts/..."`

If wrong, check environment variables:
```bash
docker exec ibkr-backend env | grep MINIO
```

Should show:
```
MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=localhost:9000
```

---

## Success Indicators

✅ **Test script passes** - All green checkmarks  
✅ **New charts use localhost:9000** - URL format correct  
✅ **Images load in browser** - No ERR_NAME_NOT_RESOLVED  
✅ **Thumbnails visible** - Gallery shows chart previews  
✅ **Downloads work** - Can save charts locally  
✅ **No console errors** - Browser DevTools clean  

---

## What's Different Now?

### Before Fix
```javascript
// Generated URL
"http://minio:9000/trading-charts/charts/TSLA/chart.jpg"

// Browser tries to load
GET http://minio:9000/... ❌ ERR_NAME_NOT_RESOLVED

// Result
<img src="minio:9000/..." />  // Broken image
```

### After Fix
```javascript
// Generated URL
"http://localhost:9000/trading-charts/charts/TSLA/chart.jpg"

// Browser loads successfully
GET http://localhost:9000/... ✅ 200 OK

// Result
<img src="localhost:9000/..." />  // Image displays!
```

---

## Next Steps

1. ✅ **Generate charts** - Create some charts for different symbols
2. ✅ **View gallery** - See all charts with thumbnails
3. ✅ **Test interactivity** - Click charts to view fullscreen
4. ✅ **Download charts** - Save images to your computer
5. ✅ **Share links** - URLs work in any browser

---

## Production Deployment

For production with a public domain:

### 1. Use CDN/Public Domain
```yaml
# docker-compose.prod.yml
backend:
  environment:
    MINIO_ENDPOINT: "minio:9000"
    MINIO_PUBLIC_ENDPOINT: "cdn.example.com:9000"  # Your public domain
```

### 2. Setup Reverse Proxy
```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name cdn.example.com;
    
    location /trading-charts/ {
        proxy_pass http://minio:9000;
    }
}
```

### 3. Update Settings
```python
MINIO_PUBLIC_ENDPOINT: str = "cdn.example.com"
MINIO_SECURE: bool = True  # Use HTTPS
```

---

## Summary

**Problem Solved**: Chart images now load in browser! 🎉

- ✅ URLs use browser-accessible hostname
- ✅ Backend still connects via internal network
- ✅ Images are publicly readable
- ✅ Gallery works perfectly
- ✅ No more ERR_NAME_NOT_RESOLVED

**Try it**: http://localhost:8000/charts

All chart thumbnails should now load instantly with no errors!

