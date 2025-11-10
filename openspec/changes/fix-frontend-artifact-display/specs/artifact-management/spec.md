# Artifact Management - Frontend Display Fixes

## MODIFIED Requirements

### Requirement: Market Data Table Display

The system SHALL display market data in a table format with proper loading states and error handling.

#### Scenario: Display Market Data with Loading States
- **Given** a chart artifact exists with ID 52
- **When** the artifact detail page is displayed
- **Then** the system SHALL show a loading spinner while fetching market data
- **And** the system SHALL display market data in a table when loaded
- **And** the system SHALL show an error message if loading fails
- **And** the system SHALL provide a refresh button to retry loading
- **And** the table SHALL format numbers correctly (2 decimal places for prices, comma-separated for volume)

#### Scenario: Handle Market Data Errors
- **Given** market data endpoint returns an error
- **When** the artifact detail page is displayed
- **Then** the system SHALL display an error message
- **And** the system SHALL provide a retry button
- **And** the system SHALL not show the loading spinner after error

### Requirement: Chart Image Display

The system SHALL display chart images with proper loading states and error handling.

#### Scenario: Display Chart Image with Loading States
- **Given** a chart artifact exists with ID 52
- **When** the artifact detail page is displayed
- **Then** the system SHALL show a loading spinner while loading the image
- **And** the system SHALL display the image when loaded
- **And** the system SHALL show an error message if image fails to load
- **And** the system SHALL provide a retry button
- **And** the system SHALL provide a link to open image in new tab

#### Scenario: Handle Image Loading Errors
- **Given** chart image fails to load
- **When** the artifact detail page is displayed
- **Then** the system SHALL display an error message
- **And** the system SHALL provide a retry button
- **And** the system SHALL show the image path for debugging

### Requirement: LLM Analysis Display

The system SHALL display LLM prompt and response with proper formatting and copy functionality.

#### Scenario: Display LLM Prompt and Response
- **Given** an LLM artifact exists with ID 54
- **When** the artifact detail page is displayed
- **Then** the system SHALL display prompt in a scrollable area
- **And** the system SHALL display response in a scrollable area
- **And** the system SHALL provide copy buttons for both prompt and response
- **And** the system SHALL show success/error feedback when copying
- **And** the system SHALL handle empty prompt/response gracefully

#### Scenario: Copy to Clipboard Functionality
- **Given** an LLM artifact with prompt and response
- **When** user clicks the copy button
- **Then** the system SHALL copy the text to clipboard
- **And** the system SHALL show "Copied!" feedback
- **And** the system SHALL handle clipboard API errors gracefully
- **And** the button SHALL return to normal state after 2 seconds

