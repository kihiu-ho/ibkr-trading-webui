# Group Artifacts by Symbol and Type

## Problem

Currently, artifacts are grouped only by `execution_id` (workflow execution), which shows all artifacts from the same workflow run together. However, users want to see artifacts organized by:
1. **Symbol** (e.g., TSLA, NVDA) - primary grouping
2. **Type** (charts, LLM analysis, signals, etc.) - secondary grouping within each symbol

This makes it easier to:
- See all artifacts for a specific symbol together
- Compare different types of analysis (charts, LLM, signals) for the same symbol
- Understand the complete analysis pipeline for each symbol

## Root Cause

The current `groupArtifacts()` function in `artifacts.html` groups artifacts by `execution_id` only, without considering symbol or type as grouping criteria.

## Solution

### Frontend Changes:
1. **Modify `groupArtifacts()` function**:
   - Group artifacts first by `symbol`
   - Within each symbol group, sub-group by `type` (chart, llm, signal, etc.)
   - Maintain execution metadata for display

2. **Update Group Header Display**:
   - Show symbol name prominently
   - Show artifact counts by type
   - Display workflow/execution info as secondary information

3. **Update Group Content Display**:
   - Show artifacts organized by type within each symbol group
   - Use visual separators or badges to distinguish types
   - Maintain existing artifact card display

### Backend Changes:
- No backend changes required - all data is already available in the artifact objects

## Impact

- **User Experience**: Better organization of artifacts by symbol and type
- **Visual Clarity**: Easier to see all analysis for a specific symbol
- **No Breaking Changes**: Existing functionality preserved, only grouping logic changed

## Implementation Notes

- Update `groupArtifacts()` to create nested structure: `{symbol: {type: [artifacts]}}`
- Update template to render nested groups
- Maintain backward compatibility with existing artifact data structure
- Test with multiple symbols and types

