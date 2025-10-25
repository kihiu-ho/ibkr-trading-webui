# Configurable Prompt System - User Guide

## Overview

The Configurable Prompt System allows you to manage, customize, and track the performance of LLM prompts used for trading signal generation. No code changes needed - all prompt modifications are done through the database and API.

## Table of Contents

1. [Key Concepts](#key-concepts)
2. [Getting Started](#getting-started)
3. [Managing Prompts](#managing-prompts)
4. [Writing Jinja2 Templates](#writing-jinja2-templates)
5. [Strategy-Specific Prompts](#strategy-specific-prompts)
6. [Performance Tracking](#performance-tracking)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Key Concepts

### Prompt Templates

- **Template Types**: `analysis`, `consolidation`, `system_message`
- **Languages**: `en` (English), `zh` (Traditional Chinese)
- **Scope**: Global (strategy_id = NULL) or Strategy-Specific
- **Versioning**: Automatic version increment on text changes
- **Default**: One default template per type/language/strategy combination

### Prompt Lookup Order

1. **Strategy-Specific**: Check for active prompt with matching strategy_id
2. **Global Fallback**: If no strategy-specific, use global default
3. **Hardcoded Fallback**: If database fails, use embedded fallback

### Performance Metrics

Daily aggregation of:
- Signals generated/executed
- Win/Loss counts and rates
- R-multiples (avg, best, worst)
- Profit/Loss totals
- Confidence averages

---

## Getting Started

### 1. Seed Default Prompts

Run the migration to load 6 default templates:

```bash
psql $DATABASE_URL -f database/migrations/seed_prompt_templates.sql
```

### 2. Verify Templates

```bash
curl http://localhost:8000/api/v1/prompts/ | jq
```

You should see 6 templates:
- Daily Chart Analysis (Chinese)
- Weekly Chart Trend Confirmation (Chinese)
- Multi-Timeframe Consolidation (Chinese)
- 3 System Messages

### 3. Test Signal Generation

Signals will now automatically use database prompts with full traceability.

---

## Managing Prompts

### List All Prompts

```bash
GET /api/v1/prompts/
```

**Filters**:
- `template_type` - Filter by type
- `language` - en or zh
- `strategy_id` - 0 for global, specific ID for strategy
- `is_active` - true/false
- `is_default` - true/false
- `tags` - Array of tags
- `page`, `page_size` - Pagination

**Example**:
```bash
curl "http://localhost:8000/api/v1/prompts/?template_type=analysis&language=zh&is_active=true"
```

### Get Single Prompt

```bash
GET /api/v1/prompts/{id}
```

### Create New Prompt

```bash
POST /api/v1/prompts/
Content-Type: application/json

{
  "name": "Aggressive Day Trading Analysis",
  "description": "For short-term day trading strategies",
  "prompt_text": "{{ prompt_text_here }}",
  "template_type": "analysis",
  "language": "en",
  "strategy_id": null,
  "is_active": true,
  "is_default": false,
  "tags": ["day-trading", "aggressive", "short-term"],
  "notes": "Focuses on intraday patterns"
}
```

### Update Existing Prompt

```bash
PUT /api/v1/prompts/{id}
Content-Type: application/json

{
  "prompt_text": "{{ updated_text }}",
  "notes": "Updated for better risk assessment"
}
```

**Note**: Updating `prompt_text` automatically increments `template_version`.

### Set as Default

```bash
PUT /api/v1/prompts/{id}
Content-Type: application/json

{
  "is_default": true
}
```

Previous default for same type/language/strategy will be automatically unset.

### Deactivate Prompt

```bash
PUT /api/v1/prompts/{id}
Content-Type: application/json

{
  "is_active": false
}
```

**Note**: Cannot delete prompts that have generated signals. Deactivate instead.

---

## Writing Jinja2 Templates

### Basic Syntax

```jinja2
Analysis Date: {{ now.strftime("%Y-%m-%d %H:%M:%S") }}

# Analysis for {{ symbol }}

Current Price: {{ current_price|round(2) }}
```

### Available Variables

**Always Available**:
- `now` - Current datetime
- `today` - Current date
- `symbol` - Stock symbol
- `exchange` - Exchange name (optional)

**Analysis Context**:
- `current_price` - Latest price
- `timeframe` - Chart timeframe (1d, 1w, etc.)
- `open`, `high`, `low`, `close`, `volume` - OHLCV data
- `atr`, `rsi`, `macd`, `supertrend`, `ma20`, `ma50`, `ma200`, `bollinger` - Indicators
- `strategy` - Strategy parameters dict
- `previous_analyses` - Previous analysis results

**Consolidation Context**:
- `analysis_daily` - Daily analysis text
- `analysis_weekly` - Weekly analysis text

### Custom Filters

**Number Formatting**:
```jinja2
{{ current_price|round(2) }}  → 150.75
{{ change|abs }}  → 5.5
{{ return_rate|percent(1) }}  → 5.5%
{{ price|currency('$', 2) }}  → $150.75
```

**Date Formatting**:
```jinja2
{{ now|date('%Y-%m-%d') }}  → 2025-10-25
{{ now|datetime('%Y-%m-%d %H:%M') }}  → 2025-10-25 14:30
```

**String Operations**:
```jinja2
{{ symbol|upper }}  → AAPL
{{ trend|lower }}  → bullish
{{ name|title }}  → Apple Inc
{{ text|trim }}  → (removes whitespace)
```

**List Operations**:
```jinja2
{{ tags|join(', ') }}  → tech, growth, momentum
{{ previous_analyses|first }}  → First item
{{ previous_analyses|last }}  → Last item
```

**Technical Analysis**:
```jinja2
{{ trend|trend_label }}  → 強烈看漲 (for Chinese)
{{ signal|signal_label }}  → 買入
```

### Conditionals

```jinja2
{% if current_price > ma20 %}
價格突破20日均線，顯示多頭力道
{% elif current_price < ma50 %}
跌破50日均線，需要警惕
{% else %}
價格在關鍵均線之間盤整
{% endif %}
```

### Loops

```jinja2
## 前期分析回顧
{% for analysis in previous_analyses %}
- {{ analysis.timeframe }}: {{ analysis.result[:100] }}...
{% endfor %}
```

### Macros (Reusable Blocks)

```jinja2
{% macro risk_warning(risk_level) %}
⚠️ 風險等級: {{ risk_level }}
{% endmacro %}

{{ risk_warning("高") }}
```

### Example Template

```jinja2
Analysis Date: {{ now.strftime("%Y-%m-%d %H:%M:%S") }}

# Technical Analysis for {{ symbol }}

## Current Market Status
- Price: {{ current_price|currency('$') }}{% if atr %} (ATR: {{ atr|round(2) }}){% endif %}
- Timeframe: {{ timeframe|upper }}

## Trend Assessment
{% if trend == 'bullish' %}
目前趨勢：看漲 🟢
建議：尋找回檔進場機會
{% elif trend == 'bearish' %}
目前趨勢：看跌 🔴
建議：等待反彈出場
{% else %}
目前趨勢：盤整
建議：觀望為主
{% endif %}

## Technical Indicators
{% if rsi %}
- RSI(14): {{ rsi|round(1) }}{% if rsi > 70 %} - 超買區域⚠️{% elif rsi < 30 %} - 超賣區域⚡{% endif %}
{% endif %}

{% if strategy %}
## Strategy Parameters
Period: {{ strategy.period }}
Risk per Trade: {{ strategy.risk_per_trade|percent }}%
{% endif %}
```

---

## Strategy-Specific Prompts

### Why Use Strategy-Specific Prompts?

Different trading strategies need different analysis focus:
- **Day Trading**: Intraday patterns, volume spikes
- **Swing Trading**: Multi-day trends, support/resistance
- **Long-Term**: Fundamentals, macro trends

### Creating Strategy Prompt

```bash
POST /api/v1/prompts/strategy/{strategy_id}
Content-Type: application/json

{
  "name": "Day Trading - 1-minute Scalping",
  "description": "Ultra-short-term momentum analysis",
  "prompt_text": "{{ template }}",
  "template_type": "analysis",
  "language": "zh",
  "is_active": true,
  "is_default": true,
  "tags": ["scalping", "1min", "high-frequency"]
}
```

### Listing Strategy Prompts

```bash
GET /api/v1/prompts/strategy/{strategy_id}?include_global=true
```

Returns both strategy-specific and global defaults.

### Override Behavior

- Strategy-specific prompts **override** global defaults
- Fallback to global if no strategy-specific active
- Set `is_default=true` to make it the default for that strategy

---

## Performance Tracking

### How It Works

1. **Signal Generation**: Every signal stores `prompt_template_id` and `prompt_version`
2. **Outcome Tracking**: Update signal outcomes (win/loss) via API
3. **Daily Aggregation**: Celery task runs at 1 AM UTC to calculate metrics
4. **API Queries**: Retrieve performance data for analysis

### Updating Signal Outcomes

```bash
PUT /api/v1/prompts/signals/{signal_id}/outcome
Content-Type: application/json

{
  "outcome": "win",
  "exit_price": 155.50,
  "exit_time": "2025-10-26T15:30:00Z",
  "actual_r_multiple": 2.5,
  "profit_loss": 550.00
}
```

**Outcome Values**: `win`, `loss`, `pending`, `cancelled`

### Get Prompt Performance

```bash
GET /api/v1/prompts/{id}/performance?start_date=2025-10-01&end_date=2025-10-31
```

**Response**:
```json
[
  {
    "date": "2025-10-25",
    "signals_generated": 10,
    "signals_executed": 8,
    "win_count": 6,
    "loss_count": 2,
    "win_rate": 0.75,
    "avg_r_multiple": 1.8,
    "total_profit_loss": 2500.00
  }
]
```

### Compare Multiple Prompts

```bash
POST /api/v1/prompts/compare
Content-Type: application/json

{
  "prompt_template_ids": [1, 2, 3],
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "metric": "avg_r_multiple"
}
```

**Metrics**: `avg_r_multiple`, `win_rate`, `total_profit_loss`

### Leaderboard

```bash
POST /api/v1/prompts/leaderboard
Content-Type: application/json

{
  "metric": "avg_r_multiple",
  "limit": 10,
  "start_date": "2025-10-01",
  "template_type": "analysis"
}
```

Returns top N prompts by selected metric.

### Manual Calculation

Trigger performance calculation manually:

```bash
# Calculate for specific date
POST /api/v1/prompts/performance/calculate
Content-Type: application/json

{
  "date": "2025-10-25"
}
```

### Backfill Historical Data

```python
from backend.tasks.prompt_performance_tasks import calculate_prompt_performance_range

# Calculate for date range
result = calculate_prompt_performance_range.delay("2025-09-01", "2025-10-31")
```

---

## API Reference

### Endpoints Summary

**CRUD**:
- `POST   /api/v1/prompts/` - Create
- `GET    /api/v1/prompts/` - List (with filters)
- `GET    /api/v1/prompts/{id}` - Get single
- `PUT    /api/v1/prompts/{id}` - Update
- `DELETE /api/v1/prompts/{id}` - Delete

**Strategy-Specific**:
- `GET    /api/v1/prompts/strategy/{id}` - List strategy prompts
- `POST   /api/v1/prompts/strategy/{id}` - Create for strategy

**Performance**:
- `GET    /api/v1/prompts/{id}/performance` - Get metrics
- `POST   /api/v1/prompts/compare` - Compare prompts
- `POST   /api/v1/prompts/leaderboard` - Top performers

**Utilities**:
- `POST   /api/v1/prompts/validate` - Validate Jinja2 syntax
- `POST   /api/v1/prompts/render` - Preview rendering

**Signal Outcomes**:
- `PUT    /api/v1/prompts/signals/{id}/outcome` - Update outcome

Full API documentation: http://localhost:8000/docs

---

## Troubleshooting

### Prompt Not Being Used

**Check**:
1. Is prompt `is_active = true`?
2. Is it the default for its type/language/strategy?
3. Check logs for "Loaded prompt: ..." messages

**Solution**:
```bash
# List active defaults
curl "http://localhost:8000/api/v1/prompts/?is_active=true&is_default=true"

# Set as default
curl -X PUT "http://localhost:8000/api/v1/prompts/{id}" \
  -H "Content-Type: application/json" \
  -d '{"is_default": true}'
```

### Template Syntax Errors

**Validate Before Saving**:
```bash
POST /api/v1/prompts/validate
Content-Type: application/json

{
  "template_text": "{{ your_template }}"
}
```

**Common Errors**:
- Missing `{% endif %}` or `{% endfor %}`
- Unmatched quotes in strings
- Invalid variable names

### Performance Metrics Missing

**Causes**:
1. Signals don't have outcomes set
2. Daily task hasn't run yet
3. No signals for that date

**Solutions**:
```bash
# Check signal outcomes
SELECT outcome, COUNT(*) FROM trading_signals GROUP BY outcome;

# Manually trigger calculation
curl -X POST "http://localhost:8000/api/v1/prompts/performance/calculate"

# Check Celery Beat is running
docker logs celery-beat
```

### Prompt Cache Issues

If prompt changes aren't reflected:

**Clear Cache** (requires code access):
```python
from backend.services.llm_service import LLMService
llm = LLMService(db_session)
llm.clear_prompt_cache()
```

Or restart services:
```bash
docker-compose restart backend celery-worker
```

---

## Best Practices

1. **Version Control**: Track prompt changes in git alongside code
2. **Testing**: Use `/render` endpoint to test templates before deploying
3. **Gradual Rollout**: Create as non-default first, test, then set as default
4. **Performance Monitoring**: Review metrics weekly to identify best prompts
5. **Strategy Alignment**: Match prompt style to strategy timeframe
6. **Backup**: Export prompts before major changes
7. **Documentation**: Use `notes` field to document prompt purpose

---

## Advanced Topics

### Custom Jinja2 Filters

To add custom filters, modify `backend/services/prompt_renderer.py`:

```python
def my_custom_filter(value):
    # Your logic
    return processed_value

# In _register_filters():
self.env.filters['my_filter'] = my_custom_filter
```

### Database Direct Access

```sql
-- List all prompts
SELECT id, name, template_type, language, strategy_id, is_default, is_active
FROM prompt_templates
ORDER BY created_at DESC;

-- Get performance for specific prompt
SELECT * FROM prompt_performance
WHERE prompt_template_id = 1
ORDER BY date DESC;

-- Top performing prompts
SELECT 
  pt.name,
  AVG(pp.avg_r_multiple) as avg_r,
  SUM(pp.win_count) as total_wins,
  SUM(pp.loss_count) as total_losses
FROM prompt_performance pp
JOIN prompt_templates pt ON pp.prompt_template_id = pt.id
GROUP BY pt.id, pt.name
ORDER BY avg_r DESC;
```

---

## Support

- **Issues**: https://github.com/your-repo/issues
- **Documentation**: `/docs`
- **API Docs**: http://localhost:8000/docs
- **OpenSpec**: `openspec/changes/add-configurable-prompt-system/`

---

**Last Updated**: 2025-10-25
**Version**: 1.0.0

