# Add Configurable Prompt System

## Why

The current LLM integration uses hardcoded prompt templates in Python code (backend/services/llm_service.py). Users cannot:
- Customize analysis prompts without code changes
- Track which prompt version generated a signal
- A/B test different prompt strategies
- Roll back to previous prompts easily
- See what prompts are being used in production

The reference n8n workflow (`reference/workflow/IBKR_2_Indicator_4_Prod (1).json`) contains sophisticated multi-timeframe analysis prompts in Traditional Chinese that follow a specific technical analysis framework. These should be:
1. Configurable without code deployments
2. Versioned and traceable
3. Editable through the web UI
4. Linked to trading signals for audit trails

## What Changes

- **Database**: Add `prompt_templates` table with **strategy_id FK** + `prompt_performance` table for metrics
- **Backend API**: Add CRUD endpoints for prompt management + **performance tracking endpoints**
- **LLM Service**: Refactor to load prompts from database with **full Jinja2 rendering** and **strategy-specific lookup**
- **Signal Storage**: Link generated signals to the prompt_template_id used + **track outcomes for performance**
- **Frontend UI**: Add Prompt Manager page with **Monaco editor**, **Jinja2 syntax highlighting**, **performance dashboards**
- **Workflow Tracing**: Display which prompt (and strategy) generated each signal + **performance metrics**
- **Default Prompts**: Import reference workflow prompts as seed data (global defaults)
- **Performance Tracking**: Daily Celery task to aggregate signal outcomes by prompt
- **Jinja2 Templates**: Full template engine with filters, conditionals, loops, macros

New features:
- **Strategy-Specific Prompts**: Different prompts per strategy with fallback to global defaults
- **Full Jinja2 Support**: Conditionals, loops, filters (not just variable substitution)
- **Performance Metrics**: Track R-multiple, win rate, P/L per prompt version
- **Prompt Comparison**: Compare performance of different prompts
- **Leaderboard**: Top-performing prompts by R-multiple

New prompt types:
- `daily_chart` - Daily timeframe technical analysis
- `weekly_chart` - Weekly timeframe trend confirmation
- `consolidation` - Multi-timeframe synthesis
- `decision` - Trading decision extraction

## Impact

**Affected Specs:**
- `llm-integration` - Add configurable prompt loading
- `frontend-dashboard` - Add Prompt Manager UI
- `database-schema` - Add prompt_templates table
- `chart-analysis` - Reference prompts when generating analysis

**Affected Code:**
- `backend/services/llm_service.py` - Refactor hardcoded templates
- `backend/services/ai_service.py` - Load prompts from database
- `backend/api/` - Add new `/api/v1/prompts` endpoints
- `backend/models/` - Add PromptTemplate model
- `frontend/components/` - Add PromptManager component
- `frontend/pages/` - Add prompts management page
- `database/migrations/` - Add migration for new table

**Breaking Changes:**
- **NONE** - Existing code will continue working with default prompts seeded from current hardcoded values

**Migration Plan:**
1. Create database table
2. Seed with current hardcoded prompts + reference workflow prompts
3. Refactor services to check database first, fall back to hardcoded
4. Add API endpoints
5. Build frontend UI
6. Add tracking to signals
7. Remove hardcoded fallback after validation

**Benefits:**
- ✅ No code changes needed to update prompts
- ✅ Full audit trail of what prompted what signal
- ✅ Easy rollback if a prompt performs poorly
- ✅ **Data-driven prompt optimization** via performance metrics
- ✅ **Strategy-specific customization** without affecting global defaults
- ✅ **Dynamic prompts** with Jinja2 conditionals and loops
- ✅ **Performance comparison** to identify best prompts
- ✅ Compliance/explainability for trading decisions
- ✅ Multilingual support (Chinese + English templates)

**Risks:**
- Users could break signal generation with bad prompts
  - *Mitigation*: Validation + require testing before making default
- Database queries add latency
  - *Mitigation*: Cache prompts in-memory, invalidate on update
- Prompt versioning could get complex
  - *Mitigation*: Start simple with soft deletes and version numbers

