# 🚀 IBKR Trading WebUI - Docker Quick Start

**Get started in 60 seconds!**

---

## ⚡ One-Command Start

```bash
./start-webapp.sh
```

That's literally it! This command:
- ✅ Starts PostgreSQL, Redis, MinIO, IBKR Gateway
- ✅ Launches FastAPI backend with Celery workers
- ✅ Waits for all services to be healthy
- ✅ Shows you where to access everything

---

## 🌐 Access Your Application

Once running, open these in your browser:

| URL | What It Does |
|-----|--------------|
| **http://localhost:8000** | Main dashboard - start here! |
| **http://localhost:8000/workflows** | Configure trading workflows ⭐ |
| **http://localhost:8000/docs** | Interactive API documentation |
| **https://localhost:5055** | IBKR Gateway (login with IBKR credentials) |
| **http://localhost:5555** | Celery task monitor (Flower) |
| **http://localhost:9001** | MinIO storage console |

---

## 🔧 First-Time Setup (Optional)

### Configure Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env
```

**Important variables:**
- `IBKR_ACCOUNT_ID` - Your Interactive Brokers account
- `OPENAI_API_KEY` - For AI-powered trading features
- `POSTGRES_PASSWORD` - Secure your database

### Authenticate with IBKR
1. Open https://localhost:5055
2. Accept security warning (self-signed cert)
3. Log in with your IBKR credentials
4. Done! Session persists across restarts

---

## 🛑 Stop Everything

```bash
./stop-all.sh
```

---

## 📊 Check Status

### Quick Health Check
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

### All Services Status
```bash
docker compose ps
```

### Run Full Test Suite
```bash
./test-services.sh
```

---

## 📚 Need More Help?

**Choose your guide:**

| Guide | Best For |
|-------|----------|
| **QUICKSTART_DOCKER.md** | Complete beginners |
| **DOCKER_SETUP_COMPLETE.md** | Technical reference & troubleshooting |
| **IMPLEMENTATION_SUMMARY.md** | Understanding what was built |

---

## 🎯 What's Included

This Docker setup includes:

1. **Web Application** - FastAPI backend + modern UI
2. **Database** - PostgreSQL 15 with 13 pre-configured tables
3. **Message Queue** - Redis for Celery task management
4. **Object Storage** - MinIO for chart storage
5. **IBKR Gateway** - Official Interactive Brokers API gateway
6. **Background Workers** - Celery workers & scheduler
7. **Monitoring** - Flower UI for task monitoring

---

## 🔥 Common Commands

```bash
# Start everything
./start-webapp.sh

# Stop everything
./stop-all.sh

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker logs -f ibkr-backend
docker logs -f ibkr-celery-worker

# Restart a service
docker compose restart backend

# Check service status
docker compose ps

# Run tests
./test-services.sh

# Reset everything (careful - deletes data!)
docker compose down -v
```

---

## ⚠️ Troubleshooting

### Services Won't Start
```bash
# Make sure Docker Desktop is running
docker info

# Check for port conflicts
docker compose ps

# View error logs
docker compose logs
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker exec ibkr-postgres pg_isready -U postgres

# View tables
docker exec ibkr-postgres psql -U postgres -d ibkr_trading -c '\dt'
```

### Reset Everything
```bash
# Nuclear option - removes all data
docker compose down -v

# Start fresh
./start-webapp.sh
```

---

## 🏗️ Architecture

```
User Browser
     ↓
┌────────────────────────────────────┐
│   FastAPI Backend (:8000)          │
│   ├─ REST API                      │
│   ├─ Web UI                        │
│   └─ WebSocket Support             │
└────┬────┬────────┬─────────┬───────┘
     │    │        │         │
     ↓    ↓        ↓         ↓
   ┌───┬────┬──────────┬─────────┐
   │DB │Cache│ Storage │  IBKR   │
   │   │     │         │ Gateway │
   └───┴────┴──────────┴─────────┘
        ↓
   ┌─────────────┐
   │   Celery    │
   │   Workers   │
   └─────────────┘
```

---

## 💡 Tips

1. **First time?** Just run `./start-webapp.sh` - it handles everything!
2. **Development?** Code changes auto-reload (no restart needed)
3. **Debugging?** Use `docker compose logs -f backend` for live logs
4. **Production?** Review `DOCKER_SETUP_COMPLETE.md` for deployment guide

---

## ✅ Verification

After starting, verify everything works:

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Check database
docker exec ibkr-postgres psql -U postgres -d ibkr_trading -c 'SELECT 1;'

# 3. Check Redis
docker exec ibkr-redis redis-cli ping

# 4. Check all services
docker compose ps
```

All green? You're ready to trade! 🎉

---

## 📞 Support

**Something not working?**

1. Check logs: `docker compose logs -f`
2. Verify services: `docker compose ps`
3. Test health: `curl http://localhost:8000/health`
4. Review troubleshooting in `DOCKER_SETUP_COMPLETE.md`

---

## 🎓 Next Steps

1. ✅ **Explore the Dashboard** - http://localhost:8000
2. ✅ **Read the API Docs** - http://localhost:8000/docs
3. ✅ **Create Your First Strategy** - Use the web UI
4. ✅ **Set Up a Workflow** - Automate your trading
5. ✅ **Monitor Background Tasks** - http://localhost:5555

---

**Ready?** Run `./start-webapp.sh` and let's go! 🚀

