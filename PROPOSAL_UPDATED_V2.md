# ✅ Proposal Updated Per Your Feedback - Ready for Approval

## Summary of Changes

I've updated the **add-configurable-prompt-system** proposal to incorporate your three design requirements:

### 1. ✅ Full Jinja2 Support (Not Simple Variables)

**Was**: Simple variable substitution `{{symbol}}` only
**Now**: Full Jinja2 template engine with:
- Filters: `{{now | date('%Y-%m-%d')}}`, `{{symbol | upper}}`
- Conditionals: `{% if trend == 'bullish' %}...{% endif %}`
- Loops: `{% for sig in previous_analyses %}...{% endfor %}`
- Macros for reusable template blocks
- Custom filters for date formatting, rounding, etc.

**Impact**: +7 tasks for Jinja2 implementation (Section 11)

### 2. ✅ Strategy-Specific Prompts (Not Global Only)

**Was**: One set of prompts for all strategies  
**Now**: 
- Prompts scoped to strategies via `strategy_id` foreign key
- NULL `strategy_id` = global default
- Lookup order: Check strategy-specific first, fall back to global
- Different prompts per strategy without affecting others

**Impact**: 
- Database schema change (add `strategy_id` column + index)
- API endpoints for strategy-specific queries
- +6 tasks for strategy-specific implementation

### 3. ✅ Performance Metrics Tracking (In v1, Not Future)

**Was**: Deferred to future version  
**Now**: Full implementation in Phase 1:
- New `prompt_performance` table
- Daily Celery task for aggregation
- Track: signals_generated, win_count, loss_count, avg_r_multiple, best/worst_r, total_profit_loss
- API endpoints: `/performance`, `/compare`, `/leaderboard`
- Frontend dashboard for prompt performance comparison

**Impact**: +7 tasks for performance tracking (Section 10)

## Updated Scope

### Task Count
- **Before**: 75 tasks in 12 phases
- **After**: **95 tasks in 13 phases**

### New Sections Added
- **Section 10**: Performance Tracking Implementation (7 tasks)
- **Section 11**: Jinja2 Template System (7 tasks)
- **Section 12**: Testing (expanded from 7 to 12 tasks)
- **Section 13**: Migration & Deployment (expanded from 6 to 10 tasks)

### Database Schema Updates

```sql
-- Added strategy_id column
CREATE TABLE prompt_templates (
    ...
    strategy_id UUID REFERENCES strategies(id) NULL,  -- NEW
    ...
);

-- New table for performance tracking
CREATE TABLE prompt_performance (
    id UUID PRIMARY KEY,
    prompt_template_id UUID NOT NULL,
    strategy_id UUID,
    date DATE NOT NULL,
    signals_generated INTEGER,
    signals_executed INTEGER,
    total_profit_loss DECIMAL(15, 2),
    win_count INTEGER,
    loss_count INTEGER,
    avg_r_multiple DECIMAL(10, 4),
    best_r_multiple DECIMAL(10, 4),
    worst_r_multiple DECIMAL(10, 4),
    avg_profit_pct DECIMAL(10, 4),
    ...
);
```

### API Endpoints Updates

**Added**:
```
# Performance endpoints
GET    /api/v1/prompts/{id}/performance     # Get metrics with date range
GET    /api/v1/prompts/compare              # Compare multiple prompts
GET    /api/v1/prompts/leaderboard          # Top performers by R-multiple
POST   /api/v1/prompts/performance/calculate  # Trigger aggregation (admin)

# Strategy-specific
GET    /api/v1/strategies/{id}/prompts      # Get strategy prompts
POST   /api/v1/strategies/{id}/prompts      # Create for strategy
```

**Total**: 18 API endpoints (was 12)

### Frontend Updates

**New Components**:
- Jinja2 Variable Reference Panel
- Performance Metrics Display (R-multiple, win rate, P/L charts)
- Prompt Performance Dashboard
- Strategy selector in prompt editor
- Prompt comparison view
- Leaderboard view

### Spec Delta Updates

Added 3 new requirements to `llm-integration/spec.md`:
1. **Strategy-Specific Prompt Support** (2 scenarios)
2. **Full Jinja2 Template Rendering** (4 scenarios)
3. **Prompt Performance Tracking** (4 scenarios)

Total: **10 new scenarios** added to spec deltas

## Validation Status

```bash
$ openspec validate add-configurable-prompt-system --strict
✅ Change 'add-configurable-prompt-system' is valid
```

All requirements have proper #### Scenario format with GIVEN/WHEN/THEN structure.

## Files Updated

| File | Changes |
|------|---------|
| `design.md` | +150 lines - Full Jinja2 decision, strategy scoping, performance tracking |
| `tasks.md` | +20 tasks - Sections 10, 11, 12, 13 expanded |
| `proposal.md` | Updated scope summary with new features |
| `specs/llm-integration/spec.md` | +100 lines - 3 new requirements, 10 scenarios |
| `specs/database-schema/spec.md` | (needs update - will do if approved) |
| `specs/frontend-dashboard/spec.md` | (needs update - will do if approved) |

## Estimated Timeline

**Original**: 4-5 weeks  
**Updated**: **6-7 weeks**

Breakdown:
- Week 1: Database + API (now includes performance tables)
- Week 2: Jinja2 + LLM service refactoring
- Week 3: Frontend UI (now includes performance dashboards)
- Week 4: Strategy integration + performance tracking
- Week 5-6: Testing (more comprehensive)
- Week 7: Deployment + validation

## Implementation Phases

### Phase 1: Database + API (Week 1-2)
- Create `prompt_templates` with `strategy_id`
- Create `prompt_performance` table
- Build 18 API endpoints
- Implement Jinja2 rendering
- Strategy-specific lookup logic

### Phase 2: Frontend UI (Week 3)
- Prompt Manager with Monaco editor
- Jinja2 syntax highlighting
- Variable reference panel
- Strategy selector

### Phase 3: Performance & Strategy (Week 4)
- Celery task for daily aggregation
- Performance calculation logic
- Performance dashboards
- Strategy-specific prompt UI
- Comparison views

### Phase 4: Testing (Week 5-6)
- 95 test scenarios
- Jinja2 template testing
- Strategy-specific tests
- Performance aggregation tests
- E2E frontend tests

### Phase 5: Deployment (Week 7)
- Run migrations
- Seed global defaults
- Validate in production
- Monitor performance
- Remove fallback

## Key Decisions Made

1. **Jinja2**: Full template engine, not simple variables
   - Rationale: Already a dependency via LangChain, enables complex dynamic prompts

2. **Strategy-Specific**: FK to strategies, not global only
   - Rationale: Different trading styles need different prompts, fallback ensures robustness

3. **Performance in v1**: Track from the start, not later
   - Rationale: Data-driven prompt optimization is core value proposition, easier than retrofitting

## Next Steps - Awaiting Your Approval

**Please confirm you approve the updated proposal:**

✅ **Option 1: Approve - Proceed with Implementation**
- I'll start Phase 1 immediately
- Create TODO list for tracking (95 tasks)
- Begin with database migration

❌ **Option 2: Request Changes**
- Specify what needs adjustment
- I'll update and re-validate

**Once approved**, I'll:
1. Create comprehensive TODO list (95 tasks)
2. Start Phase 1: Database migration
3. Implement systematically following tasks.md
4. Update checklist as I complete each task
5. Show progress after each major milestone

## Questions Before Starting?

- Scope too large? (Can split into smaller increments)
- Timeline concerns? (Can prioritize core features first)
- Technical questions? (Happy to clarify any decisions)
- Want to see more detail? (Can expand any section)

---

**Awaiting your approval to proceed! 🚀**

Type "approved" or "proceed" to start implementation, or ask questions/request changes.

