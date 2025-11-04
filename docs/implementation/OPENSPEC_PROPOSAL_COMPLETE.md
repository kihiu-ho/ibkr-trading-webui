# ✅ OpenSpec Proposal Complete: Configurable Prompt System

## Summary

I've created a complete OpenSpec proposal for implementing a configurable LLM prompt system that addresses your requirements:

1. ✅ **Reference workflow integration** - Chinese prompts from `reference/workflow/IBKR_2_Indicator_4_Prod (1).json` will be imported
2. ✅ **Configurable & traceable** - Prompts stored in database, editable via web UI, fully tracked
3. ✅ **Frontend management** - Full Prompt Manager page with Monaco editor
4. ✅ **OpenSpec compliant** - Validated proposal following all guidelines

## What Was Created

### 📋 OpenSpec Proposal Package
```
openspec/changes/add-configurable-prompt-system/
├── proposal.md (1,600 words)
│   └── Why, what changes, impact, benefits, risks
│
├── design.md (3,500 words)
│   ├── Context & goals
│   ├── 6 key technical decisions with rationale
│   ├── Data model & API design
│   ├── Risk mitigation strategies
│   └── Migration plan (4 phases)
│
├── tasks.md (75+ tasks)
│   └── 12 implementation phases with detailed checklists
│
└── specs/ (Spec deltas for affected capabilities)
    ├── llm-integration/spec.md
    │   ├── 3 ADDED requirements
    │   └── 1 MODIFIED requirement
    ├── database-schema/spec.md
    │   └── 4 ADDED requirements
    └── frontend-dashboard/spec.md
        └── 8 ADDED requirements
```

### 📚 Summary Documents
```
CONFIGURABLE_PROMPTS_PROPOSAL.md  # Executive summary (2,300 words)
QUICK_START_PROMPTS.md            # Quick reference guide
```

## Key Features

### 1. Database-Backed Prompts
```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    prompt_type VARCHAR(50),  -- daily_chart, weekly_chart, consolidation, decision
    language VARCHAR(10),      -- en, zh
    content TEXT,              -- The actual prompt template
    version INTEGER,
    is_active BOOLEAN,
    is_default BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP       -- Soft delete
);

-- Link signals to prompts for traceability
ALTER TABLE trading_signals 
    ADD COLUMN prompt_template_id UUID REFERENCES prompt_templates(id);
```

### 2. Full REST API
```
GET    /api/v1/prompts              List/filter prompts
POST   /api/v1/prompts              Create new
PUT    /api/v1/prompts/{id}         Update (auto-increment version)
DELETE /api/v1/prompts/{id}         Soft delete
POST   /api/v1/prompts/{id}/test    Test with real chart
POST   /api/v1/prompts/{id}/activate  Set as default
GET    /api/v1/prompts/export       Export all as JSON
POST   /api/v1/prompts/import       Import from JSON
```

### 3. Web UI (Prompt Manager)
- **Monaco Editor** - VS Code-style editing with syntax highlighting
- **Variable Autocomplete** - {{symbol}}, {{now}}, {{timeframe}}, etc.
- **Live Preview** - See rendered prompt with sample data
- **Test with Real Charts** - Call LLM API before activation
- **Version History** - Timeline of all changes
- **Clone & Rollback** - Easy variants and recovery
- **Import/Export** - Backup and version control

### 4. Signal Traceability
- Every signal linked to exact prompt version used
- Display prompt info in signal detail pages
- Navigate from signal to prompt
- Query signals by prompt for performance analysis

### 5. Multilingual Support
- English prompts (current llm_service.py)
- Chinese prompts (from reference workflow)
- Automatic fallback if language not found
- Support for future languages

## Validation

```bash
$ openspec validate add-configurable-prompt-system --strict
✅ Change 'add-configurable-prompt-system' is valid
```

All requirements have:
- ✅ Proper scenario format (#### Scenario:)
- ✅ GIVEN/WHEN/THEN structure
- ✅ Clear requirement statements
- ✅ Comprehensive coverage

## Implementation Plan

### Phase 1: Database + API (Week 1)
- Create `prompt_templates` table migration
- Seed with current prompts + reference workflow prompts
- Build 10 API endpoints
- Refactor LLM/AI services to load from database
- Add in-memory caching

### Phase 2: Frontend UI (Week 2)
- Build Prompt Manager page (`/prompts`)
- Monaco editor component with validation
- Test functionality with real charts
- Version history display
- Import/export features

### Phase 3: Traceability (Week 2)
- Link signals to `prompt_template_id`
- Update signal detail pages
- Add "View Prompt" navigation
- Display prompt info in workflows

### Phase 4: Validation (Week 3-4)
- Generate signals with database prompts
- Compare results with hardcoded prompts
- Monitor performance (<10ms overhead)
- Collect user feedback

### Phase 5: Cleanup (Week 4+)
- Remove hardcoded fallback after validation
- Update documentation
- Create training materials

## Reference Workflow Integration

The Chinese prompts from your n8n workflow will be:

1. **Extracted** from JSON nodes:
   - "Analyze Daily Chart" prompt (line 109)
   - "Analyze Weekly Chart" prompt (line 136)
   - "Consolidate Daily&Weekly" prompt (line 87)

2. **Stored** as database records:
   - `prompt_type: "daily_chart", language: "zh"`
   - `prompt_type: "weekly_chart", language: "zh"`
   - `prompt_type: "consolidation", language: "zh"`

3. **Made configurable**:
   - Edit via web UI
   - Version tracking
   - Test before activation
   - Link to signals

## Getting Started

### 1. Review Proposal
```bash
# Executive summary with schema and API design
cat CONFIGURABLE_PROMPTS_PROPOSAL.md

# Or quick reference
cat QUICK_START_PROMPTS.md

# Or full technical design
cat openspec/changes/add-configurable-prompt-system/design.md
```

### 2. Review Implementation Tasks
```bash
# 75+ tasks organized in 12 phases
cat openspec/changes/add-configurable-prompt-system/tasks.md
```

### 3. Review Spec Deltas
```bash
# See what changes to each capability
cat openspec/changes/add-configurable-prompt-system/specs/llm-integration/spec.md
cat openspec/changes/add-configurable-prompt-system/specs/database-schema/spec.md
cat openspec/changes/add-configurable-prompt-system/specs/frontend-dashboard/spec.md
```

### 4. Start Implementation
```bash
# Phase 1: Database migration
cd backend
alembic revision --autogenerate -m "add_prompt_templates"
alembic upgrade head

# Seed default prompts
python backend/scripts/seed_prompts.py

# Continue with tasks.md checklist...
```

## Key Design Decisions

1. **Database vs Files**: Chose database for dynamic updates, audit trail, web UI editing
2. **Caching Strategy**: 5-minute TTL in-memory cache, invalidate on update
3. **Versioning**: Simple version counter + soft deletes (can add complexity later)
4. **Variables**: Jinja2-style {{variables}} for familiarity
5. **Frontend**: Monaco editor (VS Code experience)
6. **Migration**: 4-phase incremental rollout with fallbacks

All decisions include alternatives considered and rationale.

## Benefits

### For Users
- ✅ Edit prompts without waiting for deployments
- ✅ Roll back bad prompts in <1 minute
- ✅ See exactly which prompt generated each signal
- ✅ Test prompts before activation
- ✅ A/B test different strategies (future)

### For Development
- ✅ No code changes needed for prompt updates
- ✅ Clean separation of concerns
- ✅ Easy to add new prompt types
- ✅ Supports future features (per-strategy prompts, user-specific prompts)

### For Compliance
- ✅ Full audit trail of every signal
- ✅ Traceability to exact prompt version
- ✅ Version history preserved
- ✅ Explainable AI decisions

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Bad prompts break system | Test endpoint, preview, validation, easy rollback |
| Database becomes SPOF | In-memory caching, fallback to hardcoded (Phase 1-3) |
| Performance degradation | Caching reduces DB hits, queries indexed, monitoring |
| Complex versioning | Start simple, add complexity only if needed |
| User editing wrong prompt | Confirmation dialogs, clone feature, audit trail |

## Success Criteria

After implementation:
- ✅ Prompts editable via web UI (no code changes)
- ✅ Every signal linked to prompt used (100% traceability)
- ✅ Prompt changes take effect within 5 minutes (cache TTL)
- ✅ Can rollback to previous prompt in <1 minute
- ✅ English and Chinese prompts work seamlessly
- ✅ No performance degradation (<10ms overhead)
- ✅ System continues working if DB temporarily unavailable

## Questions or Concerns?

- **Scope too large?** - Can split into smaller incremental changes
- **Different approach needed?** - Design doc has alternatives considered
- **Missing requirements?** - Spec deltas cover all scenarios
- **Implementation unclear?** - Tasks.md has detailed 75-step checklist
- **Technical questions?** - Design.md has full technical rationale

## Next Steps

1. ✅ **Proposal created** - All OpenSpec files complete
2. 📖 **Review proposal** - Read CONFIGURABLE_PROMPTS_PROPOSAL.md
3. 🤔 **Ask questions** - Clarify anything unclear
4. ✅ **Approve to proceed** - Green light for implementation
5. 🚀 **Start Phase 1** - Database migration + API endpoints

## File Reference

| File | Purpose | Lines |
|------|---------|-------|
| `CONFIGURABLE_PROMPTS_PROPOSAL.md` | Executive summary | 530 |
| `QUICK_START_PROMPTS.md` | Quick reference guide | 260 |
| `openspec/changes/add-configurable-prompt-system/proposal.md` | Why, what, impact | 100 |
| `openspec/changes/add-configurable-prompt-system/design.md` | Technical design | 700 |
| `openspec/changes/add-configurable-prompt-system/tasks.md` | Implementation checklist | 300 |
| `openspec/changes/add-configurable-prompt-system/specs/*/spec.md` | Spec deltas | 400 |

**Total Documentation**: ~2,290 lines across 8 files

## Commands

```bash
# Validate proposal
openspec validate add-configurable-prompt-system --strict

# View proposal summary
openspec show add-configurable-prompt-system

# View spec deltas
openspec diff add-configurable-prompt-system

# List all changes
openspec list
```

---

## ✅ Proposal Status: READY FOR APPROVAL

The complete OpenSpec proposal is ready for your review and approval. Once approved, follow the tasks.md checklist for implementation, starting with Phase 1 (Database + API).

**All OpenSpec requirements met:**
- ✅ Complete proposal.md with why/what/impact
- ✅ Comprehensive design.md with technical decisions
- ✅ Detailed tasks.md with implementation checklist
- ✅ Spec deltas for all affected capabilities
- ✅ Scenarios use proper #### format
- ✅ At least one scenario per requirement
- ✅ Validated with --strict mode

🚀 **Ready to implement!**

