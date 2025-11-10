# Tasks: Group Artifacts by Symbol and Type

## 1. Update Grouping Logic
- [ ] Modify `groupArtifacts()` function to group by symbol first
- [ ] Sub-group by type within each symbol
- [ ] Maintain execution metadata for display
- [ ] Update `groupedArtifacts` data structure

## 2. Update Group Header Display
- [ ] Show symbol name prominently in header
- [ ] Display artifact counts by type
- [ ] Show workflow/execution info as secondary
- [ ] Update header styling

## 3. Update Group Content Display
- [ ] Render artifacts organized by type within symbol groups
- [ ] Add visual separators or sections for each type
- [ ] Maintain existing artifact card display
- [ ] Update empty state handling

## 4. Test and Fix
- [ ] Test with single symbol
- [ ] Test with multiple symbols (TSLA, NVDA)
- [ ] Test with multiple types per symbol
- [ ] Test with missing symbols/types
- [ ] Verify all artifact types display correctly

## 5. Run IBKR Workflow
- [ ] Trigger IBKR workflow for TSLA
- [ ] Trigger IBKR workflow for NVDA
- [ ] Verify artifacts are created
- [ ] Verify grouping works with new artifacts

