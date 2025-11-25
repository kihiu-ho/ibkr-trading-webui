-- Initialize database schema for IBKR Trading Platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create workflows table (following SQLAlchemy naming)
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    steps JSON NOT NULL DEFAULT '[]',
    default_params JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create codes table for financial instruments
CREATE TABLE IF NOT EXISTS codes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    conid INTEGER NOT NULL UNIQUE,
    exchange VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create strategies table (following SQLAlchemy naming)
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE SET NULL,
    type VARCHAR(50),
    param JSON DEFAULT '{}',
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create many-to-many association table for strategies and codes
CREATE TABLE IF NOT EXISTS strategy_codes (
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    code_id INTEGER REFERENCES codes(id) ON DELETE CASCADE,
    PRIMARY KEY (strategy_id, code_id)
);

-- Workflow symbols table
CREATE TABLE IF NOT EXISTS workflow_symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    workflow_type VARCHAR(50) DEFAULT 'trading_signal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_workflow_symbols_enabled ON workflow_symbols(enabled);
CREATE INDEX IF NOT EXISTS idx_workflow_symbols_priority ON workflow_symbols(priority DESC);

-- Workflow-specific scheduling association table
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_symbol_workflow_link_pair
    ON symbol_workflow_links (workflow_symbol_id, workflow_id);

CREATE INDEX IF NOT EXISTS idx_symbol_workflow_links_symbol_priority
    ON symbol_workflow_links (workflow_symbol_id, priority);

-- Indicators table for technical indicator configurations
CREATE TABLE IF NOT EXISTS indicators (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- MA, RSI, MACD, BB, SuperTrend, ATR, etc.
    parameters JSONB NOT NULL,  -- Indicator-specific parameters
    period INTEGER DEFAULT 100,  -- Number of data points for chart (20-500)
    frequency VARCHAR(10) DEFAULT '1D',  -- Data frequency: 1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W, 1M
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Strategy-Indicator junction table (many-to-many)
CREATE TABLE IF NOT EXISTS strategy_indicators (
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    indicator_id INTEGER REFERENCES indicators(id) ON DELETE CASCADE,
    display_order INTEGER DEFAULT 0,  -- Order for chart layering
    PRIMARY KEY (strategy_id, indicator_id)
);

-- Indicator Charts table for storing generated chart metadata and references
CREATE TABLE IF NOT EXISTS indicator_charts (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    indicator_ids INTEGER[] NOT NULL,  -- Array of indicator IDs used in chart
    period INTEGER NOT NULL,  -- Number of data points used
    frequency VARCHAR(10) NOT NULL,  -- Data frequency used
    chart_url_jpeg VARCHAR(500),  -- MinIO URL for JPEG chart
    chart_url_html VARCHAR(500),  -- MinIO URL for interactive HTML chart
    metadata JSONB DEFAULT '{}',  -- Additional metadata (file sizes, generation time, etc.)
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE  -- Auto-delete date (30 days default)
);

-- Legacy compatibility views (optional, if needed)
CREATE OR REPLACE VIEW workflow AS SELECT * FROM workflows;
CREATE OR REPLACE VIEW strategy AS SELECT * FROM strategies;

-- Create market_data table
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    date TIMESTAMP NOT NULL,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, timeframe, date)
);

-- Create decisions table (following SQLAlchemy naming)
CREATE TABLE IF NOT EXISTS decisions (
    id SERIAL PRIMARY KEY,
    code_id INTEGER REFERENCES codes(id) ON DELETE SET NULL,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    current_price FLOAT,
    target_price FLOAT,
    stop_loss FLOAT,
    profit_margin FLOAT,
    r_coefficient FLOAT,
    analysis_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Legacy compatibility view
CREATE OR REPLACE VIEW decision AS SELECT * FROM decisions;

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    decision_id INTEGER REFERENCES decisions(id) ON DELETE SET NULL,
    conid INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    type VARCHAR(10) NOT NULL,
    order_type VARCHAR(10) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    price DECIMAL(10, 2),
    status VARCHAR(20) NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    ibkr_order_id VARCHAR(100)
);

-- Create trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    conid INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    commission DECIMAL(10, 2),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ibkr_execution_id VARCHAR(100)
);

-- Create positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    conid INTEGER NOT NULL,
    code VARCHAR(50) NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    avg_price DECIMAL(10, 2) NOT NULL,
    market_price DECIMAL(10, 2),
    unrealized_pnl DECIMAL(10, 2),
    realized_pnl DECIMAL(10, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, conid)
);

-- Create workflow_executions table (following SQLAlchemy naming)
CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    task_id VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    result JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create agent_conversations table (following SQLAlchemy naming)
CREATE TABLE IF NOT EXISTS agent_conversations (
    id SERIAL PRIMARY KEY,
    workflow_execution_id INTEGER REFERENCES workflow_executions(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER
);

-- Legacy compatibility view
CREATE OR REPLACE VIEW agent_conversation AS 
    SELECT id, workflow_execution_id, agent_name, message_content as message, 
           jsonb_build_object() as metadata, timestamp as created_at 
    FROM agent_conversations;

-- Create workflow_logs table for comprehensive I/O logging
CREATE TABLE IF NOT EXISTS workflow_logs (
    id SERIAL PRIMARY KEY,
    workflow_execution_id INTEGER REFERENCES workflow_executions(id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    step_type VARCHAR(50) NOT NULL,  -- fetch_data, ai_analysis, decision, order, etc.
    code VARCHAR(50),
    conid INTEGER,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_codes_symbol ON codes(symbol);
CREATE INDEX idx_codes_conid ON codes(conid);
CREATE INDEX idx_strategies_active ON strategies(active);
CREATE INDEX idx_market_data_code_timeframe ON market_data(code, timeframe, date DESC);
CREATE INDEX idx_decisions_strategy ON decisions(strategy_id, created_at DESC);
CREATE INDEX idx_decisions_code ON decisions(code_id);
CREATE INDEX idx_orders_strategy ON orders(strategy_id, submitted_at DESC);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_trades_code ON trades(code, executed_at DESC);
CREATE INDEX idx_positions_account ON positions(account_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status, started_at DESC);
CREATE INDEX idx_workflow_logs_execution ON workflow_logs(workflow_execution_id, created_at DESC);
CREATE INDEX idx_workflow_logs_step ON workflow_logs(step_name, step_type);
CREATE INDEX idx_workflow_logs_code ON workflow_logs(code, conid);
CREATE INDEX idx_indicator_charts_strategy ON indicator_charts(strategy_id, generated_at DESC);
CREATE INDEX idx_indicator_charts_symbol ON indicator_charts(symbol, generated_at DESC);
CREATE INDEX idx_indicator_charts_expires ON indicator_charts(expires_at);

-- Insert default workflow
INSERT INTO workflows (name, type, description, steps, default_params) 
VALUES (
    'Two Indicator Strategy',
    'two_indicator',
    'Default two-indicator trading workflow with SuperTrend and Moving Averages',
    '[
        {"step": "authenticate", "name": "Authenticate IBKR"},
        {"step": "fetch_data", "name": "Fetch Market Data"},
        {"step": "analyze_daily", "name": "Analyze Daily Chart"},
        {"step": "analyze_weekly", "name": "Analyze Weekly Chart"},
        {"step": "consolidate", "name": "Consolidate Analysis"},
        {"step": "make_decision", "name": "Generate Trading Decision"},
        {"step": "place_order", "name": "Place Order"}
    ]'::jsonb,
    '{"risk_per_trade": 0.02, "account_size": 100000}'::jsonb
) ON CONFLICT (name) DO NOTHING;

-- Add comments
COMMENT ON TABLE workflows IS 'Workflow templates for trading strategies';
COMMENT ON TABLE codes IS 'Financial instrument definitions (symbol, conid, exchange)';
COMMENT ON TABLE strategies IS 'Trading strategies configuration';
COMMENT ON TABLE strategy_codes IS 'Many-to-many association between strategies and codes';
COMMENT ON TABLE market_data IS 'Historical market data cache';
COMMENT ON TABLE decisions IS 'AI-generated trading decisions';
COMMENT ON TABLE orders IS 'Order history';
COMMENT ON TABLE trades IS 'Executed trades';
COMMENT ON TABLE positions IS 'Current portfolio positions';
COMMENT ON TABLE workflow_executions IS 'Workflow execution history';
COMMENT ON TABLE agent_conversations IS 'AutoGen agent conversation logs';
COMMENT ON TABLE workflow_logs IS 'Comprehensive workflow step I/O logging';
