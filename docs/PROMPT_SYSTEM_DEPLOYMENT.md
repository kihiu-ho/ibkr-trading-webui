# Configurable Prompt System - Deployment Guide

## Pre-Deployment Checklist

### ✅ Required Files

All files have been created and are ready for deployment:

**Database**:
- [ ] `database/migrations/add_prompt_templates.sql` - Schema migration
- [ ] `database/migrations/seed_prompt_templates.sql` - Seed data

**Backend Models**:
- [ ] `backend/models/prompt.py` - PromptTemplate & PromptPerformance models
- [ ] `backend/models/strategy.py` - Updated with relationships
- [ ] `backend/models/trading_signal.py` - Updated with prompt tracking
- [ ] `backend/models/__init__.py` - Exports new models

**Backend Services**:
- [ ] `backend/services/prompt_renderer.py` - Jinja2 rendering
- [ ] `backend/services/llm_service.py` - Refactored for database prompts
- [ ] `backend/services/signal_generator.py` - Updated for prompt metadata

**Backend API**:
- [ ] `backend/schemas/prompt.py` - 15 Pydantic schemas
- [ ] `backend/api/prompts.py` - 18 REST endpoints
- [ ] `backend/main.py` - Router registered

**Backend Tasks**:
- [ ] `backend/tasks/prompt_performance_tasks.py` - Celery tasks
- [ ] `backend/celery_app.py` - Beat schedule configured

**Documentation**:
- [ ] `docs/PROMPT_SYSTEM_USER_GUIDE.md` - User guide
- [ ] `docs/PROMPT_SYSTEM_DEPLOYMENT.md` - This file
- [ ] `IMPLEMENTATION_PROGRESS.md` - Implementation status

### ✅ Dependencies

All dependencies are already in `requirements.txt`:
- `jinja2>=3.1.2` ✓
- `sqlalchemy>=2.0.23` ✓
- `pydantic>=2.10.0` ✓
- `celery>=5.3.4` ✓

No new dependencies needed!

---

## Deployment Steps

### Step 1: Database Migration

#### 1.1 Backup Database

```bash
# Backup your database first!
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

#### 1.2 Run Schema Migration

```bash
# Apply schema changes
psql $DATABASE_URL -f database/migrations/add_prompt_templates.sql
```

**Expected Output**:
```
CREATE TABLE
CREATE TABLE
ALTER TABLE
ALTER TABLE
CREATE INDEX
...
(15+ CREATE INDEX statements)
CREATE FUNCTION
CREATE TRIGGER
```

#### 1.3 Verify Tables

```bash
psql $DATABASE_URL -c "\d prompt_templates"
psql $DATABASE_URL -c "\d prompt_performance"
psql $DATABASE_URL -c "\d trading_signals" | grep prompt
```

Should show:
- `prompt_templates` table with 13 columns
- `prompt_performance` table with 15 columns
- `trading_signals` with 6 new columns (prompt_template_id, prompt_version, prompt_type, outcome, actual_r_multiple, profit_loss, exit_price, exit_time)

#### 1.4 Seed Default Prompts

```bash
# Load 6 default templates
psql $DATABASE_URL -f database/migrations/seed_prompt_templates.sql
```

**Expected Output**:
```
INSERT 0 1
INSERT 0 1
INSERT 0 1
INSERT 0 1
INSERT 0 1
INSERT 0 1
NOTICE:  Prompt templates seeded successfully. Total: 6 templates
```

#### 1.5 Verify Seed Data

```bash
psql $DATABASE_URL -c "SELECT id, name, template_type, language, is_default FROM prompt_templates;"
```

Should show 6 templates:
- 3 main analysis templates (daily, weekly, consolidation)
- 3 system message templates

---

### Step 2: Deploy Backend Code

#### 2.1 Pull Latest Code

```bash
cd /Users/he/git/ibkr-trading-webui
git add .
git commit -m "Add configurable prompt system"
git push
```

#### 2.2 Restart Backend Services

```bash
# Restart all backend services to load new code
docker-compose restart backend

# Restart Celery worker (for new tasks)
docker-compose restart celery-worker

# Restart Celery Beat (for new schedule)
docker-compose restart celery-beat
```

#### 2.3 Verify Services

```bash
# Check backend logs
docker-compose logs backend | tail -50

# Check for successful startup
docker-compose logs backend | grep "Application started successfully"

# Check Celery worker
docker-compose logs celery-worker | grep "ready"

# Check Celery Beat schedule
docker-compose logs celery-beat | grep "calculate-prompt-performance-daily"
```

---

### Step 3: API Verification

#### 3.1 Health Check

```bash
curl http://localhost:8000/api/health
```

Should return `{"status": "healthy"}`

#### 3.2 List Prompts

```bash
curl http://localhost:8000/api/v1/prompts/ | jq
```

Should return 6 templates with full details.

#### 3.3 Test Prompt Loading

```bash
# Check backend logs while generating a signal
docker-compose logs -f backend &

# Generate a test signal (if you have a strategy configured)
curl -X POST "http://localhost:8000/api/signals/generate" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "strategy_id": 1}'
```

Look for log messages like:
```
INFO: Loaded global default prompt: Daily Chart Technical Analysis (ID: 1)
INFO: Rendered prompt (2500 chars) from template: Daily Chart Technical Analysis
INFO: Analysis complete for AAPL (prompt_id=1, version=1)
```

#### 3.4 Swagger UI

Visit http://localhost:8000/docs

You should see new `/api/v1/prompts/` endpoints in the API documentation.

---

### Step 4: Celery Beat Configuration

#### 4.1 Verify Beat Schedule

```bash
docker-compose exec celery-beat celery -A backend.celery_app inspect scheduled
```

Should show:
- `calculate-prompt-performance-daily` scheduled for 1:00 AM UTC
- `cleanup-old-performance-records-monthly` scheduled for 1st of month at 2:00 AM UTC

#### 4.2 Test Manual Execution

```bash
# Test performance calculation task
docker-compose exec celery-worker celery -A backend.celery_app call calculate_prompt_performance_daily
```

#### 4.3 Monitor Task Execution

```bash
# Watch Celery logs
docker-compose logs -f celery-worker

# Check task results
docker-compose exec celery-worker celery -A backend.celery_app inspect active
docker-compose exec celery-worker celery -A backend.celery_app inspect stats
```

---

### Step 5: Performance Tracking Setup

#### 5.1 Update Signal Outcomes

For existing signals, you'll need to update outcomes manually for performance tracking:

```python
# Python script to backfill outcomes
from backend.core.database import SessionLocal
from backend.models.trading_signal import TradingSignal

db = SessionLocal()

# Example: Mark old signals based on your criteria
signals = db.query(TradingSignal).filter(
    TradingSignal.status == 'executed',
    TradingSignal.outcome.is_(None)
).all()

for signal in signals:
    # Your logic to determine win/loss
    if signal.execution_price and signal.target_conservative:
        if signal.execution_price >= signal.target_conservative:
            signal.outcome = 'win'
            # Calculate R-multiple
            risk = abs(signal.execution_price - signal.stop_loss) if signal.stop_loss else 1
            reward = abs(signal.execution_price - signal.entry_price_low) if signal.entry_price_low else 0
            signal.actual_r_multiple = reward / risk if risk > 0 else 0
        else:
            signal.outcome = 'loss'

db.commit()
db.close()
```

#### 5.2 Run Initial Performance Calculation

```bash
# Calculate performance for last 30 days
docker-compose exec celery-worker python -c "
from backend.tasks.prompt_performance_tasks import calculate_prompt_performance_range
from datetime import date, timedelta
end = date.today()
start = end - timedelta(days=30)
calculate_prompt_performance_range.delay(str(start), str(end))
"
```

#### 5.3 Verify Performance Data

```bash
psql $DATABASE_URL -c "SELECT * FROM prompt_performance ORDER BY date DESC LIMIT 10;"
```

---

### Step 6: Monitoring & Validation

#### 6.1 Monitor Database Growth

```bash
# Check table sizes
psql $DATABASE_URL -c "
SELECT 
  schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN ('prompt_templates', 'prompt_performance', 'trading_signals')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

#### 6.2 Monitor API Performance

```bash
# Check API response times
curl -w "@-" -o /dev/null -s "http://localhost:8000/api/v1/prompts/" <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
   time_pretransfer:  %{time_pretransfer}\n
      time_redirect:  %{time_redirect}\n
 time_starttransfer:  %{time_starttransfer}\n
                    ----------\n
         time_total:  %{time_total}\n
EOF
```

#### 6.3 Monitor Celery Health

```bash
# Celery worker status
docker-compose exec celery-worker celery -A backend.celery_app status

# Task history
docker-compose exec celery-worker celery -A backend.celery_app events

# Failed tasks
docker-compose exec celery-worker celery -A backend.celery_app inspect failed
```

---

## Rollback Procedure

If something goes wrong, follow these steps:

### Quick Rollback (Code Only)

```bash
# Revert code changes
git reset --hard HEAD~1

# Restart services
docker-compose restart backend celery-worker celery-beat
```

### Full Rollback (Including Database)

```bash
# 1. Restore database backup
psql $DATABASE_URL < backup_YYYYMMDD.sql

# 2. Revert code
git reset --hard HEAD~1

# 3. Restart services
docker-compose restart backend celery-worker celery-beat
```

### Partial Rollback (Keep Database, Revert Code)

```bash
# If database is fine but code has issues:

# 1. Deactivate all custom prompts
psql $DATABASE_URL -c "UPDATE prompt_templates SET is_active = false WHERE created_by != 'system';"

# 2. Ensure system prompts are active
psql $DATABASE_URL -c "UPDATE prompt_templates SET is_active = true WHERE created_by = 'system';"

# 3. Restart services
docker-compose restart backend celery-worker celery-beat
```

---

## Configuration Options

### Environment Variables

No new environment variables required! The system uses existing configs:

- `DATABASE_URL` - Already configured
- `CELERY_BROKER_URL` - Already configured
- `CELERY_RESULT_BACKEND` - Already configured
- `OPENAI_API_KEY` - Already configured
- `OPENAI_API_BASE` - Already configured

### Celery Beat Schedule (Optional Customization)

To change daily aggregation time, edit `backend/celery_app.py`:

```python
'calculate-prompt-performance-daily': {
    'task': 'calculate_prompt_performance_daily',
    'schedule': crontab(hour=2, minute=30),  # Change to 2:30 AM UTC
    'options': {'queue': 'default'}
},
```

Then restart celery-beat:
```bash
docker-compose restart celery-beat
```

---

## Performance Optimization

### Database Indexes

All necessary indexes are created automatically in the migration. To verify:

```bash
psql $DATABASE_URL -c "
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('prompt_templates', 'prompt_performance', 'trading_signals')
AND indexname LIKE 'idx_%';
"
```

Should show 15+ indexes.

### Caching

Prompt templates are cached in-memory by `LLMService`. Cache is per-worker process.

**Clear cache** after prompt updates:
- Restart: `docker-compose restart backend celery-worker`
- Or wait: Cache is automatically refreshed on next prompt update

### Query Optimization

For large datasets, add composite indexes:

```sql
-- If you have millions of signals
CREATE INDEX idx_signals_generated_outcome 
ON trading_signals(generated_at, outcome, prompt_template_id)
WHERE outcome IN ('win', 'loss');

-- If you query performance by strategy frequently
CREATE INDEX idx_performance_strategy_date 
ON prompt_performance(strategy_id, date DESC)
WHERE strategy_id IS NOT NULL;
```

---

## Troubleshooting

### Issue: Migration Fails

**Symptom**: SQL error during migration

**Solution**:
1. Check database connection: `psql $DATABASE_URL -c "\l"`
2. Check for existing tables: `psql $DATABASE_URL -c "\d prompt_templates"`
3. If table exists, drop and recreate: `DROP TABLE IF EXISTS prompt_templates CASCADE;`
4. Re-run migration

### Issue: Celery Tasks Not Running

**Symptom**: No performance data being calculated

**Check**:
```bash
# Is Celery Beat running?
docker-compose ps | grep celery-beat

# Check Beat logs
docker-compose logs celery-beat | grep ERROR

# Check worker logs
docker-compose logs celery-worker | grep calculate_prompt_performance
```

**Solution**:
```bash
# Restart Beat
docker-compose restart celery-beat

# Manually trigger task
docker-compose exec celery-worker celery -A backend.celery_app call calculate_prompt_performance_daily
```

### Issue: Prompts Not Loading

**Symptom**: Signals still use hardcoded prompts

**Check**:
```bash
# Are prompts in database?
psql $DATABASE_URL -c "SELECT COUNT(*) FROM prompt_templates WHERE is_active = true;"

# Check backend logs
docker-compose logs backend | grep "Loaded prompt"
```

**Solution**:
1. Verify seed data was loaded
2. Check `is_active` and `is_default` flags
3. Restart backend: `docker-compose restart backend`

### Issue: Performance Metrics Missing

**Symptom**: No data in `prompt_performance` table

**Check**:
```bash
# Do signals have outcomes?
psql $DATABASE_URL -c "SELECT outcome, COUNT(*) FROM trading_signals GROUP BY outcome;"

# Do signals have prompt_template_id?
psql $DATABASE_URL -c "SELECT COUNT(*) FROM trading_signals WHERE prompt_template_id IS NOT NULL;"
```

**Solution**:
1. Update signal outcomes (see Step 5.1)
2. Manually run calculation: `calculate_prompt_performance_daily.delay()`
3. Check Celery worker logs for errors

---

## Security Considerations

### SQL Injection

✅ **Protected**: All database queries use SQLAlchemy ORM with parameter binding.

### Jinja2 Injection

✅ **Protected**: Sandboxed Jinja2 environment prevents code execution.

### API Authentication

⚠️ **TODO**: Add authentication middleware if exposing publicly:

```python
# backend/main.py
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.get("/api/v1/prompts/")
async def list_prompts(credentials: HTTPBearer = Depends(security)):
    # Verify token
    ...
```

### Rate Limiting

⚠️ **Consider**: Add rate limiting for API endpoints:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/api/v1/prompts/")
@limiter.limit("10/minute")
async def create_prompt(...):
    ...
```

---

## Maintenance

### Weekly Tasks

- [ ] Review performance metrics
- [ ] Check for failed Celery tasks
- [ ] Monitor database growth
- [ ] Review API error logs

### Monthly Tasks

- [ ] Analyze prompt performance trends
- [ ] Update underperforming prompts
- [ ] Backup prompt templates
- [ ] Review and cleanup old performance data

### Quarterly Tasks

- [ ] Audit prompt usage
- [ ] Optimize database indexes
- [ ] Review and update documentation
- [ ] Test disaster recovery procedure

---

## Support & Resources

- **User Guide**: `docs/PROMPT_SYSTEM_USER_GUIDE.md`
- **Implementation Status**: `IMPLEMENTATION_PROGRESS.md`
- **OpenSpec Design**: `openspec/changes/add-configurable-prompt-system/`
- **API Documentation**: http://localhost:8000/docs
- **Database Schema**: `database/migrations/add_prompt_templates.sql`

---

## Success Criteria

✅ **Deployment is successful if**:

1. All 6 default prompts loaded
2. API endpoints return 200 OK
3. Signals include `prompt_template_id`
4. Celery Beat schedule is active
5. Performance metrics are calculated daily
6. No errors in logs for 24 hours

---

**Deployment Checklist Complete!**

Run through each step sequentially and verify at each stage. If issues arise, refer to the Troubleshooting section.

**Last Updated**: 2025-10-25
**Version**: 1.0.0

