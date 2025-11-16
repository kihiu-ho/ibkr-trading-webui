# fix-artifact-lineage-and-image-sync Tasks

## 1. Specification
- [x] 1.1 Draft proposal covering MLflow lineage gaps and chart image mismatch
- [x] 1.2 Add artifact-management spec deltas
- [x] 1.3 Add api-backend spec deltas
- [x] 1.4 Validate change with `openspec validate`

## 2. Implementation (Future)
- [x] 2.1 Update Airflow workflows to persist MLflow run_id/experiment_id on stored artifacts
- [x] 2.2 Normalize `/api/artifacts/{id}/image` proxy to follow reference/webapp chart rendering logic
- [x] 2.3 Add regression tests covering artifact lineage metadata and MinIO fallback rendering
