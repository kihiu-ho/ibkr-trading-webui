## ADDED Requirements

### Requirement: Artifact Chart Retrieval Resilience
The API SHALL guarantee that chart artifacts remain viewable even when the stored file is an HTML fallback or missing.

#### Scenario: Regenerate non-image artifacts
- **WHEN** `GET /api/artifacts/{id}/image` resolves to a path whose extension is not `.png`, `.jpg`, or `.jpeg`
- **THEN** the service SHALL treat the artifact as missing and invoke `_regenerate_chart_from_metadata()`
- **AND** regeneration SHALL use the artifact's `market_data_snapshot` to rebuild a JPEG, upload it to MinIO, and update `image_path` / `chart_data.minio_url`
- **AND** the response SHALL stream the regenerated JPEG with the correct `image/*` headers
- **AND** if metadata lacks bars, the API SHALL return HTTP 409 with guidance to reinstall Kaleido or rerun the workflow

#### Scenario: Serve market data snapshot first
- **WHEN** `GET /api/artifacts/{id}/market-data` is called
- **THEN** the service SHALL populate its response from the artifact's persisted `market_data_snapshot.bars` when available
- **AND** the response schema SHALL remain `{symbol, count, data[]}` with ISO timestamps and numeric OHLCV values
- **AND** only when the snapshot is absent SHALL the API query the shared `market_data` table as a fallback
- **AND** if both sources are empty, the API SHALL return HTTP 404 with a clear explanation that the artifact lacks stored bars
