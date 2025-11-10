# Fix Chart Generator Variable Name Conflict - Implementation Tasks

## Implementation Checklist

### Phase 1: Fix Import and Variable Names

- [x] 1.1 Rename `indicators` import to `stock_indicators_lib` to avoid conflict
- [x] 1.2 Update `generate_chart` method to use `stock_indicators_lib` directly
- [x] 1.3 Remove incorrect variable assignment `stock_indicators = indicators`
- [ ] 1.4 Verify all references to `indicators` module are updated

### Phase 2: Testing

- [ ] 2.1 Test chart generation locally
- [ ] 2.2 Trigger workflow via API
- [ ] 2.3 Verify chart generation succeeds
- [ ] 2.4 Check for any remaining errors

### Phase 3: Validation

- [ ] 3.1 All IBKR workflows can generate charts
- [ ] 3.2 No AttributeError exceptions
- [ ] 3.3 Charts are saved correctly
- [ ] 3.4 Workflow completes successfully

## Testing Commands

```bash
# Test chart generation in container
docker exec ibkr-airflow-scheduler python3 -c "
from dags.utils.chart_generator import ChartGenerator
from dags.models.market_data import MarketData, OHLCVBar
from dags.models.chart import ChartConfig, Timeframe
from datetime import datetime
# Create test data and generate chart
"

# Trigger workflow via API
curl -X POST \
  -u airflow:airflow \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/airflow/dags/ibkr_trading_signal_workflow/dagRuns \
  -d '{}'
```

## Success Criteria

- ✅ Chart generation works without errors
- ✅ All workflows can generate charts
- ✅ No variable name conflicts
- ✅ Code is maintainable

