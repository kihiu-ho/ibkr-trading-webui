## 1. Shared Indicator Module
- [x] 1.1 Create `shared/indicator_engine.py` (or equivalent package) with SMA, Bollinger, MACD, RSI, ATR, SuperTrend, OBV, and volume helpers implemented in pure Python/pandas.
- [x] 1.2 Add unit-style helper to ensure the module exposes a `build_chart_payload(df)` function used by both backend and Airflow.

## 2. Backend & Webapp Updates
- [x] 2.1 Update `webapp/services/chart_service.py`, `webapp/app.py`, and any other backend services to import from the shared module.
- [x] 2.2 Remove direct dependencies on `stock_indicators`/pythonnet from backend requirements and ensure existing APIs/tests call the shared helper.

## 3. Airflow DAG & Utilities
- [x] 3.1 Update `dags/utils/chart_generator.py` (and related DAG tasks) to import the shared module without referencing `webapp.*`.
- [x] 3.2 Ensure Airflow Docker image copies the shared module into `/app` so DAG imports succeed.

## 4. Tooling & Validation
- [x] 4.1 Update validation scripts/tests (`tests/scripts/validate_plotly_llm_implementation.py`, etc.) to look for the shared module usage instead of `stock_indicators`.
- [x] 4.2 Run at least `python - <<'PY'` smoke tests (or targeted pytest module) from project root and document results to confirm the backend can import the shared module.
