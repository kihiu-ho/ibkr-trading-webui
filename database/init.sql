-- Initialize database schema for IBKR Trading Platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create workflow table
CREATE TABLE IF NOT EXISTS workflow (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    steps JSONB NOT NULL DEFAULT '[]',
    default_params JSONB DEFAULT '{}',
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create strategy table
CREATE TABLE IF NOT EXISTS strategy (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL,
    workflow_id INTEGER REFERENCES workflow(id) ON DELETE SET NULL,
    param JSONB DEFAULT '{}',
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- Create decision table
CREATE TABLE IF NOT EXISTS decision (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategy(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    type VARCHAR(10) NOT NULL,
    current_price DECIMAL(10, 2),
    target_price DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    profit_margin DECIMAL(5, 4),
    r_coefficient DECIMAL(5, 2),
    analysis_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategy(id) ON DELETE CASCADE,
    decision_id INTEGER REFERENCES decision(id) ON DELETE SET NULL,
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

-- Create workflow_execution table
CREATE TABLE IF NOT EXISTS workflow_execution (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflow(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategy(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    result JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create agent_conversation table
CREATE TABLE IF NOT EXISTS agent_conversation (
    id SERIAL PRIMARY KEY,
    workflow_execution_id INTEGER REFERENCES workflow_execution(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_strategy_code ON strategy(code);
CREATE INDEX idx_strategy_active ON strategy(active);
CREATE INDEX idx_market_data_code_timeframe ON market_data(code, timeframe, date DESC);
CREATE INDEX idx_decision_strategy ON decision(strategy_id, created_at DESC);
CREATE INDEX idx_orders_strategy ON orders(strategy_id, submitted_at DESC);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_trades_code ON trades(code, executed_at DESC);
CREATE INDEX idx_positions_account ON positions(account_id);
CREATE INDEX idx_workflow_execution_status ON workflow_execution(status, started_at DESC);

-- Insert default workflow
INSERT INTO workflow (name, description, steps, default_params) 
VALUES (
    'Two Indicator Strategy',
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
COMMENT ON TABLE workflow IS 'Workflow templates for trading strategies';
COMMENT ON TABLE strategy IS 'Trading strategies configuration';
COMMENT ON TABLE market_data IS 'Historical market data cache';
COMMENT ON TABLE decision IS 'AI-generated trading decisions';
COMMENT ON TABLE orders IS 'Order history';
COMMENT ON TABLE trades IS 'Executed trades';
COMMENT ON TABLE positions IS 'Current portfolio positions';
COMMENT ON TABLE workflow_execution IS 'Workflow execution history';
COMMENT ON TABLE agent_conversation IS 'AutoGen agent conversation logs';

