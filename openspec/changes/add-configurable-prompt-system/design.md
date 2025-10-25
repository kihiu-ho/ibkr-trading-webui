# Design Document: Configurable Prompt System

## Context

Currently, LLM prompts are hardcoded in Python service files. The system uses sophisticated prompts derived from a reference n8n workflow for multi-timeframe chart analysis. As the system evolves, we need:

- Flexibility to adjust prompts without code deployments
- Audit trail linking signals to the exact prompt version used
- Ability to roll back problematic prompts
- Support for multilingual prompts (English + Chinese)
- Easy A/B testing of prompt variations

## Goals

- **Configurability**: Non-technical users can edit prompts via web UI
- **Traceability**: Every signal is linked to its exact prompt template
- **Versioning**: Track prompt changes over time
- **Performance**: Minimal latency impact (<10ms per call)
- **Safety**: Invalid prompts can't break the system
- **Multilingual**: Support EN and ZH templates seamlessly

## Non-Goals

- Prompt template branching/merging (can add later)
- User-level prompt permissions (all admins can edit, can add later)
- Real-time prompt A/B testing (single active prompt per type/language)
- Prompt template marketplace/sharing

## Decisions

### Decision 1: Database Storage vs File-Based

**Choice**: Store prompts in PostgreSQL database

**Alternatives considered**:

- File-based (YAML/JSON in git repo)
- Hybrid (defaults in files, overrides in DB)

**Rationale**:

- Web UI editing requires database anyway
- Easier audit trail with created_at/updated_at
- No need to restart services on prompt changes
- Can leverage existing backup/restore infrastructure
- Versioning via version column + soft deletes

**Trade-offs**:

- ➕ Dynamic updates without deployment
- ➕ Built-in audit trail
- ➖ Adds database dependency to LLM calls
- ➖ Harder to track in version control (mitigated by export feature)

### Decision 2: Caching Strategy

**Choice**: In-memory cache with 5-minute TTL, invalidate on update

**Implementation**:

```python
# Simple dict cache in LLMService
_prompt_cache = {}
_cache_ttl = 300  # 5 minutes

def load_prompt(prompt_type, language):
    cache_key = f"{prompt_type}:{language}"
    cached = _prompt_cache.get(cache_key)
  
    if cached and time.time() - cached['timestamp'] < _cache_ttl:
        return cached['prompt']
  
    # Load from database
    prompt = db.query(PromptTemplate).filter(...).first()
    _prompt_cache[cache_key] = {
        'prompt': prompt,
        'timestamp': time.time()
    }
    return prompt
```

**Rationale**:

- LLM calls are already 10-60 seconds; 1-5ms DB query is negligible
- But avoid DB query on every signal (could be hundreds/day)
- 5 minutes balances freshness vs performance
- Manual invalidation via API for immediate updates

### Decision 3: Prompt Versioning Strategy

**Choice**: Simple version counter + soft deletes

**Schema**:

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    prompt_type VARCHAR(50) NOT NULL,  -- daily_chart, weekly_chart, consolidation, decision
    language VARCHAR(10) NOT NULL DEFAULT 'en',  -- en, zh
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,  -- one default per (type, language)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),  -- future: link to users table
    deleted_at TIMESTAMP NULL  -- soft delete
);
```

**Alternatives considered**:

- Git-style branching (too complex for v1)
- Separate versions table (over-engineered)
- Immutable records + parent_id chain (harder to query)

**Rationale**:

- Start simple, can add complexity if needed
- Version number auto-increments on save
- Soft deletes preserve history
- is_default flag ensures one active per type/language
- Can reconstruct history by ordering by version

### Decision 4: Prompt Template Format

**Choice**: Full Jinja2 template engine with filters, functions, and control flow

**Format**:

```jinja2
Analysis Date: {{now | date('%Y-%m-%d %H:%M')}}
Symbol: {{symbol | upper}}
Timeframe: {{timeframe}}
Strategy: {{strategy.name if strategy else "Global"}}

# Daily Chart Analysis for {{symbol}}

## 1. Core Price Analysis
Current Price: ${{current_price | round(2)}}
{% if trend == 'bullish' %}
Trend: 📈 Bullish - Price above 20 SMA
{% elif trend == 'bearish' %}
Trend: 📉 Bearish - Price below 20 SMA
{% else %}
Trend: ➡️ Neutral - Consolidating
{% endif %}

## Recent Performance (Last 3 signals)
{% for analysis in previous_analyses[:3] %}
- {{analysis.date | date('%Y-%m-%d')}}: {{analysis.signal}} → R={{analysis.r_multiple | round(1)}} ({{analysis.outcome}})
{% endfor %}

{% if volatility > 0.03 %}
⚠️ **High Volatility Warning**: ATR is {{(volatility * 100) | round(1)}}% - Consider wider stops
{% endif %}

## Daily Analysis
{{daily_analysis}}

## Weekly Analysis  
{{weekly_analysis}}
```

**Variables provided by system**:

- `now` - Current timestamp (datetime object)
- `symbol` - Stock symbol (string)
- `timeframe` - Chart timeframe: "1d", "1w" (string)
- `current_price` - Latest close price (float)
- `trend` - Current trend: "bullish", "bearish", "neutral" (string)
- `volatility` - Current ATR as % of price (float)
- `strategy` - Strategy object with `.name`, `.parameters` (object or None)
- `daily_analysis` - Daily chart LLM analysis text (string)
- `weekly_analysis` - Weekly chart LLM analysis text (string)
- `previous_analyses` - List of dicts with recent signal data (list)

**Jinja2 Filters Available**:

- `date(format)` - Format datetime objects (e.g., `'%Y-%m-%d'`)
- `round(precision)` - Round numbers (e.g., `| round(2)` → 2 decimals)
- `upper`, `lower`, `title`, `capitalize` - Text transformations
- `default(value)` - Provide fallback for None/missing values
- `length` - Get list/string length
- `join(separator)` - Join list items into string
- `abs` - Absolute value for numbers
- `int`, `float` - Type conversions

**Jinja2 Control Flow**:

- `{% if condition %}...{% endif %}` - Conditional sections
- `{% elif %}`, `{% else %}` - Multiple branches
- `{% for item in list %}...{% endfor %}` - Loops
- `{% break %}`, `{% continue %}` - Loop control
- `{% set variable = value %}` - Variable assignment
- `{% macro name(args) %}...{% endmacro %}` - Reusable template blocks

**Alternatives considered**:

- Python f-strings (too limited, no conditionals)
- Mustache templates (less powerful than Jinja2)
- Custom DSL (unnecessary complexity)

**Rationale**:

- Jinja2 already used by LangChain - zero new dependencies
- Industry standard for Python templating
- Full power for complex, dynamic prompts
- Enables conditional content (e.g., warnings only when needed)
- Support loops for historical data display
- Template macros enable DRY prompt design
- Community familiar with syntax
- Excellent debugging and error messages

### Decision 5: Frontend Tech Stack

**Choice**: React component with Monaco Editor

**Components**:

```
PromptManager
├── PromptList (table with filters)
├── PromptEditor (Monaco editor)
│   ├── Syntax highlighting
│   ├── Variable autocomplete
│   └── Preview pane
└── PromptTester (test with sample data)
```

**Rationale**:

- Monaco editor provides excellent UX (VS Code editor)
- Syntax highlighting for prompts
- Variable autocomplete prevents typos
- Preview shows rendered prompt with sample data
- Already have React + TypeScript setup

### Decision 6: Migration Strategy

**Phase 1**: Database + API (non-breaking)

- Add table, seed with current prompts
- Add API endpoints
- LLM services check DB first, fall back to hardcoded

**Phase 2**: Frontend UI

- Build Prompt Manager page
- Allow viewing/editing
- Test with preview

**Phase 3**: Traceability

- Link signals to prompt_template_id
- Display in Signal detail page

**Phase 4**: Remove Fallback (after validation)

- Remove hardcoded prompts from services
- Require database prompts only

**Rationale**:

- Incremental rollout reduces risk
- Can validate each phase before proceeding
- Easy rollback if issues detected
- Non-breaking until Phase 4

## Data Model

### Database Schema

```sql
-- Main prompt templates table
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_type VARCHAR(50) NOT NULL CHECK (prompt_type IN ('daily_chart', 'weekly_chart', 'consolidation', 'decision')),
    language VARCHAR(10) NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'zh')),
    strategy_id UUID REFERENCES strategies(id) NULL,  -- NULL = global default
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    deleted_at TIMESTAMP NULL
);

-- Indexes
CREATE INDEX idx_prompt_type_lang_strategy_active ON prompt_templates(prompt_type, language, strategy_id, is_active) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_default_prompt ON prompt_templates(prompt_type, language, strategy_id, is_default) WHERE is_default = TRUE AND deleted_at IS NULL;

-- Link signals to prompts and track performance
ALTER TABLE trading_signals 
    ADD COLUMN prompt_template_id UUID REFERENCES prompt_templates(id),
    ADD COLUMN prompt_version INTEGER;
    
CREATE INDEX idx_signals_prompt ON trading_signals(prompt_template_id);

-- Prompt performance tracking
CREATE TABLE prompt_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_template_id UUID NOT NULL REFERENCES prompt_templates(id),
    strategy_id UUID REFERENCES strategies(id),
    date DATE NOT NULL,
    signals_generated INTEGER NOT NULL DEFAULT 0,
    signals_executed INTEGER NOT NULL DEFAULT 0,
    total_profit_loss DECIMAL(15, 2) DEFAULT 0,
    win_count INTEGER NOT NULL DEFAULT 0,
    loss_count INTEGER NOT NULL DEFAULT 0,
    avg_r_multiple DECIMAL(10, 4),
    best_r_multiple DECIMAL(10, 4),
    worst_r_multiple DECIMAL(10, 4),
    avg_profit_pct DECIMAL(10, 4),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_perf_prompt ON prompt_performance(prompt_template_id, date DESC);
CREATE INDEX idx_prompt_perf_strategy ON prompt_performance(strategy_id, date DESC);
CREATE UNIQUE INDEX idx_prompt_perf_unique ON prompt_performance(prompt_template_id, strategy_id, date);
```

### API Endpoints

```
# Prompt Management
GET    /api/v1/prompts                    List prompts (filter by type, language, strategy)
GET    /api/v1/prompts/{id}               Get prompt detail with performance stats
POST   /api/v1/prompts                    Create new prompt (with strategy_id)
PUT    /api/v1/prompts/{id}               Update prompt (increments version)
DELETE /api/v1/prompts/{id}               Soft delete prompt
POST   /api/v1/prompts/{id}/activate      Set as default for type+language+strategy
POST   /api/v1/prompts/{id}/deactivate    Unset as default
POST   /api/v1/prompts/{id}/test          Test prompt with Jinja2 rendering + LLM call
GET    /api/v1/prompts/{id}/versions      Get version history
POST   /api/v1/prompts/{id}/clone         Clone prompt (optionally to different strategy)
GET    /api/v1/prompts/export             Export all prompts as JSON (with metadata)
POST   /api/v1/prompts/import             Import prompts from JSON

# Prompt Performance
GET    /api/v1/prompts/{id}/performance   Get performance metrics (with date range)
GET    /api/v1/prompts/compare            Compare performance of multiple prompts
POST   /api/v1/prompts/performance/calculate  Trigger daily aggregation (admin)
GET    /api/v1/prompts/leaderboard        Top-performing prompts by R-multiple

# Strategy-Specific Queries
GET    /api/v1/strategies/{id}/prompts    Get all prompts for a strategy
POST   /api/v1/strategies/{id}/prompts    Create prompt for specific strategy
```

## Risks / Trade-offs

### Risk: Bad prompts break signal generation

**Mitigation**:

- Test endpoint validates prompt before saving
- Preview shows rendered prompt
- Can deactivate and revert to previous version quickly
- Validation checks for required sections (entry, stop loss, targets)

### Risk: Database becomes single point of failure

**Mitigation**:

- Caching reduces database dependency
- Fallback to hardcoded prompts during Phase 1-3
- Can export prompts to JSON for backup
- PostgreSQL replication for production

### Risk: Users accidentally edit wrong prompt

**Mitigation**:

- Clear labeling of active/default prompts
- Confirmation dialog before activation
- Clone feature encourages creating new version vs editing live
- Audit trail shows who changed what when

### Risk: Performance degradation

**Mitigation**:

- In-memory caching reduces DB hits
- Indexed queries are fast (<1ms)
- LLM API calls are 10-60 seconds, 5ms DB query is negligible
- Monitor query performance, optimize if needed

### Risk: Prompt versioning gets messy

**Mitigation**:

- Start with simple version counter
- Soft deletes preserve history
- Can add more sophisticated versioning later if needed
- Export feature allows external version control

## Migration Plan

### Step 1: Database Migration (Day 1)

```sql
-- Run migration
alembic revision --autogenerate -m "add_prompt_templates"
alembic upgrade head
```

### Step 2: Seed Data (Day 1)

```bash
python backend/scripts/seed_prompts.py
```

Seeds:

- English daily_chart (from current llm_service.py)
- English weekly_chart (from current llm_service.py)
- English consolidation (from current llm_service.py)
- Chinese daily_chart (from reference workflow)
- Chinese weekly_chart (from reference workflow)
- Chinese consolidation (from reference workflow)

### Step 3: Backend Implementation (Week 1)

- Implement API endpoints
- Refactor LLM services to load from DB with fallback
- Add caching
- Add logging

### Step 4: Frontend Implementation (Week 2)

- Build Prompt Manager UI
- Add navigation
- Test editing and activation

### Step 5: Signal Traceability (Week 2)

- Link signals to prompts
- Update API responses
- Display in UI

### Step 6: Validation (Week 3-4)

- Generate signals with DB prompts
- Compare results with hardcoded prompts
- Monitor for errors or performance issues
- Collect user feedback

### Step 7: Remove Fallback (Week 4+)

- After validation period, remove hardcoded prompts
- Database becomes source of truth
- Document new workflow

## Open Questions

1. **How to handle prompt template conflicts during concurrent edits?**
   - Optimistic locking with version number
   - Show warning if someone else edited since you loaded
   - Show diff of changes made by other user

2. **Do we need role-based access control for prompts?**
   - Not in v1 (all admins can edit)
   - Add user permissions in future if needed
   - Track who edited what in created_by field

3. **Should prompt performance be calculated real-time or batch?**
   - Batch calculation daily via Celery task
   - Real-time updates would be expensive
   - Cache daily metrics for dashboard display

4. **How to handle strategy deletion when prompts reference it?**
   - Set strategy_id to NULL (becomes global default)
   - Or soft delete prompt along with strategy
   - Or prevent strategy deletion if prompts exist (preferred)

## Decisions Made (From User Feedback)

1. ✅ **Full Jinja2 Support** - Not simple variable substitution
   - Use complete Jinja2 template engine
   - Support filters, functions, conditionals, loops
   - Enable complex dynamic prompts

2. ✅ **Strategy-Specific Prompts** - Not global-only
   - Prompts scoped to strategies via strategy_id FK
   - NULL strategy_id = global default
   - Lookup: Check strategy-specific first, fall back to global

3. ✅ **Performance Metrics in v1** - Not future scope
   - Track success rate, R-multiples, P/L per prompt
   - Daily aggregation in prompt_performance table
   - Display in UI for prompt comparison 

## Success Criteria

1. ✅ Prompts can be edited via web UI without code changes
2. ✅ Every signal is linked to prompt template used
3. ✅ Prompt changes take effect within 5 minutes (cache TTL)
4. ✅ Can roll back to previous prompt in <1 minute
5. ✅ Both English and Chinese prompts work seamlessly
6. ✅ No performance degradation in signal generation
7. ✅ System continues working if database is temporarily unavailable (Phase 1-3 fallback)
