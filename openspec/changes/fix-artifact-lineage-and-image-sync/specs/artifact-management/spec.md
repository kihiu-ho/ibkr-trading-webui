# artifact-management Change: MLflow Lineage Persistence

## ADDED Requirements

### Requirement: Artifact MLflow Lineage Persistence
Chart, LLM, and signal artifacts SHALL capture the MLflow identifiers from the workflow run that produced them.

#### Scenario: Persist lineage when storing artifacts
- **GIVEN** `ibkr_trading_signal_workflow` (or any workflow that calls `mlflow_run_context`) creates chart, LLM, or signal artifacts
- **WHEN** the workflow calls `store_chart_artifact`, `store_llm_artifact`, or `store_signal_artifact`
- **THEN** the stored row's `run_id` SHALL equal the MLflow run ID returned by the workflow's logging step for that same `execution_id`
- **AND** `experiment_id` SHALL equal the MLflow experiment in which the run was logged
- **AND** the frontend SHALL never render `run_id = null` or `experiment_id = null` for artifacts created after this change

#### Scenario: Backfill lineage for legacy artifacts
- **GIVEN** a pre-existing artifact where `workflow_id = ibkr_trading_signal_workflow` and `execution_id` maps to a known MLflow run but the persisted `run_id`/`experiment_id` fields are null
- **WHEN** the artifacts service hydrates that artifact (either during GET `/api/artifacts/{id}` or through an explicit repair cron)
- **THEN** it SHALL look up the latest MLflow run associated with that `execution_id`
- **AND** update the artifact so `run_id`/`experiment_id` persist for future reads without requiring another hydration pass
- **AND** log which artifacts were repaired so QA can confirm that artifacts like ID 24 now show lineage

### Requirement: Artifact Lineage Exposure in UI
Artifact detail views SHALL surface MLflow lineage metadata once it exists.

#### Scenario: Workflow context shows MLflow identifiers
- **WHEN** a user opens the Artifact Detail drawer for a chart generated on November 15, 2025
- **THEN** the workflow context ribbon SHALL display the MLflow run ID and experiment ID (derived from the persisted artifact fields)
- **AND** the "Open in MLflow" button SHALL deep-link to that run without requiring guesswork
