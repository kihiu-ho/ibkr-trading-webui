-- Migration: Add Workflow Lineage Table
-- Date: 2025-10-25
-- Description: Creates workflow_lineage table for tracking execution step input/output

CREATE TABLE IF NOT EXISTS workflow_lineage (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    step_metadata JSONB,  -- Renamed from 'metadata' to avoid SQLAlchemy reserved name
    error TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'success',  -- success, error
    duration_ms INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_execution_step UNIQUE (execution_id, step_name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_lineage_execution_id ON workflow_lineage(execution_id);
CREATE INDEX IF NOT EXISTS idx_lineage_step_name ON workflow_lineage(step_name);
CREATE INDEX IF NOT EXISTS idx_lineage_recorded_at ON workflow_lineage(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_lineage_status ON workflow_lineage(status);

-- Add execution_id to strategy_executions if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategy_executions' 
        AND column_name = 'execution_id'
    ) THEN
        ALTER TABLE strategy_executions ADD COLUMN execution_id VARCHAR(255) UNIQUE;
        CREATE INDEX idx_strategy_executions_execution_id ON strategy_executions(execution_id);
    END IF;
END $$;

COMMENT ON TABLE workflow_lineage IS 'Tracks input/output of each step in workflow execution for complete traceability';
COMMENT ON COLUMN workflow_lineage.execution_id IS 'Unique identifier for workflow execution (e.g., strategy_123_2025-10-25T10:30:00)';
COMMENT ON COLUMN workflow_lineage.input_data IS 'JSON object containing all inputs to this step';
COMMENT ON COLUMN workflow_lineage.output_data IS 'JSON object containing all outputs from this step';

