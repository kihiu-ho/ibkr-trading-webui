# Fix Analysis None Value Formatting Error

## Why
The analysis generation is failing with a 500 Internal Server Error:
```
unsupported format string passed to NoneType.__format__
```

This occurs when indicator calculations return None values (e.g., for early data points where there isn't enough history to calculate SMA 200), and the Chinese report generation tries to format these None values using f-strings like `${value:.2f}`.

Python f-strings cannot format None values, causing the entire analysis generation to fail.

## What Changes
- Add safe formatting helper function for numeric values
- Replace direct f-string formatting with null-safe formatting
- Provide default values or "N/A" for None indicators
- Add error handling for individual indicator calculations
- Ensure analysis generation doesn't fail due to missing indicator values

## Impact
- **Affected specs:** technical-analysis (bug fix)
- **Affected code:**
  - Modified: `backend/services/analysis_service.py` - Add safe formatting and None handling
- **User impact:** Analysis generation succeeds even with incomplete indicator data
- **Breaking changes:** None - purely a bug fix

