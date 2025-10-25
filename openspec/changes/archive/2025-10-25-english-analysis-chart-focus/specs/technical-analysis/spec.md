# English Translation and Chart-Focused Analysis - Spec Delta

## ADDED Requirements

### Requirement: Multi-Language Support
The system SHALL support both English and Chinese language for analysis reports with English as the default.

#### Scenario: Generate English analysis report
- **GIVEN** analysis is requested without specifying language
- **WHEN** the system generates the report
- **THEN** the system SHALL generate an English report by default
- **AND** SHALL use professional financial terminology
- **AND** SHALL translate all Chinese terms to English

#### Scenario: Generate Chinese analysis report
- **GIVEN** analysis is requested with language parameter "zh"
- **WHEN** the system generates the report
- **THEN** the system SHALL generate a Chinese report
- **AND** SHALL use proper Chinese financial terminology

#### Scenario: English financial terminology
- **GIVEN** an English report is generated
- **WHEN** displaying technical terms
- **THEN** the system SHALL use standard financial English:
  - "Strong Bullish" not "強烈看漲"
  - "Overbought" not "超買"
  - "Moving Average" not "移動平均線"
  - "Support/Resistance" not "支撐/阻力"

### Requirement: Chart-Focused Analysis Display (New)
The system SHALL present technical analysis with charts as the primary visual element.

#### Scenario: Chart displayed first
- **GIVEN** an analysis is generated with a chart
- **WHEN** the analysis page is displayed
- **THEN** the system SHALL show the interactive chart first
- **AND** SHALL display the chart expanded by default
- **AND** SHALL make the chart full-width for maximum visibility

#### Scenario: Text report minimized
- **GIVEN** an analysis is displayed
- **WHEN** the page loads
- **THEN** the system SHALL show a concise summary (not full report)
- **AND** SHALL collapse the full markdown report by default
- **AND** SHALL provide a "View Full Report" toggle button
- **AND** SHALL emphasize visual elements over text

#### Scenario: Concise summary display
- **GIVEN** an analysis is generated
- **WHEN** displaying the summary
- **THEN** the system SHALL show:
  - Key metrics in visual cards
  - Signal confirmation status (3/4) prominently
  - Trade recommendation (BUY/SELL/HOLD) clearly
  - Entry/Stop/Target prices visually
  - Chart as main content
- **AND** SHALL minimize text paragraphs
- **AND** SHALL maximize visual indicators

### Requirement: English Report Implementation
The system SHALL generate complete English analysis reports with proper financial terminology.

#### Scenario: Complete English report structure
- **GIVEN** English analysis is requested
- **WHEN** generating the report
- **THEN** the system SHALL include all sections in English:
  1. Core Price Analysis
  2. Trend Indicator Analysis (SuperTrend, Moving Averages)
  3. Confirmation Indicator Analysis (MACD, RSI, ATR, Bollinger Bands, Volume, OBV)
  4. 3/4 Signal Confirmation System
  5. Trade Recommendation
  6. Risk Assessment
- **AND** SHALL use professional English terminology throughout

### Requirement: Visual-First User Experience
The system SHALL prioritize visual analysis over text-based analysis.

#### Scenario: Analysis page layout
- **GIVEN** the analysis page
- **WHEN** displaying analysis results
- **THEN** the system SHALL use this layout order:
  1. Visual Summary Cards (price, trend, signals)
  2. Interactive Chart (7-panel, full-width, expanded)
  3. Trade Recommendation Cards (visual)
  4. Concise Text Summary (collapsed)
  5. Full Report (hidden by default)
- **AND** SHALL use visual indicators (colors, icons, badges)
- **AND** SHALL minimize reading required

