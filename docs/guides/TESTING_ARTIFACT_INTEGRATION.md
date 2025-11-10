# Testing Guide: Artifact Workflow Integration

## Quick Start Testing

### Prerequisites
- Docker services running (`docker-compose up -d`)
- Backend restarted to apply template changes: `docker-compose restart backend`

---

## Test Scenario 1: Dashboard Visibility

**Objective**: Verify dashboard Quick Actions are clearly visible

### Steps
1. Navigate to `http://localhost:8000/`
2. Check the "Quick Actions" section

### Expected Results
- ✅ All 6 action buttons clearly visible with good contrast
- ✅ Icons are large and clear (Orders, Portfolio, Charts, MLflow, Airflow, Artifacts)
- ✅ Text labels are bold and readable
- ✅ Each button has distinct color (blue, green, indigo, pink, cyan, purple)
- ✅ Hover effects work smoothly

### Screenshot
Take a screenshot of the Quick Actions section for documentation.

---

## Test Scenario 2: Airflow Workflow Execution

**Objective**: Generate artifacts by running IBKR workflow

### Steps
1. Navigate to `http://localhost:8000/airflow`
2. Find the `ibkr_trading_signal_workflow` DAG
3. Click "Trigger" to start a new run
4. Wait for the workflow to complete (typically 2-5 minutes)

### Expected Results
- ✅ Workflow runs successfully
- ✅ All tasks turn green (success)
- ✅ No failed tasks

### What Artifacts Should Be Generated
- **Chart Artifacts**: 
  - TSLA Daily Chart
  - TSLA Weekly Chart
- **LLM Artifacts**:
  - Trading signal analysis from LLM
- **Signal Artifacts**:
  - Trading decision signal

---

## Test Scenario 3: Airflow Run Details - Artifact Display

**Objective**: View generated artifacts in Airflow run details modal

### Steps
1. On Airflow Monitor page (`http://localhost:8000/airflow`)
2. In the "Recent Runs" table, find the workflow run you just triggered
3. Click the eye icon (👁️) to view run details
4. Scroll down to the "Generated Artifacts" section

### Expected Results
- ✅ Modal opens showing run details
- ✅ "Generated Artifacts" section is visible
- ✅ 3+ artifact cards are displayed (charts + LLM + signal)
- ✅ Each artifact shows:
  - Artifact name
  - Type badge (LLM/Chart/Signal) with correct color
  - Step name (e.g., "generate_daily_chart")
  - Creation timestamp
- ✅ Artifacts are clickable
- ✅ Hover effect shows cursor pointer

### Screenshot
Capture the modal showing the artifacts section.

---

## Test Scenario 4: Navigation to Artifact Detail

**Objective**: Navigate from Airflow modal to artifact detail page

### Steps
1. From the run details modal, click on any artifact card
2. Should navigate to artifact detail page

### Expected Results
- ✅ Navigates to `/artifacts/{id}` URL
- ✅ Artifact detail page loads successfully
- ✅ Shows full artifact information:
  - Name, type, creation date
  - Workflow context (workflow_id, execution_id, step_name, dag_id)
  - Type-specific content:
    - **Chart**: Image preview
    - **LLM**: Prompt and response text
    - **Signal**: Trading action and confidence
- ✅ "View DAG" link works (navigates to `/workflows?dag=...`)

### Screenshot
Capture an LLM artifact detail page showing prompt/response.

---

## Test Scenario 5: Artifacts Page - Grouped View

**Objective**: Verify grouped view on artifacts page

### Steps
1. Navigate to `http://localhost:8000/artifacts`
2. Ensure "Grouped" view is selected (toggle at top-right)
3. Find the workflow execution group

### Expected Results
- ✅ Artifacts grouped by execution_id
- ✅ Group header shows:
  - Workflow name
  - Execution date/time
  - DAG ID
  - Artifact count (e.g., "3 artifacts")
- ✅ Click group header to expand/collapse
- ✅ First group expanded by default
- ✅ Artifacts within group match those in Airflow modal

### Screenshot
Capture the grouped view with one group expanded.

---

## Test Scenario 6: Empty State Handling

**Objective**: Verify behavior when no artifacts exist for a run

### Steps
1. In Airflow, find an old run that didn't generate artifacts (or trigger a DAG without artifact steps)
2. Click to view run details

### Expected Results
- ✅ Modal opens successfully
- ✅ "Generated Artifacts" section shows empty state:
  - Gray box icon
  - Message: "No artifacts generated"
- ✅ No errors in browser console

---

## Test Scenario 7: Flat View Toggle

**Objective**: Verify flat view on artifacts page works

### Steps
1. On artifacts page (`http://localhost:8000/artifacts`)
2. Click "List" view toggle
3. Verify artifacts display in flat list

### Expected Results
- ✅ View switches to flat grid layout
- ✅ All artifacts visible (not grouped)
- ✅ Toggle state persists on page refresh (sessionStorage)
- ✅ Clicking "Grouped" switches back

---

## Test Scenario 8: Error Handling

**Objective**: Verify graceful error handling

### Manual Test
1. Open browser DevTools → Network tab
2. Block requests to `/api/artifacts/` (using browser extensions or DevTools)
3. View Airflow run details

### Expected Results
- ✅ Modal still opens
- ✅ Empty state shown for artifacts
- ✅ Error logged to console (not shown to user)
- ✅ Rest of modal functionality works

---

## Test Scenario 9: Responsive Design

**Objective**: Verify mobile/tablet layouts

### Steps
1. Open browser DevTools
2. Toggle device emulation (iPhone, iPad)
3. Navigate through:
   - Dashboard
   - Airflow Monitor
   - Artifacts page
   - Run details modal

### Expected Results
- ✅ Dashboard Quick Actions stack vertically on mobile
- ✅ Airflow run details modal scrolls properly
- ✅ Artifact cards reflow to single column on mobile
- ✅ All text remains readable
- ✅ Touch targets are appropriately sized

---

## Regression Testing

### Verify Existing Features Still Work
- [ ] Orders page loads and functions
- [ ] Portfolio page displays positions
- [ ] Charts page works
- [ ] MLflow tracking page loads
- [ ] Sidebar navigation works
- [ ] IBKR authentication flow
- [ ] All API endpoints respond correctly

---

## Performance Validation

### Metrics to Check
1. **Page Load Time**: Dashboard < 1s
2. **Modal Open Time**: Airflow details < 500ms
3. **Artifact Fetch Time**: < 2s for 100 artifacts
4. **Browser Console**: No errors or warnings

### Tools
- Browser DevTools → Performance tab
- Network tab → Check request timing
- Console → Verify no errors

---

## Bug Reporting Template

If you find issues, report using this format:

```
**Issue**: [Brief description]
**Steps to Reproduce**:
1. 
2. 
3. 

**Expected**: [What should happen]
**Actual**: [What actually happens]
**Browser**: [Chrome/Firefox/Safari + version]
**Screenshot**: [Attach if applicable]
**Console Errors**: [Copy any errors from browser console]
```

---

## Success Criteria

All tests pass when:
- ✅ Dashboard Quick Actions are clearly visible
- ✅ Workflow generates artifacts successfully
- ✅ Artifacts appear in Airflow run details modal
- ✅ Navigation between pages works seamlessly
- ✅ Grouped and flat views both function correctly
- ✅ Empty states and error states handled gracefully
- ✅ Responsive design works on mobile/tablet
- ✅ No console errors during normal operation
- ✅ Performance meets expectations

---

## Next Steps After Testing

### If All Tests Pass ✅
1. Mark feature as production-ready
2. Add screenshots to documentation
3. Train users on new features
4. Monitor for issues in production

### If Issues Found ❌
1. Document issues using bug template
2. Prioritize by severity
3. Fix critical issues first
4. Re-test after fixes
5. Repeat until all tests pass

---

## Support

If you encounter issues or have questions:
- Check browser console for errors
- Review Docker logs: `docker-compose logs backend`
- Check Airflow logs in the UI
- Review `docs/implementation/PHASE_2_COMPLETE.md` for technical details

---

**Testing Version**: 1.0  
**Last Updated**: November 8, 2025  
**Feature**: Artifact Workflow Integration (Phase 2)

