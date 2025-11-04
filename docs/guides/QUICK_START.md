# Quick Start Guide

## Single Command Startup

Start all services with one command:

```bash
docker compose up -d
```

This single command starts all services in the correct order:
1. **Core Infrastructure**: PostgreSQL, Redis, MinIO
2. **Airflow Init**: Database initialization (runs once)
3. **Application Services**: Backend, Gateway, Celery
4. **Workflow Services**: Airflow webserver/scheduler, MLflow

## Enhanced Startup Script

For a better experience with health checks and status monitoring:

```bash
./start-webapp.sh
```

### Options

- `./start-webapp.sh` - Normal startup with health checks
- `./start-webapp.sh --rebuild` - Force rebuild all images
- `./start-webapp.sh --fast` - Skip health checks for faster startup

## Service Startup Order

Docker Compose automatically handles dependencies:

```
postgres (core)
  ├─ redis (core)
  ├─ minio (core)
  ├─ airflow-init (runs once, then exits)
  │   └─ airflow-webserver (waits for init)
  │   └─ airflow-scheduler (waits for init)
  ├─ backend (waits for redis/minio)
  ├─ gateway (starts independently)
  ├─ celery-worker (waits for redis/backend)
  ├─ celery-beat (waits for redis)
  ├─ flower (waits for redis)
  ├─ mc (waits for minio)
  │   └─ mlflow-server (waits for mc)
```

## What's Running

After startup, you'll have:

### Core Services
- **PostgreSQL**: Local database (port 5432)
- **Redis**: Message broker (port 6379)
- **MinIO**: Object storage (ports 9000, 9001)

### Trading Services
- **Backend**: FastAPI server (port 8000)
- **Gateway**: IBKR Client Portal (port 5055)
- **Celery Worker**: Background tasks
- **Celery Beat**: Scheduled tasks
- **Flower**: Celery monitoring (port 5555)

### ML/Workflow Services
- **MLflow Server**: Experiment tracking (port 5500)
- **Airflow Webserver**: Workflow UI (port 8080)
- **Airflow Scheduler**: Workflow scheduler

## Access Points

- **Main App**: http://localhost:8000
- **Airflow UI**: http://localhost:8080
- **MLflow UI**: http://localhost:5500
- **Flower**: http://localhost:5555
- **MinIO Console**: http://localhost:9001
- **IBKR Gateway**: https://localhost:5055

## Stopping Services

```bash
docker compose down
```

Or use the stop script:
```bash
./stop-all.sh
```

## Database

PostgreSQL is now **local** (containerized):
- No external database URLs needed
- Airflow and MLflow use local PostgreSQL automatically
- Data persists in Docker volume `postgres_data`

## Troubleshooting

### Check Service Status
```bash
docker compose ps
```

### View Logs
```bash
docker compose logs -f [service-name]
```

### Restart a Service
```bash
docker compose restart [service-name]
```

### Rebuild After Changes
```bash
docker compose up -d --build
```

