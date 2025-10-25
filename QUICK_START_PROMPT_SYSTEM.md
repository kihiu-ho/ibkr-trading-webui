# 🚀 Quick Start Guide: Configurable Prompt System

## ⚡ Get Started in 5 Minutes

### **Step 1: Deploy the System** (2 minutes)

```bash
# 1. Ensure DATABASE_URL is set in your .env file
# The script will automatically load it from .env

# 2. Run deployment script
./deploy_prompt_system.sh

# Output:
# Loading environment variables from .env file...
# ✓ Environment variables loaded
# [1/8] Backing up database... ✓
# [2/8] Running migrations... ✓
# [3/8] Verifying tables... ✓
# [4/8] Seeding prompts... ✓
# [5/8] Installing dependencies... ✓
# [6/8] Restarting services... ✓
# [7/8] Running tests... ✓
# [8/8] Verifying deployment... ✓
# 
# Deployment Completed Successfully! 🎉
```

> **Note**: If `.env` file doesn't exist or DATABASE_URL is not set, you can still export it manually:
> ```bash
> export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
> ./deploy_prompt_system.sh
> ```

### **Step 2: Access Prompt Manager** (1 minute)

```bash
# Open your browser
http://localhost:8000/prompts
```

You should see:
- ✅ Monaco Editor with Jinja2 highlighting
- ✅ 3 seed prompts (Daily Analysis, Weekly Analysis, Consolidation)
- ✅ "New Prompt" button

### **Step 3: Create Your First Prompt** (2 minutes)

1. Click **"New Prompt"** button

2. Fill in the form:
   - **Name**: `My Custom Analysis`
   - **Type**: `analysis`
   - **Language**: `en`
   - **Description**: `Custom analysis for my strategy`

3. Write your Jinja2 template in Monaco Editor:
```jinja2
Analysis for {{ symbol }} on {{ today|dateformat('%Y-%m-%d') }}

Current Price: ${{ current_price|round(2) }}

{% if rsi > 70 %}
⚠️ **OVERBOUGHT**: RSI at {{ rsi|round(1) }}
Consider taking profits or tightening stops.
{% elif rsi < 30 %}
📈 **OVERSOLD**: RSI at {{ rsi|round(1) }}
Potential buying opportunity if trend confirms.
{% else %}
✅ **NEUTRAL**: RSI at {{ rsi|round(1) }}
Monitor for breakout signals.
{% endif %}

**ATR (14)**: {{ atr|round(2) }}
**Stop Loss**: ${{ (current_price - 2 * atr)|round(2) }}
**Target Price**: ${{ (current_price + 3 * atr)|round(2) }}

**Strategy**: {{ strategy.name }}
**Timeframe**: {{ timeframe|upper }}
```

4. Click **"Validate"** → Should show ✅ "Template syntax is valid!"

5. Click **"Preview"** and enter sample context:
```json
{
  "symbol": "AAPL",
  "current_price": 175.50,
  "rsi": 68.5,
  "atr": 2.30,
  "timeframe": "daily",
  "strategy": {"name": "Momentum Strategy"}
}
```

6. Click **"Render"** → See your formatted output

7. Click **"Save Prompt"** → Done! ✅

---

## 🧪 Verify It's Working

### **Test 1: API Endpoint**
```bash
curl http://localhost:8000/api/v1/prompts/ | jq
```

Expected output:
```json
{
  "templates": [
    {
      "id": 1,
      "name": "My Custom Analysis",
      "template_type": "analysis",
      "is_active": true,
      ...
    }
  ],
  "total": 4
}
```

### **Test 2: Database**
```bash
psql "$DATABASE_URL" -c "SELECT id, name, template_type FROM prompt_templates;"
```

Expected output:
```
 id |              name               | template_type 
----+---------------------------------+---------------
  1 | Daily Chart Analysis (EN)       | analysis
  2 | Weekly Chart Analysis (EN)      | analysis
  3 | Consolidate Daily & Weekly (EN) | consolidation
  4 | My Custom Analysis              | analysis
```

### **Test 3: Frontend**
Open `http://localhost:8000/prompts` and verify:
- ✅ Page loads without errors
- ✅ Monaco Editor visible
- ✅ Your custom prompt appears in list
- ✅ Can edit and save changes

---

## 📊 Monitor Performance

### **View Prompt Performance**
Once your prompts generate signals and outcomes are recorded:

1. Click **"View Performance"** on any prompt
2. See metrics:
   - Total signals generated
   - Win rate (e.g., 65.3%)
   - Average R-multiple (e.g., 2.1R)
   - Total profit/loss (e.g., +$8,500)
3. Review daily breakdown table

### **Compare Prompts**
```bash
curl "http://localhost:8000/api/v1/prompts/compare?prompt_id_1=1&prompt_id_2=4" | jq
```

---

## 🛠️ Common Tasks

### **Create Strategy-Specific Prompt**
1. Create new prompt
2. Set **Strategy** dropdown to specific strategy (not "Global")
3. This prompt will override global prompt for that strategy

### **Update Existing Prompt**
1. Click **Edit** button
2. Modify template
3. Click **Save** → Version automatically increments (v1 → v2)

### **Duplicate Prompt**
1. Click **Duplicate** button
2. Modify name and template
3. Click **Save** → Creates new prompt based on original

### **Deactivate Prompt**
1. Edit prompt
2. Uncheck **"Active"** checkbox
3. Click **Save** → Prompt no longer used for new signals

---

## 🧰 Troubleshooting

### **Problem: Deployment script fails**
**Solution**: Check DATABASE_URL is set correctly
```bash
echo $DATABASE_URL
# Should output: postgresql://...
```

### **Problem: Monaco Editor doesn't load**
**Solution**: Check browser console for errors. Monaco loads from CDN.
```bash
# Test CDN access
curl -I https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/loader.js
```

### **Problem: No prompts showing in UI**
**Solution**: Verify seed data was loaded
```bash
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM prompt_templates;"
# Should return: 3 or more
```

### **Problem: Template validation fails**
**Solution**: Check Jinja2 syntax
- Variables: `{{ variable }}`
- Control flow: `{% if condition %} ... {% endif %}`
- Filters: `{{ value|filter }}`

---

## 📚 Learn More

### **Jinja2 Variables Available**
- `symbol` - Stock ticker (e.g., "AAPL")
- `current_price` - Latest price
- `rsi` - RSI indicator value
- `atr` - ATR value
- `macd` - MACD values
- `ma20`, `ma50`, `ma200` - Moving averages
- `strategy` - Strategy parameters (dict)
- `timeframe` - Chart timeframe
- `now` - Current datetime
- `today` - Current date

### **Jinja2 Filters Available**
- `|round(2)` - Round to 2 decimals
- `|percent` - Format as percentage (0.65 → 65.00%)
- `|currency` - Format as currency ($1,234.56)
- `|upper` - Uppercase
- `|lower` - Lowercase
- `|dateformat('%Y-%m-%d')` - Format date
- `|abs` - Absolute value
- `|default_if_none('N/A')` - Default value

### **Control Flow Examples**
```jinja2
{# Conditionals #}
{% if price > 100 %}
  Price is high
{% elif price > 50 %}
  Price is medium
{% else %}
  Price is low
{% endif %}

{# Loops #}
{% for indicator in indicators %}
  - {{ indicator.name }}: {{ indicator.value }}
{% endfor %}
```

---

## 🎯 Next Steps

1. ✅ **Deployed** - System is running
2. ✅ **Tested** - Created first prompt
3. ⏩ **Integrate** - Use prompts in your trading workflow
4. ⏩ **Monitor** - Track performance metrics
5. ⏩ **Optimize** - Iterate on prompt templates based on data

---

## 🆘 Need Help?

### **Documentation**
- `PROJECT_COMPLETE.md` - Full implementation details
- `SYSTEM_READY_SUMMARY.md` - System overview
- `FRONTEND_IMPLEMENTATION_COMPLETE.md` - Frontend guide

### **API Documentation**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### **Run Tests**
```bash
./run_tests.sh
```

### **Verify Deployment**
```bash
./verify_deployment.sh
```

### **Rollback (Emergency)**
```bash
./rollback_prompt_system.sh backup_YYYYMMDD_HHMMSS.sql
```

---

## ✅ You're All Set!

Your **Configurable Prompt System** is now live and ready to:
- ✅ Manage LLM prompts via web UI
- ✅ Test prompts with live preview
- ✅ Track performance metrics
- ✅ Optimize prompts based on data
- ✅ Create strategy-specific customizations

**Enjoy your new prompt management system!** 🎉

