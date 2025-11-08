# Quick Start Guide - Airflow & MLflow Monitoring

## Overview

This guide will help you start using the new Airflow and MLflow monitoring interfaces.

## Prerequisites

Ensure all services are running:
```bash
docker compose up -d
```

## Accessing the Monitoring Interfaces

### 1. Airflow Monitor

**URL**: http://localhost:8000/airflow

**Features**:
- View all DAGs and their status (Active/Paused)
- See last run time and next scheduled run
- Trigger workflows with one click
- Monitor recent DAG runs in real-time
- View detailed task instances for each run
- Auto-refreshes every 30 seconds

**Navigation**: 
- From any page, click "Airflow Monitor" in the left sidebar (System section)

### 2. MLflow Experiments

**URL**: http://localhost:8000/mlflow

**Features**:
- Browse all MLflow experiments
- View run history for each experiment
- See parameters, metrics, and tags for each run
- Compare runs across experiments
- Check run status and execution time

**Navigation**:
- From any page, click "MLflow Tracking" in the left sidebar (System section)

## Common Workflows

### Trigger an Airflow DAG

1. Go to http://localhost:8000/airflow
2. Find the DAG you want to run (e.g., `ibkr_stock_data_workflow`)
3. Click the "Trigger" button
4. Scroll down to the "Recent Workflow Runs" table to see your run

### Monitor DAG Execution

1. In the "Recent Workflow Runs" table, find your run
2. Click the eye icon (👁️) in the Actions column
3. A modal will show:
   - DAG run status
   - All task instances
   - Each task's state and duration

### View MLflow Experiments

1. Go to http://localhost:8000/mlflow
2. Click on any experiment to see its runs
3. Click "Details" on any run to see:
   - Parameters used
   - Metrics logged
   - Tags and metadata
   - Artifacts (if any)

## Testing the Integration

### Test Airflow Connection

```bash
# Check if Airflow is running
curl http://localhost:8080/health

# Or check via the monitoring page
curl http://localhost:8000/api/airflow/health
```

### Test MLflow Connection

```bash
# Check if MLflow is running
curl http://localhost:5500/health

# Or check via the monitoring page
curl http://localhost:8000/api/mlflow/health
```

### Run a Test Workflow

```bash
# Trigger the IBKR workflow via CLI
docker compose exec airflow-scheduler airflow dags trigger ibkr_stock_data_workflow

# Then monitor it at http://localhost:8000/airflow
```

## API Endpoints

All monitoring is powered by proxy APIs:

### Airflow API Proxy

Base URL: http://localhost:8000/api/airflow

- `GET /dags` - List all DAGs
- `GET /dags/{dag_id}` - Get DAG details  
- `GET /dags/{dag_id}/dagRuns` - Get DAG runs
- `POST /dags/{dag_id}/dagRuns` - Trigger DAG
- `GET /dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances` - Get task details
- `GET /health` - Health check

### MLflow API Proxy

Base URL: http://localhost:8000/api/mlflow

- `GET /experiments/list` - List all experiments
- `GET /experiments/{experiment_id}` - Get experiment
- `POST /runs/search` - Search runs
- `GET /runs/{run_id}` - Get run details
- `GET /runs/{run_id}/artifacts` - List artifacts
- `GET /health` - Health check

## Troubleshooting

### Airflow Monitor Shows "Disconnected"

1. Check if Airflow is running:
   ```bash
   docker compose ps airflow-webserver airflow-scheduler
   ```

2. Restart Airflow if needed:
   ```bash
   docker compose restart airflow-webserver airflow-scheduler
   ```

3. Check Airflow logs:
   ```bash
   docker compose logs airflow-scheduler --tail 50
   ```

### MLflow Shows "Disconnected"

1. Check if MLflow is running:
   ```bash
   docker compose ps mlflow-server
   ```

2. Restart MLflow:
   ```bash
   docker compose restart mlflow-server
   ```

3. Check MLflow logs:
   ```bash
   docker compose logs mlflow-server --tail 50
   ```

### Workflow Stuck in "Queued"

This can happen if:
- Airflow scheduler is not running
- Executor has no available slots
- Previous DAG runs are blocking

**Solutions**:
1. Check scheduler:
   ```bash
   docker compose logs airflow-scheduler --tail 100
   ```

2. Clear old DAG runs:
   ```bash
   docker compose exec airflow-scheduler airflow dags clear ibkr_stock_data_workflow -y
   ```

3. Restart scheduler:
   ```bash
   docker compose restart airflow-scheduler
   ```

### Can't Access Backend on Port 8000

1. Check if backend is running:
   ```bash
   docker compose ps backend
   ```

2. Check backend logs:
   ```bash
   docker compose logs backend --tail 50
   ```

3. Restart backend:
   ```bash
   docker compose restart backend
   ```

## Advanced Usage

### Custom Time Ranges

Add URL parameters to filter data:
```
# Last 24 hours of runs
http://localhost:8000/airflow?hours=24

# Specific date range  
http://localhost:8000/mlflow?start_date=2025-11-01&end_date=2025-11-08
```

### Keyboard Shortcuts

- `R` - Refresh data manually
- `ESC` - Close modal dialogs
- `/` - Focus search box (if available)

## Next Steps

1. **Explore the Dashboard**: Visit http://localhost:8000 for the main dashboard
2. **View Workflows**: Go to http://localhost:8000/workflows for detailed workflow management
3. **Check Signals**: Visit http://localhost:8000/signals for trading signal analysis
4. **Monitor Orders**: Check http://localhost:8000/orders for order management

## Support

For issues or questions:
1. Check logs: `docker compose logs [service-name]`
2. Review documentation in `/docs/`
3. Check OpenSpec changes in `/openspec/changes/`

## Related Documentation

- **Implementation Details**: `openspec/changes/cleanup-redundant-components/IMPLEMENTATION_COMPLETE.md`
- **Session Summary**: `docs/SESSION_SUMMARY_2025-11-08.md`
- **Project Structure**: `AGENTS.md`
- **Main README**: `README.md`

---

**Last Updated**: November 8, 2025  
**Version**: 1.0

