# chart-viewing Specification

## Purpose
TBD - created by archiving change fix-charts-and-frontend. Update Purpose after archive.
## Requirements
### Requirement: Chart Gallery View
The system SHALL provide a gallery interface to display all generated technical analysis charts.

#### Scenario: User views chart gallery
- **WHEN** user navigates to /charts page
- **THEN** system displays all charts in a card grid layout
- **AND** each card shows chart thumbnail, symbol, date, and indicators used
- **AND** charts are sorted by generation date (newest first)

#### Scenario: User filters charts
- **WHEN** user enters symbol in filter input
- **THEN** system filters charts to show only matching symbol
- **AND** filter is applied instantly without page reload

#### Scenario: Empty state
- **WHEN** no charts exist or filter returns no results
- **THEN** system displays helpful empty state with "Generate Chart" button

### Requirement: Chart Detail View
The system SHALL allow users to view full-size interactive charts.

#### Scenario: User clicks chart card
- **WHEN** user clicks on a chart card in gallery
- **THEN** system displays full-size interactive chart in modal or new view
- **AND** chart supports zoom, pan, and hover tooltips
- **AND** user can download chart as JPEG

#### Scenario: User navigates between charts
- **WHEN** viewing chart detail
- **THEN** system provides next/previous navigation controls
- **AND** clicking next/previous loads adjacent chart

### Requirement: Chart Generation Form
The system SHALL provide an interface to generate new charts.

#### Scenario: User accesses generation form
- **WHEN** user clicks "Generate New Chart" button
- **THEN** system displays form with symbol input
- **AND** form shows available indicators with checkboxes
- **AND** form shows period and frequency options

#### Scenario: User generates chart
- **WHEN** user fills form and submits
- **THEN** system validates inputs
- **AND** system sends API request to generate chart
- **AND** system shows loading indicator during generation
- **AND** system displays success message when complete
- **AND** new chart appears in gallery

#### Scenario: Generation fails
- **WHEN** chart generation fails
- **THEN** system displays error message with details
- **AND** form remains populated for retry

### Requirement: Chart Management
The system SHALL allow users to delete unwanted charts.

#### Scenario: User deletes chart
- **WHEN** user clicks delete button on chart card
- **THEN** system requests confirmation
- **AND** on confirmation, system deletes chart from storage
- **AND** chart is removed from gallery
- **AND** system shows success notification

#### Scenario: Bulk operations
- **WHEN** user selects multiple charts
- **THEN** system enables bulk delete action
- **AND** user can delete all selected charts at once

### Requirement: Chart Metadata Display
The system SHALL display comprehensive metadata for each chart.

#### Scenario: Chart card shows metadata
- **WHEN** chart is displayed in gallery
- **THEN** card shows symbol, generation date, period, frequency
- **AND** card shows list of indicators used
- **AND** card shows file size
- **AND** card shows strategy name if associated

### Requirement: Auto-Refresh
The system SHALL automatically update the gallery when new charts are generated.

#### Scenario: New chart appears
- **WHEN** a new chart is generated (by user or background task)
- **THEN** gallery updates to show new chart within 10 seconds
- **AND** no page reload is required

### Requirement: Responsive Design
The system SHALL provide optimal viewing experience on all device sizes.

#### Scenario: Mobile view
- **WHEN** user accesses charts on mobile device
- **THEN** cards stack vertically in single column
- **AND** chart images scale appropriately
- **AND** all controls remain accessible

#### Scenario: Tablet view
- **WHEN** user accesses charts on tablet
- **THEN** cards display in 2-column grid
- **AND** charts remain interactive

#### Scenario: Desktop view
- **WHEN** user accesses charts on desktop
- **THEN** cards display in 3-4 column grid
- **AND** all features are fully accessible

### Requirement: Loading States
The system SHALL provide clear feedback during asynchronous operations.

#### Scenario: Loading charts
- **WHEN** gallery is loading charts
- **THEN** system displays skeleton loading cards
- **AND** loading state is visually distinct

#### Scenario: Generating chart
- **WHEN** user submits generation form
- **THEN** button shows loading spinner
- **AND** button is disabled during generation
- **AND** progress indicator shows status

