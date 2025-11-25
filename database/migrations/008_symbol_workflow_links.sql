BEGIN;

-- Create association table with workflow-specific scheduling configuration
CREATE TABLE IF NOT EXISTS symbol_workflow_links (
    id SERIAL PRIMARY KEY,
    workflow_symbol_id INTEGER NOT NULL REFERENCES workflow_symbols(id) ON DELETE CASCADE,
    workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    timezone VARCHAR(64) NOT NULL DEFAULT 'America/New_York',
    session_start TIME,
    session_end TIME,
    allow_weekend BOOLEAN NOT NULL DEFAULT FALSE,
    config JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_symbol_workflow_link_pair
    ON symbol_workflow_links (workflow_symbol_id, workflow_id);

CREATE INDEX IF NOT EXISTS idx_symbol_workflow_links_symbol_priority
    ON symbol_workflow_links (workflow_symbol_id, priority);

-- Migrate legacy associations into the new table, carrying over scheduling data if present
DO $$
DECLARE
    has_timezone BOOLEAN;
    has_session_start BOOLEAN;
    has_session_end BOOLEAN;
    has_allow_weekend BOOLEAN;
    has_config BOOLEAN;
    insert_sql TEXT;
BEGIN
    IF to_regclass('workflow_symbol_workflows') IS NULL THEN
        RETURN;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='timezone'
    ) INTO has_timezone;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='session_start'
    ) INTO has_session_start;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='session_end'
    ) INTO has_session_end;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='allow_weekend'
    ) INTO has_allow_weekend;
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='config'
    ) INTO has_config;

    insert_sql := 'INSERT INTO symbol_workflow_links '
        || '(workflow_symbol_id, workflow_id, is_active, priority, timezone, session_start, session_end, allow_weekend, config) '
        || 'SELECT swf.workflow_symbol_id, swf.workflow_id, TRUE AS is_active, '
        || 'ROW_NUMBER() OVER (PARTITION BY swf.workflow_symbol_id ORDER BY swf.workflow_id) - 1 AS priority, ';

    insert_sql := insert_sql || CASE WHEN has_timezone THEN 'COALESCE(ws.timezone, ''America/New_York'')' ELSE '''America/New_York''' END || ' AS timezone, ';
    insert_sql := insert_sql || CASE WHEN has_session_start THEN 'ws.session_start' ELSE 'NULL::time' END || ' AS session_start, ';
    insert_sql := insert_sql || CASE WHEN has_session_end THEN 'ws.session_end' ELSE 'NULL::time' END || ' AS session_end, ';
    insert_sql := insert_sql || CASE WHEN has_allow_weekend THEN 'COALESCE(ws.allow_weekend, FALSE)' ELSE 'FALSE' END || ' AS allow_weekend, ';
    insert_sql := insert_sql || CASE WHEN has_config THEN 'ws.config::jsonb' ELSE 'NULL::jsonb' END || ' AS config '
        || 'FROM workflow_symbol_workflows swf '
        || 'LEFT JOIN workflow_symbols ws ON ws.id = swf.workflow_symbol_id '
        || ' ON CONFLICT DO NOTHING';

    EXECUTE insert_sql;
END $$;

-- Drop the legacy join table now that data has been migrated
DROP TABLE IF EXISTS workflow_symbol_workflows;

-- Remove scheduling/config columns from workflow_symbols if they still exist
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='timezone'
    ) THEN
        ALTER TABLE workflow_symbols DROP COLUMN timezone;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='session_start'
    ) THEN
        ALTER TABLE workflow_symbols DROP COLUMN session_start;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='session_end'
    ) THEN
        ALTER TABLE workflow_symbols DROP COLUMN session_end;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='allow_weekend'
    ) THEN
        ALTER TABLE workflow_symbols DROP COLUMN allow_weekend;
    END IF;
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='workflow_symbols' AND column_name='config'
    ) THEN
        ALTER TABLE workflow_symbols DROP COLUMN config;
    END IF;
END $$;

COMMIT;
