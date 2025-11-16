## MODIFIED Requirements

### Requirement: Chart Export and Storage
Chart export SHALL verify Kaleido availability and stop the task when the dependency cannot be satisfied.

#### Scenario: Export chart to image
- **AND** BEFORE exporting, the workflow SHALL verify Kaleido is importable and log a warning if a self-heal install is required.
- **AND** the task SHALL attempt a one-time automated `pip install kaleido>=0.2.1` when the dependency is missing, surfacing success/failure in task logs.
- **AND** if Kaleido is still unavailable after the auto-install attempt, the task SHALL raise a `KaleidoMissingError` that blocks the run (instead of silently falling back to HTML) and includes remediation text pointing to the Docker rebuild instructions.

### Requirement: Generate Technical Charts for Multiple Timeframes
Workflow runs SHALL capture Kaleido readiness status for every timeframe-specific task.

#### Scenario: Generate daily/weekly/monthly chart
- **AND** the workflow SHALL record in task metadata whether Kaleido passed the preflight check so operators can confirm JPEG export readiness without digging into logs.
