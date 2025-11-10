# Fix Airflow Log URL Configuration

## Problem

Airflow is generating invalid log URLs with missing host:
```
Invalid URL 'http://:8793/log/dag_id=ibkr_trading_signal_workflow/run_id=manual__2025-11-09T09:42:59.902663+00:00/task_id=fetch_market_data/attempt=1.log': No host supplied
```

The URL is missing the host part - it's `http://:8793/...` instead of `http://localhost:8793/...` or similar.

## Root Cause

Airflow needs to be configured with the correct base URL for the webserver so it can construct proper log URLs. The `AIRFLOW__WEBSERVER__BASE_URL` environment variable is not set, causing Airflow to generate URLs without a host.

## Solution

1. **Set Airflow Base URL**: Add `AIRFLOW__WEBSERVER__BASE_URL` environment variable to Airflow services in `docker-compose.yml`
2. **Configure Hostname**: Set `AIRFLOW__CORE__HOSTNAME_CALLABLE` to use proper hostname resolution
3. **Set Log Server URL**: Configure `AIRFLOW__LOGGING__BASE_LOG_FOLDER` and related log server settings

## Impact

- **Airflow**: Log URLs will be correctly generated with proper host
- **Frontend**: Log viewing will work correctly
- **No Breaking Changes**: This only fixes URL generation

## Implementation Notes

- Base URL should be set to `http://localhost:8080` for external access
- Hostname callable should use `socket:getfqdn` or similar
- Configuration should be added to both webserver and scheduler services

