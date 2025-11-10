# Change Proposal: Add timeframe directory to chart artifact paths in MinIO

## Summary
Chart HTML/JP(E)G files stored in MinIO currently use the path pattern:
`charts/{symbol}/{timestamp}_{uuid}_{chart_id}.{html|jpg}`. Some clients (and UI references) expect URLs that include a human-readable timeframe segment, e.g.:
`http://localhost:9000/trading-charts/charts/TSLA/daily/20251110_120715_1cab8cfe.html`.

This proposal introduces a backward-compatible enhancement to include a timeframe directory in the stored object path and returned public URLs:
`charts/{symbol}/{timeframeAlias}/{timestamp}_{uuid}_{chart_id}.{ext}`
where `timeframeAlias ∈ {daily, weekly, monthly}` derived from `{1d, 1w, 1mo}` respectively.

## Problem
- Incoming links reference paths like `/charts/{symbol}/daily/{file}.html`, which do not exist because current objects omit the timeframe folder.
- Direct MinIO URLs with `daily/weekly` segments return 404s.

## Goals
- Generate chart artifacts under timeframe directories for future compatibility.
- Preserve existing paths for already-generated content (no migration required).
- Keep public URLs browser-accessible via `MINIO_PUBLIC_ENDPOINT` while backend uses internal `MINIO_ENDPOINT`.

## Non-Goals
- No retroactive object migration in MinIO.
- No changes to database schemas.

## Design
1. Extend `MinIOService.upload_chart` signature to accept an optional `timeframe: Optional[str]`.
2. Map timeframe codes to aliases:
   - `1d` → `daily`
   - `1w` → `weekly`
   - `1mo` → `monthly`
   - default/fallback: no extra directory if unspecified
3. Build object paths:
   - If timeframe provided: `charts/{symbol}/{alias}/{timestamp}_{uuid}_{chart_id}.{ext}`
   - Else: maintain current behavior (no timeframe dir)
4. Update `ChartGenerator.generate_chart` to pass `timeframe` to `upload_chart`.

## API/Behavioral Changes
- Public URLs returned by chart generation will include the timeframe directory when timeframe is known.
- Existing callers remain compatible; `timeframe` is optional.

## Risks & Mitigations
- Risk: Mismatch in alias names. Mitigation: Controlled mapping table; unknown values fall back to no extra directory.
- Risk: Clients relying on previous pattern. Mitigation: Only new charts change; old URLs still resolve; no DB or storage migration.

## Test Plan
- Unit-ish validation: generate chart with `timeframe = 1d` and assert returned URL contains `/daily/`.
- Manual check: curl HEAD the returned URL (if environment running with MinIO).
- Regression: ensure charts still generate when `timeframe` omitted (paths unchanged).

## Rollout
- Merge and deploy backend.
- No migrations required. New artifacts will use new paths; existing untouched.

## Files Affected
- `backend/services/minio_service.py` (add timeframe support)
- `backend/services/chart_generator.py` (pass timeframe)


