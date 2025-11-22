-- Migration: Create strategy_schedules table
-- Date: 2025-11-22
-- Adds per-strategy scheduling metadata with cron/timezone support.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_name = 'strategy_schedules'
    ) THEN
        CREATE TABLE strategy_schedules (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER NOT NULL UNIQUE REFERENCES strategies(id) ON DELETE CASCADE,
            workflow_id INTEGER REFERENCES workflows(id) ON DELETE SET NULL,
            cron_expression VARCHAR(120) NOT NULL,
            timezone VARCHAR(64) NOT NULL DEFAULT 'America/New_York',
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            description TEXT,
            next_run_time TIMESTAMP WITH TIME ZONE,
            last_run_time TIMESTAMP WITH TIME ZONE,
            last_synced_at TIMESTAMP WITH TIME ZONE,
            pending_airflow_sync BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX idx_strategy_schedules_workflow ON strategy_schedules(workflow_id);
        CREATE INDEX idx_strategy_schedules_enabled ON strategy_schedules(enabled) WHERE enabled = TRUE;
        CREATE INDEX idx_strategy_schedules_next_run ON strategy_schedules(next_run_time);
    END IF;
END $$;
