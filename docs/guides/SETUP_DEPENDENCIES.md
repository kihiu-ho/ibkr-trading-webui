# Setup Dependencies Guide

**Purpose**: Set up required services for IBKR Trading WebUI

---

## Required Services

The application requires:
1. **PostgreSQL** - Database
2. **Redis** - Message broker for Celery

---

## Option 1: Using Docker (Recommended)

### Start Required Services

```bash
# Start PostgreSQL and Redis using Docker
docker run -d \
  --name ibkr-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ibkr_trading \
  -p 5432:5432 \
  postgres:15

docker run -d \
  --name ibkr-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### Stop Services

```bash
docker stop ibkr-postgres ibkr-redis
```

### Remove Services

```bash
docker rm ibkr-postgres ibkr-redis
```

---

## Option 2: Using Homebrew (macOS)

### Install PostgreSQL

```bash
# Install
brew install postgresql@15

# Start service
brew services start postgresql@15

# Create database
createdb ibkr_trading

# Optional: Set password
psql postgres -c "ALTER USER postgres PASSWORD 'postgres';"
```

### Install Redis

```bash
# Install
brew install redis

# Start service
brew services start redis

# Or run in foreground
redis-server
```

---

## Option 3: Using Docker Compose

Create `docker-compose.services.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ibkr_trading
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**Start**:
```bash
docker-compose -f docker-compose.services.yml up -d
```

**Stop**:
```bash
docker-compose -f docker-compose.services.yml down
```

---

## Configuration

### 1. Create .env File

```bash
cp .env.example .env
```

### 2. Update Database URL

Edit `.env` and set:

**For Python 3.13+**:
```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ibkr_trading
```

**For Python < 3.13**:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ibkr_trading
```

### 3. Update Redis URL

```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

---

## Verify Services

### Check PostgreSQL

```bash
# Test connection
psql -h localhost -U postgres -d ibkr_trading -c "SELECT 1"

# Or use Python
python3 -c "import psycopg; psycopg.connect('postgresql://postgres:postgres@localhost:5432/ibkr_trading')"
```

### Check Redis

```bash
# Test connection
redis-cli ping
# Should return: PONG

# Or check with Python
python3 -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
```

---

## Initialize Database

After services are running:

```bash
# Run database initialization
psql -h localhost -U postgres -d ibkr_trading -f database/init.sql
```

---

## Troubleshooting

### PostgreSQL Issues

**Port already in use**:
```bash
# Check what's using port 5432
lsof -i :5432

# Kill the process or use different port
docker run -p 5433:5432 ...
# Update DATABASE_URL port to 5433
```

**Permission denied**:
```bash
# Fix with Docker volume permissions
docker exec ibkr-postgres chmod 777 /var/lib/postgresql/data
```

### Redis Issues

**Port already in use**:
```bash
# Check what's using port 6379
lsof -i :6379

# Kill the process or use different port
docker run -p 6380:6379 ...
# Update REDIS_URL port to 6380
```

**Connection refused**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis
# or
docker start ibkr-redis
```

### Python Module Issues

**psycopg not found (Python 3.13)**:
```bash
pip install psycopg[binary]
```

**psycopg2 not found (Python < 3.13)**:
```bash
pip install psycopg2-binary
```

---

## Quick Start (All-in-One)

### Using Docker

```bash
# 1. Start services
docker run -d --name ibkr-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=ibkr_trading -p 5432:5432 postgres:15
docker run -d --name ibkr-redis -p 6379:6379 redis:7-alpine

# 2. Wait a moment for services to start
sleep 5

# 3. Initialize database
psql -h localhost -U postgres -d ibkr_trading -f database/init.sql

# 4. Create .env file
cp .env.example .env

# 5. Start the webapp
./start-webapp.sh
```

### Using Homebrew

```bash
# 1. Install and start services
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis

# 2. Create database
createdb ibkr_trading

# 3. Initialize database
psql ibkr_trading -f database/init.sql

# 4. Create .env file
cp .env.example .env
# Edit .env to remove password: postgresql+psycopg://postgres@localhost:5432/ibkr_trading

# 5. Start the webapp
./start-webapp.sh
```

---

## Summary

**Minimum Requirements**:
- ✅ PostgreSQL 12+ running on port 5432
- ✅ Redis 6+ running on port 6379
- ✅ Database `ibkr_trading` created
- ✅ `.env` file configured

**Then**:
```bash
./start-webapp.sh
```

---

**Need help?** Check the troubleshooting section above or create a GitHub issue.

