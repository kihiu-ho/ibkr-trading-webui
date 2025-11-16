## Overview
We will host the pandas-based indicator functions inside a new top-level `shared/indicator_engine.py` package. The repo root is already mounted into backend containers, and we will update Docker build contexts (backend + Airflow) to copy the `shared/` directory alongside `backend/` and `dags/`. This removes the tight coupling to `webapp.services` and keeps Airflow imports self-contained.

## Key Decisions
1. **Shared Module Location**: `shared/indicator_engine.py` avoids circular dependencies and can be imported as `shared.indicator_engine` from both backend and Airflow.
2. **Pure Python Dependencies**: The engine will only rely on pandas/numpy, which are already part of existing requirements, allowing it to run without .NET or pythonnet.
3. **Docker Packaging**: Backend and Airflow Dockerfiles will copy the `shared/` directory so containers can resolve the module at runtime. This also ensures tests run consistently in CI by pointing `PYTHONPATH` at project root.
