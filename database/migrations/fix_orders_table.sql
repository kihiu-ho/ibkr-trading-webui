-- Migration: Fix orders table schema to match Order model
-- Date: 2025-11-08
-- Description: Remove FK constraints and fix column types

-- Remove foreign key constraints that reference non-existent tables
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_strategy_id_fkey;
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_decision_id_fkey;

-- Change column types to match SQLAlchemy model
-- Note: PostgreSQL doesn't allow direct type changes for columns with data,
-- but since this is a new table with no data, we can alter types
ALTER TABLE orders ALTER COLUMN quantity TYPE INTEGER;
ALTER TABLE orders ALTER COLUMN price TYPE REAL;
ALTER TABLE orders ALTER COLUMN filled_price TYPE REAL;
ALTER TABLE orders ALTER COLUMN commission TYPE REAL;
ALTER TABLE orders ALTER COLUMN realized_pnl TYPE REAL;

-- Add NOT NULL constraints where required by model
ALTER TABLE orders ALTER COLUMN side SET NOT NULL;
ALTER TABLE orders ALTER COLUMN quantity SET NOT NULL;
ALTER TABLE orders ALTER COLUMN order_type SET NOT NULL;
ALTER TABLE orders ALTER COLUMN tif SET NOT NULL;
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;

-- Update indexes to match model
DROP INDEX IF EXISTS idx_orders_strategy;
CREATE INDEX IF NOT EXISTS idx_orders_strategy_id ON orders(strategy_id);
CREATE INDEX IF NOT EXISTS idx_orders_ibkr_order_id ON orders(ibkr_order_id);
CREATE INDEX IF NOT EXISTS idx_orders_submitted_at ON orders(submitted_at DESC NULLS LAST);
