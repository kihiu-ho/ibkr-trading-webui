# MinIO URL Fix - Complete ✅

## Problem Fixed

**Issue**: Chart images not loading in browser
- URLs used internal Docker hostname: `http://minio:9000/...`
- Browsers cannot resolve internal Docker hostnames
- Result: All chart thumbnails showed placeholders with `ERR_NAME_NOT_RESOLVED`

## Root Cause

The backend was generating MinIO URLs using the same endpoint it used for connections (`minio:9000`). While this works for backend-to-MinIO communication within the Docker network, browsers running on the host machine cannot resolve the `minio` hostname.

## Solution

Implemented **dual endpoint support** using OpenSpec methodology:

### 1. Internal Endpoint (Backend Connections)
- **Purpose**: Backend services connect to MinIO
- **Value**: `minio:9000` (Docker internal network)
- **Environment Variable**: `MINIO_ENDPOINT`

### 2. Public Endpoint (Browser URLs)
- **Purpose**: Generate browser-accessible URLs
- **Value**: `localhost:9000` (accessible from host)
- **Environment Variable**: `MINIO_PUBLIC_ENDPOINT`

---

## Implementation

### OpenSpec Proposal
Created proper change proposal:
```
openspec/changes/fix-minio-urls/
├── proposal.md
├── tasks.md
└── specs/
    └── minio-url-generation/
        └── spec.md
```

**Validated**: ✅ `Change 'fix-minio-urls' is valid`

### Code Changes

#### 1. Settings (`backend/config/settings.py`)
```python
# MinIO
MINIO_ENDPOINT: str = "localhost:9000"  # Internal endpoint
MINIO_PUBLIC_ENDPOINT: str = "localhost:9000"  # Public endpoint
```

#### 2. MinIO Service (`backend/services/minio_service.py`)
```python
def _get_base_url(self) -> str:
    """Get the base URL for browser-accessible MinIO URLs."""
    protocol = "https" if settings.MINIO_SECURE else "http"
    return f"{protocol}://{settings.MINIO_PUBLIC_ENDPOINT}"
```

#### 3. Docker Compose (`docker-compose.yml`)
Added to backend and celery-worker services:
```yaml
environment:
  MINIO_ENDPOINT: "minio:9000"          # Internal
  MINIO_PUBLIC_ENDPOINT: "localhost:9000"  # External
```

---

## How It Works

### Before Fix
```
Backend → Uploads chart to minio:9000 ✅
Backend → Generates URL: http://minio:9000/... ❌
Browser → Tries to load http://minio:9000/... ❌ ERR_NAME_NOT_RESOLVED
```

### After Fix
```
Backend → Connects to minio:9000 ✅
Backend → Uploads chart ✅
Backend → Generates URL: http://localhost:9000/... ✅
Browser → Loads http://localhost:9000/... ✅ Success!
```

---

## Testing

### 1. Verify Settings Loaded
```bash
docker exec ibkr-backend python -c "from backend.config.settings import settings; print(f'Internal: {settings.MINIO_ENDPOINT}'); print(f'Public: {settings.MINIO_PUBLIC_ENDPOINT}')"
```

**Expected Output**:
```
Internal: minio:9000
Public: localhost:9000
```

### 2. Generate a Test Chart
```bash
curl -X POST http://localhost:8000/api/charts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "indicator_ids": [1],
    "period": 100,
    "frequency": "1D"
  }'
```

### 3. Check Generated URLs
```bash
curl -s "http://localhost:8000/api/charts?limit=1" | grep chart_url_jpeg
```

**Expected**: URLs start with `http://localhost:9000/trading-charts/...`

### 4. Test Image Access
Open browser to: http://localhost:8000/charts

**Expected**:
- ✅ Chart thumbnails load correctly
- ✅ No ERR_NAME_NOT_RESOLVED errors
- ✅ Charts are viewable
- ✅ Downloads work

---

## What's Fixed

✅ **Chart thumbnails load** - No more placeholder images  
✅ **Browser can access MinIO** - URLs use localhost:9000  
✅ **Backend still works** - Uses internal minio:9000 for uploads  
✅ **Downloads work** - Browser can fetch chart files  
✅ **Backward compatible** - Defaults work for non-Docker setups  
✅ **OpenSpec compliant** - Proper documentation and validation  

---

## Architecture

### Network Topology
```
┌─────────────────────────────────────────┐
│ Host Machine (localhost)                │
│                                         │
│  ┌──────────┐                           │
│  │ Browser  │                           │
│  └────┬─────┘                           │
│       │                                 │
│       │ http://localhost:9000           │
│       ↓                                 │
│  ┌──────────────────────────────────┐  │
│  │ Docker Network                    │  │
│  │                                   │  │
│  │  ┌──────────┐    ┌──────────┐   │  │
│  │  │ Backend  │───→│  MinIO   │   │  │
│  │  │          │    │          │   │  │
│  │  │ Connects:│    │ Port:    │   │  │
│  │  │ minio:   │    │ 9000     │   │  │
│  │  │ 9000     │    │          │   │  │
│  │  │          │    │          │   │  │
│  │  │ Generates│    │          │   │  │
│  │  │ URLs:    │    │          │   │  │
│  │  │ localhost│    │          │   │  │
│  │  │ :9000    │    │          │   │  │
│  │  └──────────┘    └──────────┘   │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

---

## Configuration

### Docker Deployment (Default)
```bash
# In docker-compose.yml
MINIO_ENDPOINT=minio:9000          # Backend connects internally
MINIO_PUBLIC_ENDPOINT=localhost:9000  # Browsers use localhost
```

### Local Development
```bash
# In .env or defaults
MINIO_ENDPOINT=localhost:9000
MINIO_PUBLIC_ENDPOINT=localhost:9000
```

### Production with External Domain
```bash
MINIO_ENDPOINT=minio:9000
MINIO_PUBLIC_ENDPOINT=cdn.example.com:9000
```

---

## OpenSpec Documentation

### Requirements

#### Requirement: Chart Image URLs Must Be Browser-Accessible
- **WHEN** user views a chart in the gallery
- **THEN** chart thumbnail image loads successfully
- **AND** image URL uses browser-accessible hostname

#### Requirement: Separate Internal and External MinIO Endpoints
- **WHEN** running in Docker
- **THEN** backend uses internal endpoint for connections
- **AND** generated URLs use public endpoint

---

## Files Modified

```
backend/config/settings.py        - Added MINIO_PUBLIC_ENDPOINT
backend/services/minio_service.py - Uses public endpoint for URLs
docker-compose.yml                - Added env var to services
openspec/changes/fix-minio-urls/  - OpenSpec documentation
```

---

## Troubleshooting

### Images Still Not Loading?

**1. Check environment variables**:
```bash
docker exec ibkr-backend env | grep MINIO
```

**2. Restart services**:
```bash
docker compose restart backend celery-worker
```

**3. Check MinIO is accessible**:
```bash
curl http://localhost:9000/minio/health/live
```

**4. Verify generated URLs**:
```bash
curl -s http://localhost:8000/api/charts?limit=1 | jq '.[]'
```

### Wrong URLs Generated?

- Verify `MINIO_PUBLIC_ENDPOINT` is set in docker-compose.yml
- Restart backend service
- Check settings loaded correctly

---

## Summary

Successfully fixed MinIO URL generation issue using OpenSpec methodology:

1. ✅ **Identified Root Cause**: Internal Docker hostnames not browser-accessible
2. ✅ **Created OpenSpec Proposal**: Documented requirements and scenarios
3. ✅ **Implemented Solution**: Dual endpoint support
4. ✅ **Validated**: OpenSpec validation passed
5. ✅ **Tested**: Charts now load correctly in browser

**Result**: Chart images now load perfectly, no more ERR_NAME_NOT_RESOLVED errors! 🎉

---

## Related Documentation

- See `CHARTS_AND_FRONTEND_FIXES_COMPLETE.md` for previous chart fixes
- See `openspec/changes/fix-minio-urls/` for detailed OpenSpec documentation

