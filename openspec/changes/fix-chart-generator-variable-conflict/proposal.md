# Fix Chart Generator Variable Name Conflict

## Summary

**Why**: The `generate_chart` method in `chart_generator.py` has a variable name conflict where the `indicators` parameter (a `TechnicalIndicators` Pydantic model) shadows the imported `indicators` module from `stock_indicators` library, causing `AttributeError: 'TechnicalIndicators' object has no attribute 'get_sma'`.

**What Changes**: 
- Rename the imported `indicators` module to `stock_indicators_lib` to avoid conflict
- Update all references to use the renamed import
- Fix the bug in `generate_chart` method where it was trying to use the parameter instead of the library

**Impact**: 
- Chart generation will work correctly
- All IBKR workflows can generate charts successfully
- No more AttributeError when generating charts

## Problem Statement

When running `ibkr_trading_signal_workflow`, the `generate_daily_chart` task fails with:

```
AttributeError: 'TechnicalIndicators' object has no attribute 'get_sma'
```

The error occurs in `chart_generator.py` line 354:
```python
'sma_20': stock_indicators.get_sma(quotes, 20),
```

The issue is that `stock_indicators` was assigned the value of the `indicators` parameter (a `TechnicalIndicators` object) instead of using the imported `indicators` module from `stock_indicators` library.

## Root Cause

1. **Import statement**: `from stock_indicators import indicators, Quote`
2. **Method parameter**: `indicators: Optional[TechnicalIndicators] = None`
3. **Variable assignment**: `stock_indicators = indicators  # Avoid name conflict`

The parameter `indicators` shadows the imported module, so when the code tries to use `stock_indicators.get_sma()`, it's actually trying to call a method on the `TechnicalIndicators` Pydantic model object, which doesn't have that method.

## Proposed Solution

### 1. Rename Import to Avoid Conflict
Change the import to use a different name:
```python
from stock_indicators import indicators as stock_indicators_lib, Quote
```

### 2. Update All References
Update all code that uses the `indicators` module to use `stock_indicators_lib` instead.

### 3. Fix generate_chart Method
Remove the incorrect variable assignment and use the renamed import directly.

## Success Criteria

- [ ] Chart generation works without errors
- [ ] All IBKR workflows can generate charts
- [ ] No variable name conflicts
- [ ] Code is clear and maintainable

## Implementation Plan

1. **Fix Import Statement**
   - Rename `indicators` import to `stock_indicators_lib`
   - Update all references in the file

2. **Fix generate_chart Method**
   - Remove incorrect variable assignment
   - Use `stock_indicators_lib` directly

3. **Test**
   - Test chart generation in workflow
   - Verify no errors occur
   - Test via API trigger

## Breaking Changes

None - this is a bug fix.

## Testing Strategy

1. **Unit Test**: Test chart generation with sample data
2. **Integration Test**: Test via workflow execution
3. **API Test**: Trigger workflow via API and verify chart generation

## Timeline

- Fix implementation: 15 minutes
- Testing: 15 minutes
- **Total**: ~30 minutes

