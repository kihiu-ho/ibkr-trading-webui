-- Query Workflow Execution Logs
-- This script displays comprehensive I/O logging from workflow executions

-- ==============================================================================
-- 1. Show recent workflow executions
-- ==============================================================================
SELECT 
    we.id as execution_id,
    we.status,
    s.name as strategy_name,
    w.name as workflow_name,
    we.started_at,
    we.completed_at,
    EXTRACT(EPOCH FROM (we.completed_at - we.started_at)) as duration_seconds,
    we.error
FROM workflow_executions we
JOIN strategies s ON we.strategy_id = s.id
JOIN workflows w ON we.workflow_id = w.id
ORDER BY we.started_at DESC
LIMIT 10;

-- ==============================================================================
-- 2. Show detailed logs for latest execution
-- ==============================================================================
WITH latest_execution AS (
    SELECT id FROM workflow_executions ORDER BY started_at DESC LIMIT 1
)
SELECT 
    wl.id,
    wl.workflow_execution_id,
    wl.step_name,
    wl.step_type,
    wl.code,
    wl.conid,
    wl.success,
    wl.duration_ms,
    wl.created_at,
    wl.input_data,
    wl.output_data,
    wl.error_message
FROM workflow_logs wl
WHERE wl.workflow_execution_id = (SELECT id FROM latest_execution)
ORDER BY wl.created_at ASC;

-- ==============================================================================
-- 3. Summary statistics for latest execution
-- ==============================================================================
WITH latest_execution AS (
    SELECT id FROM workflow_executions ORDER BY started_at DESC LIMIT 1
)
SELECT 
    wl.step_type,
    wl.code,
    COUNT(*) as total_steps,
    SUM(CASE WHEN wl.success THEN 1 ELSE 0 END) as successful_steps,
    SUM(CASE WHEN NOT wl.success THEN 1 ELSE 0 END) as failed_steps,
    AVG(wl.duration_ms) as avg_duration_ms,
    MAX(wl.duration_ms) as max_duration_ms,
    MIN(wl.duration_ms) as min_duration_ms
FROM workflow_logs wl
WHERE wl.workflow_execution_id = (SELECT id FROM latest_execution)
GROUP BY wl.step_type, wl.code
ORDER BY wl.code, wl.step_type;

-- ==============================================================================
-- 4. Show I/O for specific step type (e.g., AI analysis)
-- ==============================================================================
WITH latest_execution AS (
    SELECT id FROM workflow_executions ORDER BY started_at DESC LIMIT 1
)
SELECT 
    wl.step_name,
    wl.code,
    wl.conid,
    wl.duration_ms,
    wl.input_data->>'symbol' as symbol,
    wl.input_data->>'chart_url' as chart_url,
    LENGTH(wl.output_data->>'analysis_preview') as analysis_length,
    wl.created_at
FROM workflow_logs wl
WHERE wl.workflow_execution_id = (SELECT id FROM latest_execution)
  AND wl.step_type = 'ai_analysis'
ORDER BY wl.created_at ASC;

-- ==============================================================================
-- 5. Show decision outputs
-- ==============================================================================
WITH latest_execution AS (
    SELECT id FROM workflow_executions ORDER BY started_at DESC LIMIT 1
)
SELECT 
    wl.code,
    wl.conid,
    wl.output_data->>'type' as decision_type,
    wl.output_data->>'current_price' as current_price,
    wl.output_data->>'target_price' as target_price,
    wl.output_data->>'stop_loss' as stop_loss,
    wl.output_data->>'profit_margin' as profit_margin,
    wl.output_data->>'R_coefficient' as r_coefficient,
    wl.created_at
FROM workflow_logs wl
WHERE wl.workflow_execution_id = (SELECT id FROM latest_execution)
  AND wl.step_name = 'generate_decision'
ORDER BY wl.code;

-- ==============================================================================
-- 6. Show order placement results
-- ==============================================================================
WITH latest_execution AS (
    SELECT id FROM workflow_executions ORDER BY started_at DESC LIMIT 1
)
SELECT 
    wl.code,
    wl.conid,
    wl.success,
    wl.input_data->>'side' as side,
    wl.input_data->>'quantity' as quantity,
    wl.output_data->>'order_id' as order_id,
    wl.output_data->>'ibkr_order_id' as ibkr_order_id,
    wl.output_data->>'status' as order_status,
    wl.error_message,
    wl.created_at
FROM workflow_logs wl
WHERE wl.workflow_execution_id = (SELECT id FROM latest_execution)
  AND wl.step_type = 'order'
ORDER BY wl.code;

-- ==============================================================================
-- 7. Show full timeline for a specific code (e.g., TSLA)
-- ==============================================================================
WITH latest_execution AS (
    SELECT id FROM workflow_executions ORDER BY started_at DESC LIMIT 1
)
SELECT 
    wl.created_at,
    wl.step_name,
    wl.step_type,
    wl.success,
    wl.duration_ms,
    CASE 
        WHEN wl.duration_ms IS NOT NULL THEN CONCAT(ROUND(wl.duration_ms::numeric/1000, 2), 's')
        ELSE 'N/A'
    END as duration_str,
    CASE 
        WHEN wl.success THEN '✓'
        ELSE '✗'
    END as status
FROM workflow_logs wl
WHERE wl.workflow_execution_id = (SELECT id FROM latest_execution)
  AND wl.code = 'TSLA'
ORDER BY wl.created_at ASC;

-- ==============================================================================
-- 8. Export full logs as JSON for analysis
-- ==============================================================================
WITH latest_execution AS (
    SELECT id FROM workflow_executions ORDER BY started_at DESC LIMIT 1
)
SELECT json_agg(
    json_build_object(
        'execution_id', wl.workflow_execution_id,
        'step_name', wl.step_name,
        'step_type', wl.step_type,
        'code', wl.code,
        'conid', wl.conid,
        'success', wl.success,
        'duration_ms', wl.duration_ms,
        'timestamp', wl.created_at,
        'input', wl.input_data,
        'output', wl.output_data,
        'error', wl.error_message
    ) ORDER BY wl.created_at
) as workflow_logs_json
FROM workflow_logs wl
WHERE wl.workflow_execution_id = (SELECT id FROM latest_execution);

-- ==============================================================================
-- 9. Compare performance across multiple executions
-- ==============================================================================
SELECT 
    we.id as execution_id,
    we.started_at,
    COUNT(DISTINCT wl.code) as codes_processed,
    COUNT(wl.id) as total_steps,
    SUM(CASE WHEN wl.success THEN 1 ELSE 0 END) as successful_steps,
    ROUND(AVG(wl.duration_ms)::numeric, 2) as avg_step_duration_ms,
    ROUND(SUM(wl.duration_ms)::numeric / 1000, 2) as total_duration_seconds,
    we.status
FROM workflow_executions we
LEFT JOIN workflow_logs wl ON we.id = wl.workflow_execution_id
WHERE we.started_at > NOW() - INTERVAL '24 hours'
GROUP BY we.id, we.started_at, we.status
ORDER BY we.started_at DESC;

-- ==============================================================================
-- 10. Find errors and failures
-- ==============================================================================
SELECT 
    we.id as execution_id,
    we.started_at,
    s.name as strategy_name,
    wl.code,
    wl.step_name,
    wl.step_type,
    wl.error_message,
    wl.input_data
FROM workflow_logs wl
JOIN workflow_executions we ON wl.workflow_execution_id = we.id
JOIN strategies s ON we.strategy_id = s.id
WHERE wl.success = FALSE
ORDER BY wl.created_at DESC
LIMIT 20;

