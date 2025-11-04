# IBKR Stock Data Workflow Guide

## Overview

This guide explains how to use the IBKR stock data workflow built with Airflow and MLflow.

## What It Does

The workflow:
1. **Extracts** stock data (TSLA, NVDA) from PostgreSQL database
2. **Validates** data quality (required columns, null checks, price validity)
3. **Transforms** data (calculate returns, price ranges, derived metrics)
4. **Tracks** all runs in MLflow with comprehensive metadata

## Prerequisites

- Docker Compose services running (`./start-webapp.sh`)
- Sample stock data loaded in PostgreSQL
- Airflow UI accessible at http://localhost:8080
- MLflow UI accessible at http://localhost:5500

## Configuration

### Environment Variables

Set in `.env` file or docker-compose.yml:

```bash
# Debug mode - detailed logging and debug artifacts
DEBUG_MODE=true

# Stock symbols to fetch (comma-separated)
STOCK_SYMBOLS=TSLA,NVDA

# Environment identifier
ENVIRONMENT=development

# MLflow experiment name
MLFLOW_EXPERIMENT_NAME=ibkr-stock-data
```

### Database Connection

Automatic configuration from environment:
- Host: `postgres` (local Docker service)
- Port: `5432`
- Database: `postgres`
- User/Password: `postgres/postgres`

## Loading Sample Data

Run the sample data script:

```bash
docker compose exec -T postgres psql -U postgres -d postgres < scripts/create_sample_stock_data.sql
```

This creates:
- `stock_data` table
- Sample TSLA data (23 days)
- Sample NVDA data (23 days)

## Running the Workflow

### Via Airflow UI

1. Open http://localhost:8080
2. Login (airflow/airflow)
3. Find DAG `ibkr_stock_data_workflow`
4. Click **Unpause** (toggle switch)
5. Click **Trigger DAG** (play button)

### Via CLI

```bash
# Unpause the DAG
docker compose exec airflow-scheduler airflow dags unpause ibkr_stock_data_workflow

# Trigger manually
docker compose exec airflow-scheduler airflow dags trigger ibkr_stock_data_workflow

# Check status
docker compose exec airflow-scheduler airflow dags list-runs -d ibkr_stock_data_workflow
```

## Workflow Structure

```
extract_stock_data
    ↓
validate_data
    ↓
transform_data
    ↓
log_to_mlflow
```

### Task: extract_stock_data

- Fetches TSLA and NVDA data from PostgreSQL
- Checks symbol existence
- Logs missing symbols
- Returns extraction summary

### Task: validate_data

- Required columns check
- Null value validation
- Price validity (positive values)
- Volume validity (non-negative)

### Task: transform_data

- Calculate daily returns
- Calculate price ranges
- Add percentage metrics
- Sort by symbol and date

### Task: log_to_mlflow

- Log parameters (symbols, dates, config)
- Log metrics (row counts, validation status)
- Log artifacts (data samples, reports)
- Tag runs with metadata

## Debug Mode

When `DEBUG_MODE=true`:

- Detailed SQL queries logged
- Sample data from each step logged
- Comprehensive debug artifact in MLflow
- Full execution context captured

When `DEBUG_MODE=false`:

- INFO level logging only
- No debug artifacts
- Standard execution

## Viewing Results

### Airflow UI

1. Go to http://localhost:8080
2. Click on `ibkr_stock_data_workflow` DAG
3. View **Graph**, **Logs**, **XCom** tabs
4. Check task execution status

### MLflow UI

1. Go to http://localhost:5500
2. Select experiment `ibkr-stock-data`
3. View runs with:
   - **Parameters**: symbols, debug_mode, execution_date
   - **Metrics**: total_rows, symbols_processed, validation_checks
   - **Artifacts**: data samples, validation reports, debug info
   - **Tags**: workflow_type, environment, missing_symbols

## Monitoring

### Check DAG Status

```bash
docker compose exec airflow-scheduler airflow dags list
```

### Check Run Status

```bash
docker compose exec airflow-scheduler airflow dags list-runs -d ibkr_stock_data_workflow
```

### Check Task Logs

```bash
# Scheduler logs
docker logs ibkr-airflow-scheduler

# Webserver logs
docker logs ibkr-airflow-webserver
```

### Check Database Data

```bash
docker compose exec postgres psql -U postgres -d postgres -c "SELECT symbol, COUNT(*) FROM stock_data GROUP BY symbol;"
```

## Troubleshooting

### DAG Not Appearing

1. Check DAG file is mounted: `docker compose exec airflow-scheduler ls /opt/airflow/dags/`
2. Check for parsing errors: `docker logs ibkr-airflow-scheduler | grep ERROR`
3. Restart Airflow: `docker compose restart airflow-scheduler airflow-webserver`

### Task Failures

1. Check task logs in Airflow UI
2. Run task test: `docker compose exec airflow-scheduler airflow tasks test ibkr_stock_data_workflow extract_stock_data 2025-11-04`
3. Check database connectivity
4. Verify environment variables are set

### Database Connection Issues

1. Check PostgreSQL is running: `docker compose ps postgres`
2. Verify database has data: see "Check Database Data" above
3. Check connection string in environment

### MLflow Not Logging

1. Check MLflow is running: `docker compose ps mlflow-server`
2. Verify `MLFLOW_TRACKING_URI` is set correctly
3. Check MLflow logs: `docker logs ibkr-mlflow-server`

## Customization

### Adding More Symbols

1. Update `STOCK_SYMBOLS` environment variable: `STOCK_SYMBOLS=TSLA,NVDA,AAPL,MSFT`
2. Add data to PostgreSQL for new symbols
3. Restart Airflow services

### Changing Schedule

Edit `docker-compose.yml` or DAG file to set `schedule_interval`:

```python
# In ibkr_stock_data_workflow.py
schedule_interval='@daily',  # Run daily at midnight
# or
schedule_interval='0 9 * * *',  # Run at 9 AM every day
```

### Custom Transformations

Edit `transform_data` function in `dags/ibkr_stock_data_workflow.py`:

```python
def transform_data(**context):
    # Add your custom transformations
    df['custom_metric'] = df['close'] * df['volume']
    ...
```

## Architecture

### Components

1. **Airflow**: Workflow orchestration
   - Scheduler: Manages DAG execution
   - Webserver: UI for monitoring
   - Triggerer: Handles deferrable tasks

2. **PostgreSQL**: Data storage
   - Stock data table
   - Airflow metadata
   - MLflow tracking database

3. **MLflow**: Experiment tracking
   - Run tracking
   - Parameter/metric logging
   - Artifact storage (MinIO S3)

4. **MinIO**: S3-compatible artifact storage

### Data Flow

```
PostgreSQL (stock_data)
    ↓
Airflow DAG (extract → validate → transform)
    ↓
MLflow (track parameters, metrics, artifacts)
    ↓
MinIO (store artifacts)
```

## Next Steps

1. Add more stock symbols
2. Implement data enrichment (technical indicators, market data)
3. Add alerting for data quality issues
4. Schedule regular data updates
5. Create downstream ML models using tracked data
6. Integrate with IBKR Gateway for live data

## Related Documentation

- [OpenSpec Proposal](openspec/changes/add-ibkr-stock-data-workflow/proposal.md)
- [Technical Specification](openspec/changes/add-ibkr-stock-data-workflow/specs/data-pipeline/spec.md)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

