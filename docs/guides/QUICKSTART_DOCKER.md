# Quick Start Guide - Docker Edition 🚀

Get the IBKR Trading WebUI running in under 5 minutes!

## Prerequisites

- ✅ Docker Desktop installed and running
- ✅ 4GB+ RAM available
- ✅ 10GB+ disk space

## Start Everything (One Command)

```bash
./start-webapp.sh
```

That's it! The script will:
- ✅ Check Docker is ready
- ✅ Pull required images (if needed)
- ✅ Start all 8 services
- ✅ Wait for everything to be healthy
- ✅ Show you all access points

## Access Your Application

Once started, open your browser:

| What | Where | Why |
|------|-------|-----|
| **Main Dashboard** | http://localhost:8000 | Start here! |
| **Workflows** | http://localhost:8000/workflows | Set up trading workflows ⭐ |
| **API Docs** | http://localhost:8000/docs | Test API endpoints |
| **IBKR Gateway** | https://localhost:5055 | Log in with IBKR credentials |

## First Time Setup

### 1. Copy Environment File
```bash
cp .env.example .env
```

### 2. Edit Your Settings (Optional)
```bash
nano .env
```

Key settings:
- `IBKR_ACCOUNT_ID` - Your IBKR account (default: DU1234567 for demo)
- `OPENAI_API_KEY` - For AI trading features
- `POSTGRES_PASSWORD` - Database password (use strong password in production)

### 3. Authenticate IBKR Gateway
1. Open https://localhost:5055
2. Accept the security warning (self-signed cert)
3. Log in with your IBKR credentials
4. Done! The session persists

## Stop Everything

```bash
./stop-all.sh
```

## View Logs

```bash
# All services
docker compose logs -f

# Just the backend
docker logs -f ibkr-backend

# Just Celery worker
docker logs -f ibkr-celery-worker
```

## Check Health

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

Expected output:
```json
{
  "status": "healthy",
  "database": "connected",
  "ibkr": "not_authenticated"
}
```

## Common Issues

### Docker Desktop Not Running
**Solution:** Open Docker Desktop and wait for it to fully start (whale icon should be steady)

### Port Already in Use
**Solution:** Stop conflicting services or change ports in `docker-compose.yml`

### IBKR Gateway Not Starting
**Solution:** This is normal - it takes 60-90 seconds. Check logs:
```bash
docker logs ibkr-gateway --tail 50
```

### Reset Everything
If something goes wrong:
```bash
docker compose down -v  # Remove all data
./start-webapp.sh        # Start fresh
```

## What's Running?

```bash
docker compose ps
```

You should see:
- ✅ **backend** - Web application (Python/FastAPI)
- ✅ **postgres** - Database (PostgreSQL 15)
- ✅ **redis** - Message queue (Redis 7)
- ✅ **minio** - File storage (MinIO)
- ✅ **ibkr-gateway** - IBKR API connection
- ✅ **celery-worker** - Background tasks
- ✅ **celery-beat** - Task scheduler
- ✅ **flower** - Task monitoring UI

## Development Tips

### Restart a Service
```bash
docker compose restart backend
```

### Rebuild After Code Changes
```bash
docker compose up -d --build backend
```

### Enter a Container
```bash
docker exec -it ibkr-backend bash
```

### View Database Tables
```bash
docker exec ibkr-postgres psql -U postgres -d ibkr_trading -c '\dt'
```

### Test Redis
```bash
docker exec ibkr-redis redis-cli ping
# Should return: PONG
```

## Architecture Overview

```
┌─────────────────────────────────────┐
│  Browser                            │
│  http://localhost:8000              │
└──────────┬──────────────────────────┘
           │
           ↓
┌─────────────────────────────────────┐
│  FastAPI Backend                    │
│  • REST API                         │
│  • Web UI (Jinja2 templates)       │
│  • Celery task submission          │
└─┬────────────┬──────────────┬───────┘
  │            │              │
  ↓            ↓              ↓
┌────────┐  ┌─────┐  ┌──────────────┐
│Postgres│  │Redis│  │ IBKR Gateway │
└────────┘  └──┬──┘  └──────────────┘
               │
               ↓
         ┌──────────┐
         │ Celery   │
         │ Workers  │
         └──────────┘
```

## Next Steps

1. ✅ **Explore Dashboard** - http://localhost:8000
2. ✅ **Review API Docs** - http://localhost:8000/docs
3. ✅ **Create a Strategy** - Use the web UI
4. ✅ **Set Up Workflow** - Automate your trading
5. ✅ **Monitor Tasks** - http://localhost:5555 (Flower)

## Production Checklist

Before deploying to production:
- [ ] Set strong passwords in `.env`
- [ ] Use real SSL certificates
- [ ] Enable backups for PostgreSQL
- [ ] Set up monitoring/alerting
- [ ] Review security settings
- [ ] Test disaster recovery
- [ ] Configure log retention

## Need Help?

1. **Check logs**: `docker compose logs -f`
2. **Verify health**: `curl http://localhost:8000/health`
3. **Container status**: `docker compose ps`
4. **Restart services**: `./stop-all.sh && ./start-webapp.sh`

---

**Ready to trade?** Open http://localhost:8000 and start building your strategies! 📈

