# Fix Chart HTML Artifact Display

## Why
- Airflow's `ibkr_trading_signal_workflow.generate_weekly_chart` task (run `manual__2025-11-16T03:52:06.563106+00:00`) succeeded but Plotly failed to export a JPEG because Kaleido was missing, so the DAG stored `TSLA_1W_20251116_035212.html` as the chart artifact.
- The backend `/api/artifacts/{id}/image` endpoint streamed that `.html` file with `image/png` headers, so the frontend detail view raised “Chart image not available” and only exposed the raw path.
- Even though the artifact metadata already carried a `market_data_snapshot`, `/api/artifacts/{id}/market-data` still queries the shared `market_data` table. When cache misses occur the API returns zero rows, and the UI shows “No market data available for this artifact”.
- Users cannot review the generated chart or the OHLCV context for the execution, making the workflow output unusable.

## What Changes
### 1. Regenerate images when stored path is HTML or missing
- Detect non-image extensions (e.g., `.html`) or failed MinIO/local loads inside `backend/api/chart_images.py`.
- Treat these cases the same as missing files: use `_regenerate_chart_from_metadata()` to rebuild a JPEG from the persisted `market_data_snapshot`, upload it to MinIO, and update `artifact.image_path`/`chart_data.minio_url` for future loads.
- Return a 409 + remediation hint only if metadata lacks bars, so operators know to reinstall Kaleido instead of getting a broken `<img>` payload.

### 2. Serve market data directly from artifact metadata
- Update `GET /api/artifacts/{id}/market-data` to prefer the `market_data_snapshot.bars` list stored on the artifact before hitting the `market_data` table.
- Preserve the existing response contract (`{symbol, count, data[]}`) so the frontend needs no schema changes.
- When both sources are empty, return HTTP 404 with a descriptive error and log the artifact id/symbol.

### 3. Frontend affordances for regenerated/HTML charts
- Enhance `frontend/templates/artifact_detail.html` so the Chart Image block surfaces when the backend regenerated a chart (success toast) or when only an `.html` artifact remains.
- If the metadata indicates HTML fallback (image path ends with `.html` and regeneration is still running), show a prominent "Open interactive HTML" button instead of the broken `<img>`, and keep the existing retry button pointed at `/api/artifacts/{id}/image?t=...` to refresh after regeneration.
- Highlight that market data is now always shown (no secondary fetch failures) to reinforce trust.

## Impact
- Specs touched: `api-backend` (artifact image + market data endpoints) and `chart-viewing` (chart detail fallback UX).
- No workflow changes; Airflow continues to emit HTML fallback files when Kaleido is missing, but the UI/backend now repair the artifact automatically.

## Testing
1. Run `ibkr_trading_signal_workflow` with Kaleido uninstalled to force HTML fallback, wait for the artifact to appear, and load `/api/artifacts/{id}/image` → receives regenerated JPEG.
2. Hit `/api/artifacts/{id}/market-data` for the same artifact → response contains the 20 weekly bars from metadata even when `market_data` table is empty.
3. Open the artifact detail page: the image renders (after regeneration) or the HTML fallback button appears; the market data table populates without manual refresh.
4. Regression: artifacts that already point to MinIO JPEGs still stream through unchanged, and the market data endpoint continues to work for cached symbols.
