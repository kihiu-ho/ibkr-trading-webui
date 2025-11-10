-- Create artifacts table for storing ML/LLM artifacts
-- Migration: create_artifacts_table
-- Date: 2025-11-08

CREATE TABLE IF NOT EXISTS artifacts (
    id SERIAL PRIMARY KEY,
    
    -- Artifact identification
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'llm', 'chart', 'signal', 'market_data'
    
    -- Associated data
    symbol VARCHAR(50),
    run_id VARCHAR(255),
    experiment_id VARCHAR(255),
    
    -- Workflow tracking
    workflow_id VARCHAR(255),
    execution_id VARCHAR(255),
    step_name VARCHAR(100),
    dag_id VARCHAR(255),
    task_id VARCHAR(255),
    
    -- LLM-specific fields
    prompt TEXT,
    response TEXT,
    prompt_length INTEGER,
    response_length INTEGER,
    model_name VARCHAR(100),
    
    -- Chart-specific fields
    image_path TEXT,
    chart_type VARCHAR(50),
    chart_data JSONB,
    
    -- Signal-specific fields
    action VARCHAR(20),
    confidence DECIMAL(3,2),
    signal_data JSONB,
    
    -- Metadata
    artifact_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_artifacts_name ON artifacts(name);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);
CREATE INDEX IF NOT EXISTS idx_artifacts_symbol ON artifacts(symbol);
CREATE INDEX IF NOT EXISTS idx_artifacts_run_id ON artifacts(run_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_experiment_id ON artifacts(experiment_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_workflow_id ON artifacts(workflow_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_execution_id ON artifacts(execution_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_workflow_execution ON artifacts(workflow_id, execution_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_step_name ON artifacts(step_name);
CREATE INDEX IF NOT EXISTS idx_artifacts_dag_id ON artifacts(dag_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type_symbol ON artifacts(type, symbol);
CREATE INDEX IF NOT EXISTS idx_artifacts_created_at ON artifacts(created_at DESC);

-- Add comments
COMMENT ON TABLE artifacts IS 'Stores ML/LLM artifacts including charts, signals, and analysis results';
COMMENT ON COLUMN artifacts.workflow_id IS 'Workflow identifier (e.g., ibkr_trading_signal_workflow)';
COMMENT ON COLUMN artifacts.execution_id IS 'Specific workflow execution/run ID';
COMMENT ON COLUMN artifacts.step_name IS 'Workflow step that generated this artifact';
COMMENT ON COLUMN artifacts.dag_id IS 'Airflow DAG ID';
COMMENT ON COLUMN artifacts.task_id IS 'Airflow task ID';
COMMENT ON COLUMN artifacts.artifact_metadata IS 'Additional metadata (stored as metadata in API)';

