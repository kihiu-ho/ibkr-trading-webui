# Configurable Prompt System - OpenSpec Proposal

## Status: ✅ READY FOR APPROVAL

**OpenSpec Change ID**: `add-configurable-prompt-system`
**Validation**: ✅ Passed strict validation
**Location**: `openspec/changes/add-configurable-prompt-system/`

## Overview

This proposal adds a configurable prompt template system that allows managing LLM prompts through a web UI instead of hardcoded values in Python.

### What It Solves

**Current Problems:**
1. ❌ Prompts are hardcoded in `backend/services/llm_service.py`
2. ❌ No audit trail of which prompt generated which signal
3. ❌ Can't A/B test different prompt strategies
4. ❌ Requires code deployment to update prompts
5. ❌ Reference workflow prompts (Chinese) are in JSON, not integrated

**After This Change:**
1. ✅ Prompts stored in database, editable via Web UI
2. ✅ Every signal linked to exact prompt version used
3. ✅ Easy rollback to previous prompts
4. ✅ No code changes needed to update prompts
5. ✅ Reference workflow prompts integrated and configurable

## Key Features

### 1. Database Storage
- New `prompt_templates` table
- Versioning with soft deletes
- One default prompt per (type, language) combination
- Full audit trail

### 2. Web UI (Prompt Manager)
- List/filter/search prompts
- Monaco editor with syntax highlighting
- Variable autocomplete ({{symbol}}, {{now}}, etc.)
- Live preview with sample data
- Test prompts with real charts
- Clone for easy versioning
- Import/export for backup

### 3. Signal Traceability
- Link every signal to `prompt_template_id`
- Display prompt info in signal detail pages
- Navigate from signal to prompt that generated it
- Query signals by prompt for performance analysis

### 4. Multilingual Support
- English and Chinese templates
- Based on reference n8n workflow
- Separate prompts per language
- Fallback to English if Chinese not found

### 5. Performance
- In-memory caching (5-minute TTL)
- ~1-5ms database query overhead (negligible vs 10-60s LLM call)
- Cache invalidation on prompt updates

## Files to Review

### 📋 Core Documentation
- **`openspec/changes/add-configurable-prompt-system/proposal.md`** - Why, what, impact
- **`openspec/changes/add-configurable-prompt-system/design.md`** - Technical decisions, data model, migration plan
- **`openspec/changes/add-configurable-prompt-system/tasks.md`** - 75+ implementation tasks (12 phases)

### 📐 Spec Deltas (What Changes)
- **`specs/llm-integration/spec.md`** - Load prompts from DB, caching, traceability
- **`specs/database-schema/spec.md`** - New table, indexes, constraints
- **`specs/frontend-dashboard/spec.md`** - Prompt Manager UI, editor, testing

## Prompt Types

Based on reference workflow, the system will support:

| Type | Description | Language | Source |
|------|-------------|----------|--------|
| `daily_chart` | Daily timeframe analysis | EN, ZH | Current code + reference |
| `weekly_chart` | Weekly timeframe confirmation | EN, ZH | Current code + reference |
| `consolidation` | Multi-timeframe synthesis | EN, ZH | Current code + reference |
| `decision` | Trading decision extraction | EN | Current code |

## Database Schema

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_type VARCHAR(50) NOT NULL,  -- daily_chart, weekly_chart, consolidation, decision
    language VARCHAR(10) NOT NULL DEFAULT 'en',  -- en, zh
    content TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    deleted_at TIMESTAMP NULL
);

-- Link signals to prompts
ALTER TABLE trading_signals 
    ADD COLUMN prompt_template_id UUID REFERENCES prompt_templates(id),
    ADD COLUMN prompt_version INTEGER;
```

## API Endpoints

New endpoints in `/api/v1/prompts`:

```
GET    /api/v1/prompts                     List prompts (filterable)
GET    /api/v1/prompts/{id}                Get specific prompt
POST   /api/v1/prompts                     Create new prompt
PUT    /api/v1/prompts/{id}                Update prompt (increments version)
DELETE /api/v1/prompts/{id}                Soft delete
POST   /api/v1/prompts/{id}/activate       Set as default
POST   /api/v1/prompts/{id}/test           Test with real chart
GET    /api/v1/prompts/{id}/versions       Get history
POST   /api/v1/prompts/{id}/clone          Clone for versioning
GET    /api/v1/prompts/export              Export all as JSON
POST   /api/v1/prompts/import              Import from JSON
```

## Frontend Pages

### New Page: `/prompts` (Prompt Manager)

**Components:**
- **PromptList** - Table with filters, search, sort
- **PromptEditor** - Monaco editor with validation
- **PromptTester** - Test with real charts
- **PromptHistory** - Version timeline

**Actions:**
- Create, Edit, Delete prompts
- Set as default / Activate / Deactivate
- Clone for versioning
- Test before activating
- View version history
- Import / Export

### Enhanced: Signal Detail Pages
- Display prompt name + version used
- Link to view full prompt
- Show language and timestamp

## Implementation Plan

### Phase 1: Database + API (Week 1)
1. Create migration for `prompt_templates` table
2. Seed with current hardcoded prompts + reference workflow
3. Build API endpoints
4. Add caching to LLM service

### Phase 2: Frontend UI (Week 2)
1. Build Prompt Manager page
2. Implement Monaco editor
3. Add testing functionality
4. Wire up to API

### Phase 3: Traceability (Week 2)
1. Link signals to prompts
2. Update signal detail pages
3. Add prompt info to API responses

### Phase 4: Validation (Week 3-4)
1. Generate signals with DB prompts
2. Compare with hardcoded prompts
3. Monitor performance
4. Collect user feedback

### Phase 5: Cleanup (Week 4+)
1. Remove hardcoded fallback
2. Update documentation
3. Training materials

## Testing Strategy

### Unit Tests
- PromptTemplate model CRUD
- API endpoint validation
- Prompt rendering with variables

### Integration Tests
- Full workflow: Create → Test → Activate → Generate Signal
- Cache invalidation
- Multilingual prompts

### E2E Tests
- Frontend: Create and edit prompt via UI
- Signal generation with custom prompt
- Rollback to previous version

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Bad prompts break system | Test endpoint validates before save, preview shows result |
| Database becomes SPOF | In-memory caching, hardcoded fallback in Phase 1-3 |
| Performance degradation | Caching, indexed queries, monitoring |
| Accidental edits | Confirmation dialogs, clone feature, version history |
| Prompt versioning complexity | Start simple with version counter + soft deletes |

## Success Criteria

- ✅ Prompts editable via web UI (no code changes)
- ✅ Every signal linked to prompt used (full audit trail)
- ✅ Prompt changes take effect within 5 minutes (cache TTL)
- ✅ Can rollback to previous prompt in <1 minute
- ✅ English and Chinese prompts work seamlessly
- ✅ No performance degradation (<10ms overhead)
- ✅ System continues working if DB temporarily unavailable (Phase 1-3)

## Next Steps

1. **Review this proposal** - Check design decisions, scope, tasks
2. **Approve to proceed** - If ready to implement
3. **Start Phase 1** - Database migration + API endpoints
4. **Follow tasks.md** - 75+ tasks organized in 12 phases

## Questions or Concerns?

- Scope too large? Can split into smaller changes
- Need different approach? Design doc has alternatives considered
- Missing requirements? Spec deltas are in `specs/*/spec.md`
- Implementation unclear? Tasks.md has detailed checklist

## Documentation

All documentation is in `openspec/changes/add-configurable-prompt-system/`:

```
add-configurable-prompt-system/
├── proposal.md          ← Why, what, impact
├── design.md            ← Technical decisions, data model
├── tasks.md             ← Implementation checklist (75+ tasks)
└── specs/
    ├── llm-integration/spec.md      ← LLM service changes
    ├── database-schema/spec.md      ← Database changes
    └── frontend-dashboard/spec.md   ← UI changes
```

## Validation

```bash
$ openspec validate add-configurable-prompt-system --strict
✅ Change 'add-configurable-prompt-system' is valid
```

---

**Ready to implement!** 🚀

To start implementation:
```bash
# Review the proposal
cat openspec/changes/add-configurable-prompt-system/proposal.md
cat openspec/changes/add-configurable-prompt-system/design.md

# Follow implementation tasks
cat openspec/changes/add-configurable-prompt-system/tasks.md

# Start with Phase 1: Database + API
cd backend && alembic revision --autogenerate -m "add_prompt_templates"
```

