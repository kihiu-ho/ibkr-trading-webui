## Why
The Airflow monitor fetches `/api/airflow/dags/<dag_id>/dagRuns?limit=5&order_by=-start_date` to show recent runs. When Airflow rejects the request (e.g., DAG missing, invalid filter, scheduler down), it often returns an HTML/text payload instead of JSON. Our proxy blindly calls `response.json()` and raises `JSONDecodeError`, so the FastAPI route catches the exception and responds with HTTP 500. Users just see a generic 500 and the frontend cannot surface the actual Airflow error.

## What Changes
- Make the DAG run listing endpoint treat upstream responses as opaque: parse JSON when possible, but otherwise stream the raw body with the original status code and media type.
- Centralize this fallback logic so we can reuse it for other Airflow proxy handlers later.
- Add regression coverage to ensure non-JSON Airflow responses propagate without exploding.

## Impact
- Affected specs: `api-backend` (Airflow proxy resilience)
- Affected code:
  - `backend/app/routes/airflow_proxy.py`
  - `backend/tests/test_airflow_proxy_response.py` (new)
