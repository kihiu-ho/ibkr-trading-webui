# Implementation Tasks

## 1. Database Schema
- [ ] 1.1 Create `prompt_templates` table migration
  - id, name, prompt_type, language, **strategy_id**, content, version, is_active, is_default, created_at, updated_at, created_by
- [ ] 1.2 Create `prompt_performance` table for metrics tracking
  - id, prompt_template_id, strategy_id, date, signals_generated, signals_executed, total_profit_loss, win_count, loss_count, avg_r_multiple, best_r_multiple, worst_r_multiple, avg_profit_pct
- [ ] 1.3 Add `prompt_template_id` and `prompt_version` foreign keys to `trading_signals` table
- [ ] 1.4 Create indexes on (prompt_type, language, strategy_id, is_active) and (is_default, prompt_type, language, strategy_id)
- [ ] 1.5 Create performance tracking indexes
- [ ] 1.6 Run migration and verify schema

## 2. Backend Models
- [ ] 2.1 Create `PromptTemplate` SQLAlchemy model with strategy_id FK
- [ ] 2.2 Create `PromptPerformance` SQLAlchemy model
- [ ] 2.3 Add validation for prompt_type enum (daily_chart, weekly_chart, consolidation, decision)
- [ ] 2.4 Add validation for language enum (en, zh)
- [ ] 2.5 Add methods: get_active_prompt(strategy_id), get_default_prompt(type, lang, strategy_id), activate(), deactivate()
- [ ] 2.6 Add relationship to Strategy model (prompt_templates backref)
- [ ] 2.7 Add performance metrics aggregation methods

## 3. Seed Data
- [ ] 3.1 Extract current hardcoded prompts from llm_service.py to JSON
- [ ] 3.2 Extract reference workflow prompts from `reference/workflow/IBKR_2_Indicator_4_Prod (1).json`
- [ ] 3.3 Create seed data script: `backend/scripts/seed_prompts.py`
- [ ] 3.4 Seed default English prompts (current llm_service.py)
- [ ] 3.5 Seed default Chinese prompts (from reference workflow)
- [ ] 3.6 Test seed script

## 4. Backend API Endpoints
- [ ] 4.1 Create `backend/api/prompts.py` router
- [ ] 4.2 Implement GET `/api/v1/prompts` - List prompts (filter by type, language, **strategy_id**)
- [ ] 4.3 Implement GET `/api/v1/prompts/{id}` - Get prompt with **performance stats**
- [ ] 4.4 Implement POST `/api/v1/prompts` - Create new prompt with **strategy_id**
- [ ] 4.5 Implement PUT `/api/v1/prompts/{id}` - Update prompt (increments version)
- [ ] 4.6 Implement DELETE `/api/v1/prompts/{id}` - Soft delete prompt
- [ ] 4.7 Implement POST `/api/v1/prompts/{id}/activate` - Set as default for type+language+**strategy**
- [ ] 4.8 Implement POST `/api/v1/prompts/{id}/test` - Test with **Jinja2 rendering + LLM call**
- [ ] 4.9 Implement GET `/api/v1/prompts/{id}/versions` - Get version history
- [ ] 4.10 Implement POST `/api/v1/prompts/{id}/clone` - Clone prompt (optionally to different strategy)
- [ ] 4.11 Implement GET `/api/v1/prompts/export` - Export all as JSON
- [ ] 4.12 Implement POST `/api/v1/prompts/import` - Import from JSON
- [ ] 4.13 Implement GET `/api/v1/prompts/{id}/performance` - **Get performance metrics**
- [ ] 4.14 Implement GET `/api/v1/prompts/compare` - **Compare multiple prompts**
- [ ] 4.15 Implement GET `/api/v1/prompts/leaderboard` - **Top performers by R-multiple**
- [ ] 4.16 Implement GET `/api/v1/strategies/{id}/prompts` - Get strategy-specific prompts
- [ ] 4.17 Add Pydantic schemas for request/response validation (including performance metrics)
- [ ] 4.18 Register router in `backend/main.py`

## 5. LLM Service Refactoring
- [ ] 5.1 Add `load_prompt_from_db(prompt_type, language, **strategy_id**)` method to LLMService
- [ ] 5.2 Implement **strategy-specific prompt lookup** (check strategy first, fall back to global)
- [ ] 5.3 Implement **full Jinja2 template rendering** with filters and control flow
- [ ] 5.4 Add Jinja2 context builder: provide all variables (symbol, trend, volatility, previous_analyses, etc.)
- [ ] 5.5 Implement in-memory caching for prompts with TTL (key includes strategy_id)
- [ ] 5.6 Refactor `_prepare_prompt()` to render Jinja2 templates from database
- [ ] 5.7 Add Jinja2 error handling with helpful messages
- [ ] 5.8 Keep hardcoded prompts as fallback during migration
- [ ] 5.9 Update `analyze_chart()` to accept optional prompt_template_id and strategy_id parameters
- [ ] 5.10 Store prompt_template_id and prompt_version in analysis results
- [ ] 5.11 Add logging: which prompt template (including strategy) was used for analysis

## 6. AI Service Refactoring
- [ ] 6.1 Refactor ai_service.py to load decision prompt from database
- [ ] 6.2 Update `generate_trading_decision()` to track prompt used
- [ ] 6.3 Add prompt caching similar to LLMService

## 7. Signal Storage Enhancement
- [ ] 7.1 Update SignalGenerator to link signals to prompt_template_id and prompt_version
- [ ] 7.2 Update database queries to join prompt_template **and strategy** data
- [ ] 7.3 Ensure signal API responses include prompt info **and performance metrics**
- [ ] 7.4 Add signal outcome tracking (win/loss, R-multiple, profit_loss) for performance aggregation

## 8. Frontend - Prompt Manager UI
- [ ] 8.1 Create `frontend/components/PromptManager.tsx`
- [ ] 8.2 Create `frontend/components/PromptEditor.tsx` with **Jinja2 syntax highlighting**
- [ ] 8.3 Create `frontend/components/PromptList.tsx` - table view with **performance metrics**
- [ ] 8.4 Add filter by type, language, **and strategy**
- [ ] 8.5 Add **strategy selector dropdown** when creating/editing prompts
- [ ] 8.6 Add version history view
- [ ] 8.7 Add "Test Prompt" button with **Jinja2 preview + LLM test**
- [ ] 8.8 Add "Activate/Deactivate" toggle (per strategy)
- [ ] 8.9 Add "Clone Prompt" feature (with option to clone to different strategy)
- [ ] 8.10 Add "Revert to Default" button
- [ ] 8.11 Add **Jinja2 variable reference panel** (shows available variables and filters)
- [ ] 8.12 Add **performance metrics display** (R-multiple, win rate, P/L) in prompt list and detail

## 9. Frontend - Integration
- [ ] 9.1 Add "Prompts" nav link in sidebar
- [ ] 9.2 Create route `/prompts` → PromptManager page
- [ ] 9.3 Create route `/prompts/:id` → Prompt detail page with **performance charts**
- [ ] 9.4 Update Signal detail page to show prompt used (with **strategy context**)
- [ ] 9.5 Add "View Prompt" link from signal to prompt detail
- [ ] 9.6 Update Workflow page to show active prompts in use (per strategy)
- [ ] 9.7 Update Strategy detail page to show **strategy-specific prompts**
- [ ] 9.8 Add **Prompt Performance Dashboard** - compare prompts, view trends over time

## 10. Documentation
- [ ] 10.1 Update README.md with Prompt Management section
- [ ] 10.2 Create `PROMPT_CONFIGURATION_GUIDE.md`
- [ ] 10.3 Document prompt template format and variables
- [ ] 10.4 Add examples of customizing prompts
- [ ] 10.5 Document best practices for prompt versioning
- [ ] 10.6 Add API documentation for /api/v1/prompts endpoints

## 10. Performance Tracking Implementation
- [ ] 10.1 Create Celery task for daily performance aggregation
- [ ] 10.2 Implement `calculate_prompt_performance()` function
  - Query signals by prompt_template_id and date range
  - Aggregate: count, win_count, loss_count, avg_r_multiple, best/worst_r, avg_profit_pct, total_profit_loss
  - Insert/update prompt_performance table
- [ ] 10.3 Add Celery Beat schedule for daily execution (e.g., midnight)
- [ ] 10.4 Create performance comparison queries (compare multiple prompts)
- [ ] 10.5 Implement leaderboard query (top N prompts by R-multiple or win rate)
- [ ] 10.6 Add performance metrics to prompt API responses
- [ ] 10.7 Test performance calculation with sample data

## 11. Jinja2 Template System
- [ ] 11.1 Add Jinja2 as explicit dependency (already used by LangChain)
- [ ] 11.2 Create `PromptRenderer` class with Jinja2 environment
- [ ] 11.3 Register custom filters (date formatting, etc.)
- [ ] 11.4 Build context dictionary with all available variables
- [ ] 11.5 Add Jinja2 error handling (template syntax errors, undefined variables)
- [ ] 11.6 Add sandbox mode (disable dangerous functions if needed)
- [ ] 11.7 Test complex templates with conditionals, loops, filters

## 12. Testing
- [ ] 12.1 Unit tests for PromptTemplate model **with strategy_id**
- [ ] 12.2 Unit tests for PromptPerformance model
- [ ] 12.3 Unit tests for prompt API endpoints (including **performance endpoints**)
- [ ] 12.4 Unit tests for **Jinja2 rendering** with various templates
- [ ] 12.5 Integration test: Create → Test (Jinja2 + LLM) → Activate → Generate Signal
- [ ] 12.6 Integration test: **Strategy-specific prompt lookup**
- [ ] 12.7 Test prompt caching and invalidation (including strategy_id in cache key)
- [ ] 12.8 Test fallback to hardcoded prompts
- [ ] 12.9 Test multilingual prompts (English + Chinese)
- [ ] 12.10 Test **performance aggregation** Celery task
- [ ] 12.11 Frontend E2E test: Create and edit prompt with **Jinja2 syntax**
- [ ] 12.12 Frontend E2E test: View **performance metrics** in UI

## 13. Migration & Deployment
- [ ] 13.1 Run database migration (prompt_templates + prompt_performance tables)
- [ ] 13.2 Run seed script to populate **global default prompts** (strategy_id=NULL)
- [ ] 13.3 Verify default prompts are active for each type+language
- [ ] 13.4 Test signal generation with database prompts (both **global and strategy-specific**)
- [ ] 13.5 Test **Jinja2 template rendering** in production
- [ ] 13.6 Monitor for any performance issues (caching effectiveness)
- [ ] 13.7 Run initial **performance aggregation** for historical signals
- [ ] 13.8 Verify **performance metrics** display correctly in UI
- [ ] 13.9 Monitor Celery Beat task for daily performance updates
- [ ] 13.10 Remove hardcoded fallback after 2-week validation period

