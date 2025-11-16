# Quick Fix Guide - IBKR Trading WebUI

## 🎉 All Issues Fixed!

This guide shows you how to use the newly fixed features.

---

## Issue 1: Chart Generation - ✅ FIXED

### What Was Wrong
```
Error: Mapped instance expected for relationship comparison to object
```

### What's Fixed
- ✅ SQLAlchemy query now works correctly
- ✅ Symbols automatically fetched from IBKR if not in database
- ✅ Market data retrieved and cached from IBKR
- ✅ Database schema updated

### How to Use
```bash
# Generate a chart
curl -X POST http://localhost:8000/api/charts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "indicator_ids": [1],
    "period": 100,
    "frequency": "1D"
  }'
```

The system will:
1. Look up AAPL symbol (or fetch from IBKR if not found)
2. Get historical data from IBKR
3. Cache the data for future use
4. Generate the chart

---

## Issue 2: IBKR Gateway Status - ✅ FIXED

### What Was Wrong
- Gateway always showed as "Offline"
- No error messages to help diagnose
- Confusing authentication state

### What's Fixed
- ✅ Detailed error messages
- ✅ Better connection detection
- ✅ Clear status indicators

### How to Check Status
```bash
# Check gateway status
curl http://localhost:8000/api/ibkr/auth/status
```

**Response when gateway is offline**:
```json
{
    "authenticated": false,
    "server_online": false,
    "server_error": "Cannot connect to IBKR Gateway. Is it running?",
    "gateway_url": "https://ibkr-gateway:5055/v1/api"
}
```

**Response when gateway is online**:
```json
{
    "authenticated": true,
    "server_online": true,
    "account_id": "DU1234567",
    "accounts": ["DU1234567"],
    "gateway_url": "https://ibkr-gateway:5055/v1/api"
}
```

---

## Issue 3: IBKR Login Page - ✅ FIXED

### What Was Wrong
- No clear way to access IBKR Gateway login
- Confusing authentication process
- No troubleshooting help

### What's Fixed
- ✅ Direct link to gateway web interface
- ✅ Step-by-step instructions
- ✅ Troubleshooting guide
- ✅ Error messages displayed clearly

### How to Use

#### Step 1: Open Login Page
Navigate to: **http://localhost:8000/ibkr/login**

#### Step 2: Start Gateway (if offline)
```bash
docker compose up ibkr-gateway -d
```

Wait 30-60 seconds for gateway to fully start.

#### Step 3: Initial Authentication
1. Click **"Open Gateway Login (Port 5055)"** button
2. Your browser will open: **https://localhost:5055**
3. Accept the SSL certificate warning (it's self-signed, this is normal)
4. Login with your IBKR credentials
5. Open IBKR Mobile app and approve the login (2FA)

#### Step 4: Verify Connection
1. Return to the login page
2. Click **"Refresh"** button
3. You should see:
   - 🟢 Gateway Server: **Online**
   - 🟢 Authentication: **Connected**
   - Account ID: **DU1234567** (your account)

---

## Database Migration Applied ✅

The `market_data` table schema has been updated:

```sql
-- Old schema (incompatible)
market_data (code VARCHAR, timeframe VARCHAR, date, open, high, low, close, volume)

-- New schema (current)
market_data (id, conid INTEGER, period VARCHAR, bar VARCHAR, data JSONB, created_at)
```

**Already applied!** No action needed from you.

---

## Quick Start (After Fixes)

### 1. Start All Services
```bash
docker compose up -d
```

### 2. Verify Gateway
```bash
# Check if gateway is running
docker ps | grep ibkr-gateway

# Check gateway logs
docker logs ibkr-gateway -f
```

### 3. Login to IBKR
Open browser: **http://localhost:8000/ibkr/login**

Click: **"Open Gateway Login"** → Login → Approve on mobile

### 4. Test Chart Generation
```bash
# Via API
curl -X POST http://localhost:8000/api/charts/generate \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","indicator_ids":[1],"period":100,"frequency":"1D"}'

# Or use the web interface
# Navigate to: http://localhost:8000/charts
```

---

## Troubleshooting

### Gateway Shows Offline

**Check 1: Is it running?**
```bash
docker ps | grep ibkr-gateway
```
If not listed, start it:
```bash
docker compose up ibkr-gateway -d
```

**Check 2: Check logs**
```bash
docker logs ibkr-gateway -f
```
Look for errors or authentication prompts.

**Check 3: Test connectivity**
```bash
curl -k https://localhost:5055/v1/api/tickle
```

### Chart Generation Fails

**Issue**: "Symbol not found"
- Make sure gateway is authenticated
- Try common symbols: AAPL, TSLA, MSFT

**Issue**: "No market data"
- The symbol will be fetched automatically on first use
- Subsequent requests will use cached data

**Issue**: "Kaleido/Chrome required"
- This means the Airflow image cannot import Kaleido/Chromium for Plotly exports.
- Run `./scripts/verify_kaleido.sh --service airflow-webserver` (or `--image ibkr-airflow:latest`) to confirm the dependency.
- If verification fails, rebuild the image and restart services:
  ```bash
  docker compose build airflow-webserver airflow-scheduler
  ./scripts/verify_kaleido.sh --image ibkr-airflow:latest
  docker compose up -d airflow-webserver airflow-scheduler
  ```
- When running workflows outside Docker, install Kaleido locally: `pip install kaleido==0.2.1`

### Cannot Access Login Page

**Check**: Is backend running?
```bash
docker ps | grep ibkr-backend
docker logs ibkr-backend -f
```

**Restart**: If needed
```bash
docker compose restart backend
```

---

## What Changed

### Files Modified
```
backend/api/charts.py              ← Fixed SQLAlchemy query
backend/api/ibkr_auth.py           ← Enhanced status checking
frontend/templates/ibkr_login.html ← Added gateway access UI
database/migrate_market_data.sql   ← Database schema fix
```

### New Features
- ✅ Automatic symbol lookup from IBKR
- ✅ Automatic market data fetching
- ✅ Data caching for performance
- ✅ Detailed error messages
- ✅ Direct gateway access button
- ✅ Comprehensive troubleshooting guide

---

## Testing Your Installation

Run the automated test:
```bash
./test_all_fixes.sh
```

This will check:
- Backend health
- Authentication status
- Gateway connectivity
- Frontend pages
- Docker services

---

## Summary

All three issues are now **completely fixed**:

1. ✅ **Chart Generation**: SQLAlchemy error resolved, automatic IBKR data fetching
2. ✅ **Gateway Status**: Clear error messages, better detection
3. ✅ **Login Page**: Direct gateway access, step-by-step guide

You can now:
- Generate charts with any symbol
- See clear gateway connection status
- Easily authenticate with IBKR Gateway
- Get helpful error messages when things go wrong

---

## Need Help?

Check the logs:
```bash
# Backend logs
docker logs ibkr-backend -f

# Gateway logs
docker logs ibkr-gateway -f

# All services
docker compose logs -f
```

Visit the IBKR Login page for diagnostic information:
**http://localhost:8000/ibkr/login**

Happy Trading! 📈
