## 1. Harden Airflow Image
- [x] 1.1 Create an Airflow-specific requirements file listing `plotly`, `kaleido==0.2.1`, and other chart deps.
- [x] 1.2 Update `Dockerfile.airflow` to install via that file and keep `uv pip install` in sync.
- [x] 1.3 Add a build-time smoke test (`python - <<'PY' ...`) that fails the image build if Kaleido cannot be imported.
- [x] 1.4 Document the new rebuild command for developers (`docker compose build airflow-webserver airflow-scheduler`).

## 2. Runtime Dependency Guard
- [x] 2.1 Add `ensure_kaleido_available()` in `dags/utils/chart_generator.py` that verifies the package before exporting charts.
- [x] 2.2 Attempt an on-the-fly `pip install kaleido>=0.2.1` once per task if the dependency is missing (with timeout + logging).
- [x] 2.3 Raise a custom `KaleidoMissingError` with actionable remediation text when installation still fails and surface it in task logs/XCom.
- [x] 2.4 Update `ibkr_trading_signal_workflow` tasks to call the guard early so tasks fail fast instead of silently falling back to HTML.

## 3. Operational Health Checks
- [x] 3.1 Add a CLI helper (e.g., `scripts/verify_kaleido.sh`) that runs `docker compose exec` (or `airflow info`) to confirm Kaleido is installed.
- [x] 3.2 Integrate that helper into `start-services.sh` or CI so missing Kaleido blocks startup.
- [x] 3.3 Extend docs (`docs/implementation/QUICK_FIX_GUIDE.md` or new troubleshooting entry) with steps for rebuilding the Airflow image and running the health check.

## 4. Testing
- [ ] 4.1 Rebuild the Airflow image and capture the successful Kaleido import log during build.
- [ ] 4.2 Execute `ibkr_trading_signal_workflow` end-to-end; confirm `generate_daily_chart` and `generate_weekly_chart` store JPEG paths.
- [ ] 4.3 Manually uninstall Kaleido inside the container, rerun the DAG, and verify the auto-install/fast-fail behavior plus improved logging.
- [ ] 4.4 Run the new health-check script in CI/local dev to prove it detects both success and failure cases.
