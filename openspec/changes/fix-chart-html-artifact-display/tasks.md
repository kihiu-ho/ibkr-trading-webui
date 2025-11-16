## 1. Chart Image Endpoint

- [x] 1.1 Detect non-image artifact paths (e.g., `.html`) and skip streaming them directly.
- [x] 1.2 Reuse `_regenerate_chart_from_metadata()` whenever MinIO/local fetch fails or the stored extension is not `.png|.jpg|.jpeg`.
- [x] 1.3 Update `artifact.image_path` / `chart_data.minio_url` after regeneration to avoid repeated work.
- [x] 1.4 Return a descriptive 409/404 when no metadata snapshot is available so operators know Kaleido must be fixed.

## 2. Market Data Endpoint

- [x] 2.1 Extend `GET /api/artifacts/{id}/market-data` to read `market_data_snapshot.bars` directly from artifact metadata.
- [x] 2.2 Normalize metadata bars into the existing response schema (date, open, high, low, close, volume).
- [x] 2.3 Retain SQL fallback for legacy artifacts, but log when neither source returns data.

## 3. Frontend Chart Detail UX

- [x] 3.1 Detect HTML fallback via `artifact.image_path.endsWith('.html')` and show an "Open interactive HTML" button with the file path link.
- [x] 3.2 Keep the retry button but display guidance that backend will regenerate the PNG (so users retry once the task finishes).
- [x] 3.3 Surface success/error toasts when the `/api/artifacts/{id}/image` request returns regenerated content vs. failure.
- [x] 3.4 Ensure the market data table always renders (because the API now answers) and adjust copy accordingly.

## 4. Testing

- [ ] 4.1 Force an Airflow run without Kaleido, then validate `/api/artifacts/{id}/image` now returns JPEGs derived from metadata.
- [ ] 4.2 Verify `/api/artifacts/{id}/market-data` responds with the snapshot bars when the `market_data` table is empty.
- [ ] 4.3 Confirm the frontend renders regenerated charts, shows HTML fallback link pre-regeneration, and the market data grid populates.
- [ ] 4.4 Regression test with an artifact that already points at a MinIO JPEG to prove no behavior change.
