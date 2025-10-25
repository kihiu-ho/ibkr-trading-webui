# .env File Syntax Guide

## ✅ Fixed: "Trading: command not found" Error

### **Problem**
```bash
./start-webapp.sh
# Error: Trading: command not found
```

**Cause**: `.env` file had a line with unquoted value containing spaces:
```bash
APP_NAME=IBKR Trading WebApp  ❌ WRONG
```

When bash sources this, it interprets it as:
- Set `APP_NAME=IBKR`
- Then try to execute command `Trading` with argument `WebApp`
- Result: "Trading: command not found"

**Fix**: Add quotes around values with spaces:
```bash
APP_NAME="IBKR Trading WebApp"  ✅ CORRECT
```

---

## 📋 .env File Syntax Rules

### **Rule 1: Quote Values with Spaces**

```bash
# ❌ WRONG - Will cause "command not found" errors
APP_NAME=IBKR Trading WebApp
DESCRIPTION=This is my app

# ✅ CORRECT - Use double quotes
APP_NAME="IBKR Trading WebApp"
DESCRIPTION="This is my app"
```

### **Rule 2: No Quotes Needed for Single Words**

```bash
# ✅ Both are correct
DATABASE_HOST=localhost
DATABASE_HOST="localhost"

# ✅ Prefer without quotes for simple values
DEBUG=true
PORT=8000
ENVIRONMENT=production
```

### **Rule 3: No Spaces Around Equals Sign**

```bash
# ❌ WRONG - Spaces around =
DATABASE_URL = postgresql://...
APP_NAME = "My App"

# ✅ CORRECT - No spaces
DATABASE_URL=postgresql://...
APP_NAME="My App"
```

### **Rule 4: No `export` Keyword**

```bash
# ❌ WRONG - .env files don't need export
export DATABASE_URL=postgresql://...
export APP_NAME="My App"

# ✅ CORRECT - Just key=value
DATABASE_URL=postgresql://...
APP_NAME="My App"
```

### **Rule 5: Comments Start with #**

```bash
# ✅ CORRECT - Comments
# This is a comment
DATABASE_URL=postgresql://...  # Inline comment works too

# ❌ WRONG - Uncommented text
This will cause errors
DATABASE_URL=postgresql://...
```

### **Rule 6: Empty Lines Are OK**

```bash
# ✅ CORRECT - Empty lines for readability
DATABASE_URL=postgresql://...

APP_NAME="My App"

DEBUG=true
```

### **Rule 7: Multi-line Values Need Quotes**

```bash
# ✅ CORRECT - Multi-line with quotes
DESCRIPTION="This is a long
description that spans
multiple lines"

# ❌ WRONG - Without quotes
DESCRIPTION=This is a long
description that spans
multiple lines
```

---

## 🔍 Common Issues & Fixes

### **Issue 1: "command not found" Errors**

**Symptoms**: 
```bash
./start-webapp.sh
# Error: Trading: command not found
# Error: Secret: command not found
```

**Cause**: Unquoted values with spaces

**Fix**: Add quotes
```bash
# Before
APP_NAME=IBKR Trading WebApp
SECRET_KEY=my secret key

# After
APP_NAME="IBKR Trading WebApp"
SECRET_KEY="my secret key"
```

### **Issue 2: Variables Not Set**

**Symptoms**:
```bash
docker-compose exec backend printenv APP_NAME
# Output: (empty or wrong value)
```

**Cause**: Spaces around `=` sign

**Fix**: Remove spaces
```bash
# Before
APP_NAME = "My App"

# After
APP_NAME="My App"
```

### **Issue 3: Unexpected Behavior**

**Symptoms**: Variables have wrong values or cause parsing errors

**Cause**: Special characters not escaped

**Fix**: Use quotes and escape if needed
```bash
# Passwords with special characters
PASSWORD="p@ssw0rd!#$"

# URLs with parameters
DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"

# Values with quotes inside
MESSAGE="He said \"Hello\""
```

---

## ✅ Correct .env File Example

```bash
# ========================================
# Database Configuration
# ========================================
DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/dbname?sslmode=require"

# ========================================
# Application Settings
# ========================================
APP_NAME="IBKR Trading WebApp"
DEBUG=true
ENVIRONMENT=development
SECRET_KEY="change-this-secret-key-in-production"

# ========================================
# OpenAI Configuration
# ========================================
OPENAI_API_KEY="sk-1234567890abcdef"
OPENAI_API_BASE="https://api.openai.com/v1"
OPENAI_MODEL="gpt-4-turbo-preview"

# ========================================
# IBKR Configuration
# ========================================
IBKR_ACCOUNT_ID=DU1234567
IBKR_API_BASE_URL="https://localhost:5055/v1/api"

# ========================================
# MinIO Configuration
# ========================================
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_USE_SSL=false

# ========================================
# Redis Configuration
# ========================================
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/1"
```

---

## 🧪 How to Validate Your .env File

### **Method 1: Source Test (Quick)**
```bash
# Test if .env can be sourced without errors
set -a && source .env && set +a && echo "✓ .env syntax is valid"
```

### **Method 2: Check for Common Issues**
```bash
# Check for unquoted values with spaces
grep -n "^[A-Z_]*=[^\"'].*\s" .env

# Check for spaces around =
grep -n ".*\s=\s.*" .env

# Check for export keywords
grep -n "^export " .env
```

### **Method 3: Visual Inspection**
Look for these patterns in your `.env`:
- ❌ `KEY=value with spaces` (missing quotes)
- ❌ `KEY = value` (spaces around =)
- ❌ `export KEY=value` (unnecessary export)
- ✅ `KEY="value with spaces"` (correct)
- ✅ `KEY=single_value` (correct)

---

## 🛠️ Auto-Fix Script

Save this as `fix-env-syntax.sh`:

```bash
#!/bin/bash
# Auto-fix common .env syntax issues

cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Fix: Remove export keywords
sed -i.tmp 's/^export //' .env

# Fix: Remove spaces around =
sed -i.tmp 's/ *= */=/' .env

# Note: Manual fix needed for unquoted spaces
# Run: grep -n "^[A-Z_]*=[^\"'].*\s" .env
# Then add quotes manually

rm .env.tmp
echo "✓ Basic fixes applied. Check .env for unquoted values with spaces."
```

---

## 📚 Best Practices

### **1. Use Quotes Liberally**
When in doubt, use quotes. They don't hurt and prevent issues:
```bash
# Always safe
APP_NAME="My App"
DATABASE_URL="postgresql://..."
```

### **2. Use Comments for Sections**
```bash
# ========================================
# Section Name
# ========================================
KEY=value
```

### **3. Keep Secrets in .env, Not in Code**
```bash
# ✅ Good - In .env
SECRET_KEY="your-secret-here"

# ❌ Bad - In code
# SECRET_KEY = "hardcoded-secret"
```

### **4. Document Expected Format**
```bash
# Database URL format:
# postgresql+psycopg2://user:password@host:port/dbname
DATABASE_URL="postgresql+psycopg2://..."
```

### **5. Use env.example as Template**
```bash
# In env.example (no real values)
DATABASE_URL="postgresql://user:pass@host/db"
APP_NAME="My App Name"

# Users copy and fill in:
cp env.example .env
nano .env
```

---

## 🎯 Quick Reference

| ✅ DO | ❌ DON'T |
|-------|----------|
| `KEY="value with spaces"` | `KEY=value with spaces` |
| `KEY=simple_value` | `KEY = value` |
| `# Comments` | `Uncommented text` |
| `PASSWORD="p@ss"` | `export PASSWORD=p@ss` |
| Test after changes | Assume it works |

---

## 🚀 After Fixing .env

Once your `.env` syntax is correct:

```bash
# Test it
set -a && source .env && set +a && echo "✓ Syntax OK"

# Start services
./start-webapp.sh

# Should see:
# ✓ Found .env file
# ℹ Loading environment variables...
# ✓ DATABASE_URL loaded: postgresql://...
# (No "command not found" errors)
```

---

## 📖 Summary

**Problem**: `.env` file syntax errors cause "command not found"  
**Solution**: Follow proper .env syntax (quotes, no spaces, no export)  
**Your Fix**: Changed `APP_NAME=IBKR Trading WebApp` to `APP_NAME="IBKR Trading WebApp"`  
**Status**: ✅ **FIXED**

**Key Rule**: **Always quote values with spaces!**

---

**Last Updated**: 2024-07-29  
**Status**: ✅ Complete

