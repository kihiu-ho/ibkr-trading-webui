# Fix Airflow Kaleido Runtime Gaps

## Why
- On host `67a124b3f152`, the `ibkr_trading_signal_workflow.generate_daily_chart` run `manual__2025-11-16T12:59:36.697890+00:00` failed to export a JPEG even though `Dockerfile.airflow` already installs Plotly/Kaleido. Plotly raised `ValueError: Image export using the "kaleido" engine requires the Kaleido package`, forcing HTML fallback artifacts like `/app/charts/TSLA_1D_20251116_125940.html`.
- When Kaleido is missing inside the DAG runtime, all chart artifacts degrade to HTML-only, MinIO uploads never occur, and downstream LLM + artifact viewers must rely on regeneration workarounds.
- Rebuilding the Airflow image manually is brittle; we need build-time verification plus runtime self-healing so every task run either installs Kaleido automatically or fails fast with a clear remediation path.

## What Changes
1. **Airflow image hardening**
   - Add an explicit `requirements-airflow.txt` (or extend existing tooling) that pins `kaleido==0.2.1` alongside plotly.
   - Update `Dockerfile.airflow` to install from that file and run a build-time smoke test `python - <<<'import kaleido, plotly.io as pio; pio.kaleido.scope'` so CI fails if Kaleido is absent.
   - Ensure Chromium + Kaleido assets live in the same layer and document the rebuild command (`docker compose build airflow-webserver airflow-scheduler`).
2. **Runtime dependency check & auto-install**
   - Introduce `ensure_kaleido_available()` inside `dags/utils/chart_generator.py` that (a) `importlib.util.find_spec('kaleido')`, (b) tries a one-time `subprocess.run(['pip','install','kaleido>=0.2.1'])` if missing, and (c) raises a custom `KaleidoMissingError` with actionable log hints if installation fails.
   - Push the dependency status into task logs / XCom context so downstream troubleshooting knows why HTML fallback occurred.
3. **Operational guardrails**
   - Wire a health check (CLI script or `start-services.sh` step) that calls `docker compose exec airflow-worker python -c "import kaleido"` and surfaces failures before workflows run.
   - Document the new verification + rebuild steps in `docs/implementation/QUICK_FIX_GUIDE.md` (or a new troubleshooting doc) so operators know how to recover.

## Impact
- Specs touched: `chart-generation` (export requirement now mandates Kaleido validation/self-healing) and `airflow-integration` (custom Airflow image must ship the dependency and provide health checks).
- No API surface change; focus is on CI/CD and DAG runtime stability.

## Testing
1. Build the new Airflow image locally; CI must fail if Kaleido import fails during build.
2. Run `ibkr_trading_signal_workflow` in a clean environment → verify both daily and weekly tasks export JPEGs without triggering HTML fallback.
3. Temporarily uninstall Kaleido inside the running container → DAG should auto-install or emit the new actionable error before falling back.
4. Run the health-check script in `start-services.sh` (or a GitHub Action) to ensure it reports success when Kaleido exists and fails when it does not.
