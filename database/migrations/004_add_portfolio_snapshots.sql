-- Migration: Add Portfolio Snapshots Table
-- Date: 2025-10-25
-- Description: Creates portfolio_snapshots table for historical portfolio tracking

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    cash_balance DECIMAL(18, 4) NOT NULL DEFAULT 0.0,
    portfolio_value DECIMAL(18, 4) NOT NULL DEFAULT 0.0,
    total_value DECIMAL(18, 4) NOT NULL DEFAULT 0.0,
    realized_pnl DECIMAL(18, 4) NOT NULL DEFAULT 0.0,
    unrealized_pnl DECIMAL(18, 4) NOT NULL DEFAULT 0.0,
    snapshot_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_user_id ON portfolio_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_snapshot_at ON portfolio_snapshots(snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_user_date ON portfolio_snapshots(user_id, snapshot_at DESC);

COMMENT ON TABLE portfolio_snapshots IS 'Historical snapshots of user portfolio for tracking performance over time';
COMMENT ON COLUMN portfolio_snapshots.total_value IS 'cash_balance + portfolio_value';
COMMENT ON COLUMN portfolio_snapshots.realized_pnl IS 'Total P&L from closed trades';
COMMENT ON COLUMN portfolio_snapshots.unrealized_pnl IS 'Total P&L from open positions';

