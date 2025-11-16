## Why
Airflow DAG imports now fail (`ModuleNotFoundError: No module named 'webapp'`) because the new indicator utilities live under the backend/webapp tree, which is not shipped inside the Airflow image. The previous .NET-based `stock_indicators` package also made Airflow unusable on hosts without the CLR. We need a Python-only indicator engine that both the FastAPI backend and the Airflow DAGs can import without runtime dependencies that don't exist in container images.

## What Changes
- Create a shared Python module for technical indicator calculations that lives in the repo root (e.g., `shared/indicators/engine.py`) and is packaged with every service, eliminating cross-package imports.
- Update backend chart APIs, scripts, and Airflow utilities to import from the shared module instead of `webapp.services` or `.NET` libraries.
- Ensure Docker images (backend + Airflow) include the shared module on `PYTHONPATH` and add sanity tests/validation so DAG imports fail fast if the module moves.

## Impact
- Affected specs: `chart-generation` (indicator calculation requirements)
- Affected code: `webapp/services/chart_service.py`, `webapp/app.py`, `backend/services/chart_service.py`, `dags/utils/chart_generator.py`, Dockerfiles/build contexts, relevant tests/scripts.
