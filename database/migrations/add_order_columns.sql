-- Migration: Add missing columns to orders table
-- Date: 2025-11-08
-- Description: Adds columns to orders table to match Order model

-- Add missing columns to orders table
ALTER TABLE orders ADD COLUMN IF NOT EXISTS signal_id INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS side VARCHAR(10);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tif VARCHAR(10) DEFAULT 'DAY';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS filled_price DECIMAL(10, 2);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS filled_quantity INTEGER DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS remaining_quantity INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS commission DECIMAL(10, 2);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS realized_pnl DECIMAL(10, 2);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS ibkr_response JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Update existing records to have created_at set to submitted_at if it exists
UPDATE orders SET created_at = submitted_at WHERE created_at IS NULL AND submitted_at IS NOT NULL;
UPDATE orders SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_signal_id ON orders(signal_id);
CREATE INDEX IF NOT EXISTS idx_orders_side ON orders(side);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_updated_at ON orders(updated_at);

-- Update comments
COMMENT ON COLUMN orders.signal_id IS 'Reference to trading signal that triggered this order';
COMMENT ON COLUMN orders.side IS 'Order side: BUY, SELL, SELL_SHORT';
COMMENT ON COLUMN orders.tif IS 'Time in force: DAY, GTC, IOC';
COMMENT ON COLUMN orders.filled_price IS 'Average fill price';
COMMENT ON COLUMN orders.filled_quantity IS 'Total quantity filled';
COMMENT ON COLUMN orders.remaining_quantity IS 'Remaining quantity to fill';
COMMENT ON COLUMN orders.commission IS 'Total commission paid';
COMMENT ON COLUMN orders.realized_pnl IS 'Realized profit/loss for this order';
COMMENT ON COLUMN orders.ibkr_response IS 'Full IBKR API response JSON';
COMMENT ON COLUMN orders.error_message IS 'Error message if order failed';
COMMENT ON COLUMN orders.created_at IS 'When order was created in system';
COMMENT ON COLUMN orders.updated_at IS 'When order was last updated';
