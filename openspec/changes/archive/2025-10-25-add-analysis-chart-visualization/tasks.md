# Implementation Tasks

## 1. Backend - Enhance Analysis Service
- [x] 1.1 Update `ComprehensiveAnalysis` schema to include chart URLs
- [x] 1.2 Modify analysis generation to create chart after indicator calculation
- [x] 1.3 Use existing `ChartService` to generate chart
- [x] 1.4 Upload chart to MinIO and get public URL
- [x] 1.5 Include chart URLs in analysis response

## 2. Frontend - Chart Display
- [x] 2.1 Add chart display section to `analysis.html`
- [x] 2.2 Show interactive Plotly chart using chart HTML (via iframe)
- [x] 2.3 Add chart download button (JPEG)
- [x] 2.4 Add chart toggle (show/hide)
- [x] 2.5 Reference 7-panel layout from `reference/webapp/services/chart_service.py`

## 3. Chart Layout Reference
- [x] 3.1 Review `reference/webapp/services/chart_service.py` layout
- [x] 3.2 Ensure 7 subplots match reference: Price, SuperTrend, Volume, MACD, RSI, OBV, ATR
- [x] 3.3 Verify max/min/avg annotations are working (via existing ChartService)
- [x] 3.4 Confirm latest value markers (yellow dots)
- [x] 3.5 Test interactive features (zoom, pan, hover) - Plotly built-in

## 4. Testing
- [x] 4.1 Test chart generation for TSLA, NVDA, AAPL
- [x] 4.2 Verify all 7 subplots display correctly
- [x] 4.3 Test chart download functionality
- [x] 4.4 Verify chart matches analysis indicators
- [x] 4.5 Test mobile responsiveness (iframe responsive)

## 5. Documentation
- [x] 5.1 Update analysis documentation
- [x] 5.2 Document chart reference to `reference/webapp/services/chart_service.py`
- [x] 5.3 Create user guide for chart features

## 6. OpenSpec Validation
- [x] 6.1 Validate with `openspec validate add-analysis-chart-visualization --strict`
- [x] 6.2 Update tasks to mark completion

