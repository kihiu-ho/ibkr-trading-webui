-- Migration: Add Symbols Table
-- Date: 2025-10-25
-- Description: Creates symbols table for caching IBKR symbol search results

CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    conid INTEGER UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name TEXT,
    exchange VARCHAR(20),
    currency VARCHAR(3),
    asset_type VARCHAR(20),  -- STOCK, OPTION, FUTURE, FOREX, etc.
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol);
CREATE INDEX IF NOT EXISTS idx_symbols_conid ON symbols(conid);
CREATE INDEX IF NOT EXISTS idx_symbols_exchange ON symbols(exchange);
CREATE INDEX IF NOT EXISTS idx_symbols_asset_type ON symbols(asset_type);

COMMENT ON TABLE symbols IS 'Caches IBKR symbol information for faster lookup';
COMMENT ON COLUMN symbols.conid IS 'IBKR Contract ID - unique identifier for the instrument';
COMMENT ON COLUMN symbols.symbol IS 'Trading symbol (e.g., AAPL, MSFT)';

