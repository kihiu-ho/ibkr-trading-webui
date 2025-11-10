-- Add workflow tracking fields to artifacts table
-- Migration: add_workflow_tracking_to_artifacts
-- Date: 2025-11-08

-- Add workflow tracking columns
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS workflow_id VARCHAR(255);
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS execution_id VARCHAR(255);
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS step_name VARCHAR(100);
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS dag_id VARCHAR(255);
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS task_id VARCHAR(255);

-- Add indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_artifacts_workflow_id ON artifacts(workflow_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_execution_id ON artifacts(execution_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_workflow_execution ON artifacts(workflow_id, execution_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_step_name ON artifacts(step_name);
CREATE INDEX IF NOT EXISTS idx_artifacts_dag_id ON artifacts(dag_id);

-- Add comments
COMMENT ON COLUMN artifacts.workflow_id IS 'Workflow identifier (e.g., ibkr_trading_signal_workflow)';
COMMENT ON COLUMN artifacts.execution_id IS 'Specific workflow execution/run ID';
COMMENT ON COLUMN artifacts.step_name IS 'Workflow step that generated this artifact';
COMMENT ON COLUMN artifacts.dag_id IS 'Airflow DAG ID';
COMMENT ON COLUMN artifacts.task_id IS 'Airflow task ID';

