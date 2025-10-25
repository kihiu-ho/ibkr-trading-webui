-- Migration: Add LLM Signal Generation Support
-- Date: 2025-10-24
-- Description: Adds LLM configuration to strategies table and creates trading_signals table

-- Extend strategies table with LLM configuration
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS llm_enabled INTEGER DEFAULT 0;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS llm_model VARCHAR(50) DEFAULT 'gpt-4-vision-preview';
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS llm_language VARCHAR(5) DEFAULT 'en';
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS llm_timeframes JSON DEFAULT '["1d", "1w"]';
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS llm_consolidate INTEGER DEFAULT 1;
ALTER TABLE strategies ADD COLUMN IF NOT EXISTS llm_prompt_custom VARCHAR(500);

-- Create trading_signals table
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    
    -- Signal details
    signal_type VARCHAR(10) NOT NULL,
    trend VARCHAR(20),
    confidence FLOAT,
    
    -- Timeframes
    timeframe_primary VARCHAR(10) NOT NULL DEFAULT '1d',
    timeframe_confirmation VARCHAR(10) DEFAULT '1w',
    
    -- Trading parameters
    entry_price_low FLOAT,
    entry_price_high FLOAT,
    stop_loss FLOAT,
    target_conservative FLOAT,
    target_aggressive FLOAT,
    r_multiple_conservative FLOAT,
    r_multiple_aggressive FLOAT,
    position_size_percent FLOAT,
    
    -- Signal confirmation
    confirmation_signals JSONB,
    
    -- Analysis text
    analysis_daily TEXT,
    analysis_weekly TEXT,
    analysis_consolidated TEXT,
    
    -- Chart URLs
    chart_url_daily VARCHAR(500),
    chart_url_weekly VARCHAR(500),
    chart_html_daily VARCHAR(500),
    chart_html_weekly VARCHAR(500),
    
    -- Metadata
    language VARCHAR(5) NOT NULL DEFAULT 'en',
    model_used VARCHAR(50),
    provider VARCHAR(20),
    
    -- Timestamps
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    execution_price FLOAT,
    execution_time TIMESTAMP WITH TIME ZONE,
    execution_notes TEXT
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol ON trading_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_status ON trading_signals(symbol, status);
CREATE INDEX IF NOT EXISTS idx_trading_signals_strategy_id ON trading_signals(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trading_signals_generated_at ON trading_signals(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_trading_signals_status ON trading_signals(status);

-- Add comment
COMMENT ON TABLE trading_signals IS 'Stores LLM-generated trading signals from chart analysis';
COMMENT ON COLUMN trading_signals.signal_type IS 'BUY, SELL, or HOLD';
COMMENT ON COLUMN trading_signals.trend IS 'strong_bullish, bullish, neutral, bearish, or strong_bearish';
COMMENT ON COLUMN trading_signals.confirmation_signals IS 'JSON containing 3/4 signal confirmation details';
COMMENT ON COLUMN trading_signals.status IS 'active, expired, executed, or cancelled';

