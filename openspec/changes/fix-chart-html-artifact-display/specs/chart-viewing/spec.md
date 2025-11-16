## MODIFIED Requirements

### Requirement: Chart Detail View
The chart detail experience SHALL surface regenerated charts and provide guidance when only an HTML fallback exists.

#### Scenario: HTML fallback guidance
- **WHEN** a chart artifact's `image_path` ends with `.html`
- **THEN** the detail view SHALL replace the broken `<img>` with a warning state that links directly to the stored HTML file
- **AND** the warning SHALL explain that the backend is regenerating a PNG and provide a "Retry" action that re-fetches `/api/artifacts/{id}/image?t=timestamp`
- **AND** once the API returns a valid JPEG, the view SHALL automatically swap back to the rendered image without requiring a full page reload

#### Scenario: Market data snapshot display
- **WHEN** the artifact detail view loads
- **THEN** the market data table SHALL render using the API response populated from `market_data_snapshot`
- **AND** the UI SHALL stop showing "No market data" placeholders when the snapshot contains bars
- **AND** if the API responds with 404/500, the view SHALL show the existing retry affordance with the error message provided by the backend
