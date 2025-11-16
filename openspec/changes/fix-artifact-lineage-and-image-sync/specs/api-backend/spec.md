# api-backend Change: Artifact Lineage & Image Parity

## ADDED Requirements

### Requirement: Artifact API Hydrates MLflow Lineage
The artifacts API SHALL ensure `run_id` and `experiment_id` are populated before returning any artifact payload.

#### Scenario: GET /api/artifacts/{id} backfills lineage
- **GIVEN** artifact 24 (`workflow_id = ibkr_trading_signal_workflow`, `execution_id = 2025-11-15 13:54:31.981650+00:00`) currently returns `"run_id": null`
- **WHEN** a client calls `GET /api/artifacts/24`
- **THEN** the API SHALL resolve the MLflow run recorded for that execution (via the `log_workflow_to_mlflow` step or MLflow REST API)
- **AND** patch the artifact row so the response includes non-null `run_id` and `experiment_id`
- **AND** subsequent GETs SHALL not require another hydration for the same artifact

#### Scenario: GET /api/artifacts?type=chart surfaces lineage fields
- **WHEN** the frontend fetches chart artifacts for grouping by execution
- **THEN** every returned artifact SHALL include populated `run_id`/`experiment_id`
- **AND** the payload SHALL add hyperlinks (or fields) that allow the UI to build "View in MLflow" actions without additional API calls

### Requirement: Chart Image Endpoint Matches Reference Renderer
`GET /api/artifacts/{id}/image` SHALL stream the same chart visual produced by `reference/webapp/app.py` for the artifact's market data snapshot.

#### Scenario: Proxy MinIO objects with authentication
- **WHEN** `chart_data.minio_url = http://localhost:9000/trading-charts/charts/TSLA/daily/20251115_135558_1b8741ec.png`
- **THEN** the endpoint SHALL parse the bucket/object from the URL, request it through the configured MinIO client (with auth), and stream the bytes with accurate `Content-Type`
- **AND** the response headers SHALL advertise caching (`Cache-Control: public, max-age=3600`) so UI reloads do not re-fetch immediately

#### Scenario: Regenerate chart when object is missing or stale
- **GIVEN** the MinIO object is missing OR the stored PNG does not match the artifact's `metadata.market_data_snapshot`
- **WHEN** `GET /api/artifacts/{id}/image` is invoked
- **THEN** the backend SHALL rebuild the chart using the same indicator pipeline from `reference/webapp/app.py` (SMA 20/50/200, Bollinger Bands, SuperTrend, MACD, RSI, OBV, ATR, Volume) and the OHLCV bars embedded in the artifact metadata
- **AND** the regenerated image SHALL be uploaded back to MinIO and/or cached on disk so repeated calls stream the new asset without recomputing every time
- **AND** logs SHALL note that a regeneration occurred for auditing
