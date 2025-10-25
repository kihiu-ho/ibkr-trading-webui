-- Setup Test Strategy with TSLA and NVDA for Workflow Testing
-- This script creates the necessary test data for workflow execution

-- Insert TSLA code
INSERT INTO codes (symbol, conid, exchange, name, created_at, updated_at)
VALUES ('TSLA', 76792991, 'NASDAQ', 'Tesla Inc', NOW(), NOW())
ON CONFLICT (conid) DO UPDATE 
SET symbol = EXCLUDED.symbol, 
    exchange = EXCLUDED.exchange, 
    name = EXCLUDED.name,
    updated_at = NOW();

-- Insert NVDA code
INSERT INTO codes (symbol, conid, exchange, name, created_at, updated_at)
VALUES ('NVDA', 4815747, 'NASDAQ', 'NVIDIA Corporation', NOW(), NOW())
ON CONFLICT (conid) DO UPDATE 
SET symbol = EXCLUDED.symbol, 
    exchange = EXCLUDED.exchange, 
    name = EXCLUDED.name,
    updated_at = NOW();

-- Get the workflow ID for "Two Indicator Strategy"
DO $$
DECLARE
    workflow_id_var INTEGER;
    strategy_id_var INTEGER;
    tsla_id INTEGER;
    nvda_id INTEGER;
BEGIN
    -- Get workflow ID
    SELECT id INTO workflow_id_var FROM workflows WHERE name = 'Two Indicator Strategy';
    
    IF workflow_id_var IS NULL THEN
        RAISE EXCEPTION 'Workflow "Two Indicator Strategy" not found. Please run init.sql first.';
    END IF;
    
    -- Get code IDs
    SELECT id INTO tsla_id FROM codes WHERE conid = 76792991;
    SELECT id INTO nvda_id FROM codes WHERE conid = 4815747;
    
    -- Create or update test strategy
    INSERT INTO strategies (name, workflow_id, type, param, active, created_at, updated_at)
    VALUES (
        'Test Multi-Code Strategy - TSLA & NVDA',
        workflow_id_var,
        'two_indicator',
        '{"period_1": "1y", "bar_1": "1d", "period_2": "5y", "bar_2": "1w", "risk_per_trade": 0.02, "account_size": 100000}'::jsonb,
        1,
        NOW(),
        NOW()
    )
    ON CONFLICT (name) DO UPDATE
    SET workflow_id = EXCLUDED.workflow_id,
        param = EXCLUDED.param,
        updated_at = NOW()
    RETURNING id INTO strategy_id_var;
    
    -- Associate TSLA with strategy
    INSERT INTO strategy_codes (strategy_id, code_id)
    VALUES (strategy_id_var, tsla_id)
    ON CONFLICT DO NOTHING;
    
    -- Associate NVDA with strategy
    INSERT INTO strategy_codes (strategy_id, code_id)
    VALUES (strategy_id_var, nvda_id)
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'Test strategy created with ID: %', strategy_id_var;
    RAISE NOTICE 'Associated codes: TSLA (%), NVDA (%)', tsla_id, nvda_id;
END $$;

-- Display the created strategy
SELECT 
    s.id,
    s.name,
    s.type,
    s.workflow_id,
    w.name as workflow_name,
    s.param,
    COUNT(sc.code_id) as num_codes
FROM strategies s
JOIN workflows w ON s.workflow_id = w.id
LEFT JOIN strategy_codes sc ON s.id = sc.strategy_id
WHERE s.name = 'Test Multi-Code Strategy - TSLA & NVDA'
GROUP BY s.id, s.name, s.type, s.workflow_id, w.name, s.param;

-- Display associated codes
SELECT 
    s.name as strategy_name,
    c.symbol,
    c.conid,
    c.exchange,
    c.name as company_name
FROM strategies s
JOIN strategy_codes sc ON s.id = sc.strategy_id
JOIN codes c ON sc.code_id = c.id
WHERE s.name = 'Test Multi-Code Strategy - TSLA & NVDA'
ORDER BY c.symbol;

