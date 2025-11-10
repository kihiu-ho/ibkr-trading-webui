# Enhance Artifact Visualization

## Problem

1. **Artifact 47 (Chart)**: Currently only displays chart image and raw JSON. Needs to visualize:
   - Market data in table form (OHLC, volume, etc.)
   - Technical indicators in table form
   - Chart image display

2. **Artifact 49 (LLM)**: Currently displays prompt and response, but needs better visualization:
   - Clear input/output sections
   - Better formatting for readability
   - Enhanced display of LLM analysis

## Root Cause

- Chart artifacts have `chart_data` with indicators list, but no market data table
- LLM artifacts have prompt/response but display could be improved
- Frontend lacks structured table views for market data and indicators
- Backend doesn't provide market data endpoint for artifacts

## Solution

### Backend Changes:
1. **New API Endpoint**: `/api/artifacts/{id}/market-data` - Fetch market data for chart artifacts
2. **Enhanced Artifact Model**: Store market data in `chart_data` or `metadata` if available
3. **Market Data Service**: Retrieve latest market data for symbol from database or API

### Frontend Changes:
1. **Chart Artifact View**: 
   - Display market data table (OHLC, volume, date)
   - Display indicators table with values
   - Keep chart image display
   - Add tabs or sections for organized view

2. **LLM Artifact View**:
   - Enhanced prompt/response display
   - Better formatting with syntax highlighting if needed
   - Clear input/output sections with icons
   - Copy to clipboard functionality

## Impact

- **User Experience**: Better visualization of trading data
- **Data Accessibility**: Market data and indicators in structured format
- **LLM Analysis**: Clearer display of AI reasoning
- **No Breaking Changes**: Existing functionality preserved

## Implementation Notes

- Market data may need to be fetched from IBKR API or stored in database
- Indicators values may need to be calculated or stored
- Frontend will use Alpine.js for dynamic table rendering
- Responsive design for mobile/desktop

