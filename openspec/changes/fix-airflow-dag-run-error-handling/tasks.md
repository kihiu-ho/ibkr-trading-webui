## 1. Implementation
- [x] 1.1 Add a reusable helper in `backend/app/routes/airflow_proxy.py` that returns a FastAPI response even when Airflow sends non-JSON payloads.
- [x] 1.2 Update the DAG run listing route (`GET /api/airflow/dags/{dag_id}/dagRuns`) to use the helper and preserve upstream status codes/content-types.
- [x] 1.3 Improve logging so unexpected Airflow payloads are recorded without crashing the handler.

## 2. Testing & Validation
- [x] 2.1 Add unit tests covering JSON and plain-text Airflow responses to confirm the helper never raises.
- [x] 2.2 Run targeted tests (or linting) if applicable and document verification steps.
- [x] 2.3 Run `openspec validate fix-airflow-dag-run-error-handling --strict`.
