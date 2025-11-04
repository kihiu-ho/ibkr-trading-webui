# OpenSpec: Data Persistence Issue Diagnosis & Fix

**Status**: 🚧 In Progress  
**Created**: 2025-10-29  
**Author**: AI Agent  
**Category**: Bug Fix & Data Verification

## Problem Statement

No data is being stored in PostgreSQL database:
- No charts in `charts` table
- No strategies in `strategies` table
- No LLM analyses in `llm_analyses` table

## Root Cause Analysis

### Potential Issues

1. **Database Tables Not Created** - Tables may not exist
2. **Workflow Errors** - Charts/analyses save failing silently
3. **Transaction Rollbacks** - Database commits not happening
4. **Missing Base Data** - No strategies/symbols seeded
5. **Column Name Mismatch** - DataFrame columns (uppercase vs lowercase)

## Diagnostic Plan

### Step 1: Verify Database Tables Exist
- Check if `charts` table exists
- Check if `llm_analyses` table exists
- Check if `strategies` table has data
- Check if `symbols` table has data

### Step 2: Check Workflow Execution Logs
- Review celery worker logs for errors
- Check if chart persistence throws exceptions
- Verify LLM analysis persistence

### Step 3: Test Data Creation
- Manually insert test strategy
- Run workflow with explicit logging
- Verify each persistence step

## Solution

### Fix 1: Ensure Database Tables Exist
```sql
-- Verify tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```

### Fix 2: Seed Base Data
- Create test strategies
- Populate symbols from cache
- Verify codes table

### Fix 3: Fix DataFrame Column Names
- Handle both uppercase and lowercase columns
- Update persistence logic to be case-insensitive

### Fix 4: Add Transaction Management
- Ensure db.commit() is called
- Add error handling and logging

## Implementation Steps

1. ✅ Create diagnostic script
2. ✅ Check database schema
3. ✅ Seed base data (strategies, symbols)
4. ✅ Fix workflow errors
5. ✅ Run test workflow
6. ✅ Verify data persistence

