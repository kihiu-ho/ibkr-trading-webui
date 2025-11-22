# Interactive Brokers Web API

## Video Walkthrough

https://www.youtube.com/watch?v=CRsH9TKveLo

## Requirements

* Docker Desktop - https://www.docker.com/products/docker-desktop/
* External PostgreSQL Database (Neon, AWS RDS, etc.) - See [Database Setup Guide](docs/guides/DATABASE_SETUP_AIRFLOW_MLFLOW.md)

## Quick Start

### 1. Clone the source code
```bash
git clone https://github.com/hackingthemarkets/interactive-brokers-web-api.git
cd interactive-brokers-web-api
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp env.example .env

# Edit .env and set your DATABASE_URL (REQUIRED)
# See docs/guides/DATABASE_SETUP_AIRFLOW_MLFLOW.md for detailed instructions
nano .env  # or use your preferred editor
```

**Important**: You MUST set a valid `DATABASE_URL` in your `.env` file before starting the application.

Example:
```env
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname?sslmode=require
OPENAI_API_BASE=https://api.openai.com/v1  # or https://turingai.plus/v1 for TuringAI
OPENAI_API_KEY=your_key_here
IBKR_ACCOUNT_ID=DU1234567
```

See [OpenAI API Configuration Guide](docs/implementation/OPENAI_API_CONFIGURATION.md) for using TuringAI or other OpenAI-compatible providers.

### 3. Bring up the container
```
docker-compose up
```

## Getting a command line prompt

```
docker exec -it ibkr bash
```

## Common Commands

### Environment Variables
```bash
# Reload environment after .env changes
./reload-env.sh

# Verify environment variables in container
docker-compose exec backend printenv DATABASE_URL
```

### Service Management
```bash
# Start services (fast mode, no rebuild)
./start-webapp.sh

# Rebuild images after requirements.txt changes
./start-webapp.sh --rebuild

# Quick restart without health checks
./start-webapp.sh --fast

# Stop all services
docker-compose down
```

### Strategy Scheduling
The `/schedules` page (Workflow Schedules) lets you bind IBKR strategies to cron expressions without redeploying:

1. Click **New Schedule**, enter the strategy ID, workflow ID, cron string, timezone, and description.
2. Save to create a dedicated Airflow DAG (`strategy_<id>_schedule`) that triggers the main `ibkr_trading_strategy` DAG.
3. Toggle **Enable** to pause/resume; changes propagate to Airflow via the REST API in ~60 seconds.
4. Use **Run** for ad-hoc executions. This calls `POST /api/workflows/{workflow_id}/run-now` so you can test changes immediately.

API equivalents:

```bash
# Create a schedule (9:30 AM ET on weekdays)
curl -X POST http://localhost:8000/api/workflows/1/schedule \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 42, "cron_expression": "30 9 * * 1-5", "timezone": "America/New_York"}'

# Pause a schedule
curl -X PUT http://localhost:8000/api/schedules/5 -H "Content-Type: application/json" -d '{"enabled": false}'
```

Tips:
- Use exchange-aware cron expressions (e.g., `0 9 * * 1-5` for NYSE open). 
- Default timezone is `America/New_York`, but you can switch to `UTC`, `America/Los_Angeles`, etc.
- Disable schedules before lengthy maintenance windows; Airflow DAGs are paused but preserved.
- Airflow credentials for backend syncing are configurable (`AIRFLOW_API_URL`, `AIRFLOW_USERNAME`, `AIRFLOW_PASSWORD`).

### Health Checks
```bash
# Check all services status
docker-compose ps

# Backend health
curl http://localhost:8000/health

# View logs
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### Troubleshooting
See [TROUBLESHOOTING.md](docs/guides/TROUBLESHOOTING.md) for detailed solutions to common issues, including:
- Environment variable reloading (Issue 11)
- Database connection issues
- Service startup failures
- And more...
