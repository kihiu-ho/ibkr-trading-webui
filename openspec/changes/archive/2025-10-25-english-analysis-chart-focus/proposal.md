# English Translation and Chart-Focused Analysis

## Why
Currently, the comprehensive technical analysis system:
1. Generates reports primarily in Chinese (default language)
2. Shows text report prominently with chart as secondary
3. Lacks complete English translation

Users need:
- Full English language support for international traders
- Chart as the primary analysis output (visual-first approach)
- Concise text summary instead of lengthy reports
- Professional English financial terminology

## What Changes
1. **Complete English Translation:**
   - Implement full `_generate_english_report()` method
   - Translate all Chinese terms to English financial terminology
   - Set default language to English
   - Keep Chinese as optional secondary language

2. **Chart-Focused Analysis:**
   - Make interactive chart the primary/default view
   - Show chart first, text summary second
   - Replace lengthy markdown report with concise bullet points
   - Emphasize visual analysis over text analysis
   - Keep full report available but collapsed/optional

## Impact
- **Affected specs:** technical-analysis (enhancement)
- **Affected code:**
  - Modified: `backend/services/analysis_service.py` - Full English report implementation
  - Modified: `backend/schemas/analysis.py` - Default language to English
  - Modified: `frontend/templates/analysis.html` - Chart-first UI, English labels
- **User impact:** English-speaking traders can use the system, visual-first approach
- **Breaking changes:** None - language parameter allows both Chinese and English

