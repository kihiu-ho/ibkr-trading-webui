-- Migration: Add Configurable Prompt Template System
-- Date: 2025-10-25
-- Description: Adds prompt_templates and prompt_performance tables with Jinja2 support and strategy-specific prompts

-- Create prompt_templates table
CREATE TABLE IF NOT EXISTS prompt_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Template content
    prompt_text TEXT NOT NULL,  -- Full Jinja2 template
    template_version INTEGER NOT NULL DEFAULT 1,
    
    -- Categorization
    template_type VARCHAR(50) NOT NULL DEFAULT 'analysis',  -- analysis, consolidation, decision
    language VARCHAR(5) NOT NULL DEFAULT 'en',  -- en, zh
    
    -- Strategy association
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,  -- NULL = global default
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,  -- Only one default per type+language+strategy combination
    
    -- Metadata
    created_by VARCHAR(100),
    tags VARCHAR(255)[],  -- Array for categorization
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_default_prompt UNIQUE (template_type, language, strategy_id, is_default) DEFERRABLE INITIALLY DEFERRED
);

-- Create prompt_performance table for tracking prompt effectiveness
CREATE TABLE IF NOT EXISTS prompt_performance (
    id SERIAL PRIMARY KEY,
    
    -- Prompt identification
    prompt_template_id INTEGER NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    
    -- Time period
    date DATE NOT NULL,
    
    -- Signal counts
    signals_generated INTEGER NOT NULL DEFAULT 0,
    signals_executed INTEGER NOT NULL DEFAULT 0,
    
    -- Financial metrics
    total_profit_loss DECIMAL(15, 2),
    
    -- Win/Loss tracking
    win_count INTEGER NOT NULL DEFAULT 0,
    loss_count INTEGER NOT NULL DEFAULT 0,
    
    -- R-Multiple statistics
    avg_r_multiple DECIMAL(10, 4),
    best_r_multiple DECIMAL(10, 4),
    worst_r_multiple DECIMAL(10, 4),
    
    -- Percentage returns
    avg_profit_pct DECIMAL(10, 4),
    avg_loss_pct DECIMAL(10, 4),
    
    -- Confidence metrics
    avg_confidence DECIMAL(5, 4),
    
    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_prompt_performance_date UNIQUE (prompt_template_id, strategy_id, date)
);

-- Extend trading_signals table with prompt tracking columns
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS prompt_template_id INTEGER REFERENCES prompt_templates(id) ON DELETE SET NULL;
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS prompt_version INTEGER;
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS prompt_type VARCHAR(50);  -- Which prompt was used (analysis_daily, analysis_weekly, consolidation)

-- Add outcome tracking columns to trading_signals for performance aggregation
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS outcome VARCHAR(20);  -- 'win', 'loss', 'pending', 'cancelled'
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS actual_r_multiple DECIMAL(10, 4);  -- Realized R-multiple
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS profit_loss DECIMAL(15, 2);  -- Realized P/L
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS exit_price DECIMAL(10, 4);
ALTER TABLE trading_signals ADD COLUMN IF NOT EXISTS exit_time TIMESTAMP WITH TIME ZONE;

-- Create indexes for prompt_templates
CREATE INDEX IF NOT EXISTS idx_prompt_templates_type ON prompt_templates(template_type, language);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_strategy ON prompt_templates(strategy_id) WHERE strategy_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_prompt_templates_active ON prompt_templates(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_prompt_templates_default ON prompt_templates(is_default, template_type, language, strategy_id) WHERE is_default = TRUE;
CREATE INDEX IF NOT EXISTS idx_prompt_templates_tags ON prompt_templates USING GIN(tags);  -- For array search

-- Create indexes for prompt_performance
CREATE INDEX IF NOT EXISTS idx_prompt_performance_prompt_date ON prompt_performance(prompt_template_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_performance_strategy ON prompt_performance(strategy_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_performance_date ON prompt_performance(date DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_performance_r_multiple ON prompt_performance(avg_r_multiple DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_prompt_performance_win_rate ON prompt_performance((CASE WHEN (win_count + loss_count) > 0 THEN win_count::DECIMAL / (win_count + loss_count) ELSE 0 END) DESC);

-- Create indexes for trading_signals prompt tracking
CREATE INDEX IF NOT EXISTS idx_trading_signals_prompt_template ON trading_signals(prompt_template_id) WHERE prompt_template_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trading_signals_outcome ON trading_signals(outcome, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_trading_signals_prompt_outcome ON trading_signals(prompt_template_id, outcome) WHERE outcome IN ('win', 'loss');

-- Add comments
COMMENT ON TABLE prompt_templates IS 'Stores configurable Jinja2 prompt templates for LLM analysis, with strategy-specific overrides';
COMMENT ON TABLE prompt_performance IS 'Aggregated daily performance metrics per prompt template for data-driven optimization';
COMMENT ON COLUMN prompt_templates.prompt_text IS 'Full Jinja2 template with filters, conditionals, loops';
COMMENT ON COLUMN prompt_templates.strategy_id IS 'NULL for global defaults, specific ID for strategy overrides';
COMMENT ON COLUMN prompt_templates.is_default IS 'Only one default per (type, language, strategy) combination';
COMMENT ON COLUMN prompt_performance.avg_r_multiple IS 'Average risk-reward multiple (target-entry)/(entry-stop)';
COMMENT ON COLUMN trading_signals.prompt_template_id IS 'Which prompt template generated this signal';
COMMENT ON COLUMN trading_signals.prompt_version IS 'Template version at generation time for audit trail';
COMMENT ON COLUMN trading_signals.outcome IS 'Signal outcome: win, loss, pending, cancelled';
COMMENT ON COLUMN trading_signals.actual_r_multiple IS 'Realized R-multiple based on actual exit';

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_prompt_templates_updated_at 
    BEFORE UPDATE ON prompt_templates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_performance_updated_at 
    BEFORE UPDATE ON prompt_performance 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

