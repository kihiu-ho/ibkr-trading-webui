-- Migration: Enhance Strategies Table
-- Date: 2025-10-25
-- Description: Adds schedule, symbol_conid, prompt_template_id, and risk_params to strategies table

-- Add new columns if they don't exist
DO $$
BEGIN
    -- Add schedule column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategies' AND column_name = 'schedule'
    ) THEN
        ALTER TABLE strategies ADD COLUMN schedule VARCHAR(100);
        COMMENT ON COLUMN strategies.schedule IS 'Cron expression for automatic execution (e.g., "0 9 * * MON-FRI")';
    END IF;
    
    -- Add symbol_conid column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategies' AND column_name = 'symbol_conid'
    ) THEN
        ALTER TABLE strategies ADD COLUMN symbol_conid INTEGER;
        COMMENT ON COLUMN strategies.symbol_conid IS 'IBKR Contract ID for the trading symbol';
    END IF;
    
    -- Add prompt_template_id column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategies' AND column_name = 'prompt_template_id'
    ) THEN
        ALTER TABLE strategies ADD COLUMN prompt_template_id INTEGER REFERENCES prompt_templates(id) ON DELETE SET NULL;
        COMMENT ON COLUMN strategies.prompt_template_id IS 'LLM prompt template used for analysis';
    END IF;
    
    -- Add risk_params column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategies' AND column_name = 'risk_params'
    ) THEN
        ALTER TABLE strategies ADD COLUMN risk_params JSONB;
        COMMENT ON COLUMN strategies.risk_params IS 'Risk management parameters (risk_per_trade, stop_loss_type, position_sizing, etc.)';
    END IF;
    
    -- Add last_executed_at column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategies' AND column_name = 'last_executed_at'
    ) THEN
        ALTER TABLE strategies ADD COLUMN last_executed_at TIMESTAMP WITH TIME ZONE;
        COMMENT ON COLUMN strategies.last_executed_at IS 'Timestamp of last execution';
    END IF;
    
    -- Add next_execution_at column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'strategies' AND column_name = 'next_execution_at'
    ) THEN
        ALTER TABLE strategies ADD COLUMN next_execution_at TIMESTAMP WITH TIME ZONE;
        COMMENT ON COLUMN strategies.next_execution_at IS 'Calculated next execution time based on schedule';
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_strategies_schedule ON strategies(next_execution_at) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_strategies_symbol_conid ON strategies(symbol_conid);
CREATE INDEX IF NOT EXISTS idx_strategies_prompt_template_id ON strategies(prompt_template_id);

-- Set default risk_params for existing strategies
UPDATE strategies 
SET risk_params = '{
    "risk_per_trade": 0.01,
    "stop_loss_type": "atr",
    "position_sizing": "risk_based",
    "max_position_size": 1000
}'::jsonb
WHERE risk_params IS NULL;

