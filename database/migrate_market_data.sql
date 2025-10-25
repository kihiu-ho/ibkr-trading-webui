-- Migration script to update market_data table schema
-- This updates the table to match the SQLAlchemy model used for IBKR data storage

BEGIN;

-- Backup existing data (if any)
CREATE TABLE IF NOT EXISTS market_data_backup AS SELECT * FROM market_data;

-- Drop old table
DROP TABLE IF EXISTS market_data CASCADE;

-- Create new market_data table with correct schema
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    conid INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL,  -- IBKR period: 1d, 1w, 1m, 1y
    bar VARCHAR(20) NOT NULL,     -- IBKR bar size: 1min, 5min, 1h, 1d, 1w
    data JSONB NOT NULL,          -- Raw IBKR response with OHLCV data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to codes table
    CONSTRAINT fk_market_data_conid FOREIGN KEY (conid) 
        REFERENCES codes(conid) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_market_data_conid ON market_data(conid);
CREATE INDEX idx_market_data_period_bar ON market_data(conid, period, bar);
CREATE INDEX idx_market_data_created_at ON market_data(created_at DESC);

-- Add comment
COMMENT ON TABLE market_data IS 'Market data cache from IBKR API';
COMMENT ON COLUMN market_data.conid IS 'Interactive Brokers contract ID';
COMMENT ON COLUMN market_data.period IS 'IBKR period parameter (1d, 1w, 1m, 6m, 1y, etc.)';
COMMENT ON COLUMN market_data.bar IS 'IBKR bar size (1min, 5min, 1h, 1d, 1w, etc.)';
COMMENT ON COLUMN market_data.data IS 'Raw IBKR historical data response in JSON format';

COMMIT;

