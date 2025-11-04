# Docker Compose Integration - Already Working!

## ✅ Docker Compose is Already Integrated

The `start-webapp.sh` script **already starts Docker Compose** automatically when Docker Desktop is running.

### Here's How It Works

**Line 117 of `start-webapp.sh`:**
```bash
$COMPOSE_CMD -f docker-compose.services.yml up -d 2>&1 | grep -v "is up-to-date" | grep -v "^$" || true
```

This line:
- ✅ Starts PostgreSQL container (`ibkr-postgres`)
- ✅ Starts Redis container (`ibkr-redis`)
- ✅ Creates networks and volumes
- ✅ Runs in detached mode (`-d`)

### Full Flow

```bash
./start-webapp.sh
```

**What happens**:

1. ✅ Checks if Docker is running
2. ✅ If Docker available → Runs `docker-compose up -d`
3. ✅ Waits for PostgreSQL to be healthy (pg_isready check)
4. ✅ Waits for Redis to be healthy (ping check)
5. ✅ Starts FastAPI backend
6. ✅ Starts Celery worker

### Verify Docker Compose is Started

After running `./start-webapp.sh`, check:

```bash
docker ps
```

You should see:
```
CONTAINER ID   IMAGE              STATUS                    PORTS                    NAMES
xxxxx          postgres:15-alpine Up 2 minutes (healthy)   0.0.0.0:5432->5432/tcp   ibkr-postgres
xxxxx          redis:7-alpine     Up 2 minutes (healthy)   0.0.0.0:6379->6379/tcp   ibkr-redis
```

### What You Need to Do

**Just start Docker Desktop, then run the script:**

```bash
# 1. Start Docker Desktop from Applications
open -a Docker

# 2. Wait for Docker to be ready (whale icon in menu bar)

# 3. Run the script - it does everything!
./start-webapp.sh
```

That's it! The script handles everything automatically.

### Script Output When Using Docker

```
==================================
IBKR Trading WebUI Startup
==================================

💡 Tip: For easiest setup, start Docker Desktop first!

✓ Python 3 found: Python 3.13.5
✓ Virtual environment activated
✓ Dependencies installed/updated
✓ Found .env file

Starting required services (PostgreSQL & Redis)...

✓ Docker is available
ℹ Starting PostgreSQL and Redis via Docker...
ℹ Waiting for services to be ready...
✓ PostgreSQL is ready
✓ Redis is ready

Starting webapp services...

✓ Backend started (PID: 12345)
✓ Celery worker started (PID: 12346)

==================================
✓ All services started successfully!
==================================

📦 Using Docker services:
  PostgreSQL:  Docker container (ibkr-postgres)
  Redis:       Docker container (ibkr-redis)

🌐 Access the application:
  Workflows:    http://localhost:8000/workflows  ⭐
```

### The Docker Compose File Being Used

**`docker-compose.services.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: ibkr-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ibkr_trading
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: ibkr-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
    name: ibkr_postgres_data
  redis_data:
    name: ibkr_redis_data
```

### Manual Docker Compose Commands (Optional)

If you want to manage Docker services manually:

```bash
# Start services only
docker-compose -f docker-compose.services.yml up -d

# Stop services
docker-compose -f docker-compose.services.yml down

# View logs
docker-compose -f docker-compose.services.yml logs -f

# Restart services
docker-compose -f docker-compose.services.yml restart

# Check status
docker-compose -f docker-compose.services.yml ps
```

### Troubleshooting

**If containers don't start:**

```bash
# Check Docker is running
docker ps

# Check container logs
docker logs ibkr-postgres
docker logs ibkr-redis

# Restart containers
docker-compose -f docker-compose.services.yml restart

# Complete reset
docker-compose -f docker-compose.services.yml down -v
./start-webapp.sh
```

### Summary

✅ **Docker Compose integration is complete and working**  
✅ **No additional steps needed**  
✅ **Just run `./start-webapp.sh`**

The script automatically:
- Detects Docker
- Starts containers via docker-compose
- Waits for health checks
- Starts the webapp

**You don't need to run docker-compose manually!**

