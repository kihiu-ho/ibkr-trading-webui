# Quick Start: Configurable Prompts Implementation

## 📋 OpenSpec Proposal Complete!

**Change ID**: `add-configurable-prompt-system`
**Status**: ✅ Validated and ready for implementation
**Full Proposal**: `CONFIGURABLE_PROMPTS_PROPOSAL.md`

## What Was Created

### 1. OpenSpec Documentation
```
openspec/changes/add-configurable-prompt-system/
├── proposal.md          # Why, what, impact summary
├── design.md            # Technical decisions, 20+ pages
├── tasks.md             # 75+ implementation tasks
└── specs/               # Spec deltas for affected capabilities
    ├── llm-integration/spec.md
    ├── database-schema/spec.md
    └── frontend-dashboard/spec.md
```

### 2. Summary Document
- **`CONFIGURABLE_PROMPTS_PROPOSAL.md`** - Executive summary with schema, API design, implementation plan

## Quick Overview

### What It Does
- Stores LLM prompts in database (not hardcoded)
- Web UI to edit prompts (Monaco editor)
- Links every signal to prompt used (audit trail)
- Supports English + Chinese prompts
- Based on reference n8n workflow

### Key Features
✅ Configurable without code changes
✅ Full version history
✅ Test prompts before activation
✅ Clone for easy variants
✅ Import/export for backup
✅ Signal traceability

## Implementation Phases

### Phase 1: Database + API (Week 1)
```bash
# 1. Create database table
cd backend
alembic revision --autogenerate -m "add_prompt_templates"
alembic upgrade head

# 2. Seed with prompts
python backend/scripts/seed_prompts.py

# 3. Build API endpoints
# See: tasks.md section "4. Backend API Endpoints"

# 4. Refactor LLM service
# See: tasks.md section "5. LLM Service Refactoring"
```

### Phase 2: Frontend UI (Week 2)
```bash
# Build Prompt Manager page
# See: tasks.md section "8. Frontend - Prompt Manager UI"

# Create components:
# - PromptList.tsx
# - PromptEditor.tsx (Monaco editor)
# - PromptTester.tsx
```

### Phase 3: Traceability (Week 2)
```bash
# Link signals to prompts
# See: tasks.md section "7. Signal Storage Enhancement"

# Update signal detail pages
# See: tasks.md section "9. Frontend - Integration"
```

### Phase 4-5: Validation & Cleanup (Week 3-4)
```bash
# Test, monitor, remove fallback
# See: tasks.md sections "11. Testing" and "12. Migration & Deployment"
```

## Quick Commands

### View Proposal
```bash
# Executive summary
cat CONFIGURABLE_PROMPTS_PROPOSAL.md

# Full technical design
cat openspec/changes/add-configurable-prompt-system/design.md

# Implementation tasks
cat openspec/changes/add-configurable-prompt-system/tasks.md
```

### Validate OpenSpec
```bash
cd /Users/he/git/ibkr-trading-webui
openspec validate add-configurable-prompt-system --strict
```

### View Spec Deltas
```bash
# See what changes to llm-integration
cat openspec/changes/add-configurable-prompt-system/specs/llm-integration/spec.md

# See database changes
cat openspec/changes/add-configurable-prompt-system/specs/database-schema/spec.md

# See frontend changes
cat openspec/changes/add-configurable-prompt-system/specs/frontend-dashboard/spec.md
```

## Database Schema (Quick Reference)

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    prompt_type VARCHAR(50) NOT NULL,  -- daily_chart, weekly_chart, consolidation, decision
    language VARCHAR(10) NOT NULL DEFAULT 'en',  -- en, zh
    content TEXT NOT NULL,  -- The actual prompt template
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL  -- Soft delete
);

ALTER TABLE trading_signals 
    ADD COLUMN prompt_template_id UUID REFERENCES prompt_templates(id);
```

## API Endpoints (Quick Reference)

```
GET    /api/v1/prompts              List/filter prompts
POST   /api/v1/prompts              Create new prompt
PUT    /api/v1/prompts/{id}         Update (increments version)
DELETE /api/v1/prompts/{id}         Soft delete
POST   /api/v1/prompts/{id}/test    Test with real chart
POST   /api/v1/prompts/{id}/activate  Set as default
GET    /api/v1/prompts/export       Export all as JSON
```

## Frontend Routes (Quick Reference)

```
/prompts                   Prompt Manager page
/prompts/{id}              View/edit specific prompt
/signals/{id}              Signal detail (now shows prompt used)
```

## Prompt Types

| Type | Purpose | Languages |
|------|---------|-----------|
| `daily_chart` | Daily timeframe analysis | EN, ZH |
| `weekly_chart` | Weekly confirmation | EN, ZH |
| `consolidation` | Multi-timeframe synthesis | EN, ZH |
| `decision` | Trading decision extraction | EN |

## Reference Workflow Integration

The Chinese prompts from `reference/workflow/IBKR_2_Indicator_4_Prod (1).json` will be:
1. Extracted during seed process
2. Stored as default Chinese templates
3. Editable via web UI
4. Linked to signals for traceability

## Task Breakdown

75+ tasks organized into 12 phases:
1. Database Schema (4 tasks)
2. Backend Models (4 tasks)
3. Seed Data (6 tasks)
4. Backend API Endpoints (10 tasks)
5. LLM Service Refactoring (7 tasks)
6. AI Service Refactoring (3 tasks)
7. Signal Storage Enhancement (3 tasks)
8. Frontend - Prompt Manager UI (9 tasks)
9. Frontend - Integration (5 tasks)
10. Documentation (6 tasks)
11. Testing (7 tasks)
12. Migration & Deployment (6 tasks)

**Total**: ~75 implementation tasks

## Key Decisions (From design.md)

1. ✅ Database storage (not file-based)
2. ✅ In-memory caching (5-minute TTL)
3. ✅ Simple version counter (not git-style branching)
4. ✅ Jinja2-style variables ({{symbol}}, {{now}})
5. ✅ Monaco editor for frontend
6. ✅ 4-phase migration (incremental rollout)

## Success Metrics

After implementation:
- ✅ Edit prompts without code deployments
- ✅ <1 minute to rollback bad prompt
- ✅ 100% signal traceability
- ✅ <10ms database overhead
- ✅ Support EN + ZH seamlessly

## Next Steps

1. **Review** - Read `CONFIGURABLE_PROMPTS_PROPOSAL.md`
2. **Questions?** - Check `design.md` for rationale
3. **Approve** - Confirm scope and approach
4. **Implement** - Follow `tasks.md` checklist

## Getting Help

- **Full proposal**: `CONFIGURABLE_PROMPTS_PROPOSAL.md`
- **Technical design**: `openspec/changes/add-configurable-prompt-system/design.md`
- **Task checklist**: `openspec/changes/add-configurable-prompt-system/tasks.md`
- **Spec deltas**: `openspec/changes/add-configurable-prompt-system/specs/*/spec.md`

---

**TL;DR**: Complete OpenSpec proposal for configurable prompts is ready. Follow `tasks.md` for implementation, starting with database migration in Phase 1. 🚀

