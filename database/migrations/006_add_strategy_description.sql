-- Migration: Add description column to strategies table
-- Ensures SQLAlchemy Strategy model matches database schema.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'strategies'
          AND column_name = 'description'
    ) THEN
        ALTER TABLE strategies ADD COLUMN description TEXT;
        COMMENT ON COLUMN strategies.description IS 'Human-readable notes for the trading strategy';
    END IF;
END $$;
