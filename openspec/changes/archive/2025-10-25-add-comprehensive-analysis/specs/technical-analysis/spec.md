# Technical Analysis - Spec

## ADDED Requirements

### Requirement: Comprehensive Indicator Synthesis
The system SHALL synthesize data from all available technical indicators to produce a unified analysis.

#### Scenario: Multiple indicators analyzed together
- **GIVEN** market data with calculated indicators (SuperTrend, MACD, RSI, ATR, Bollinger Bands, Moving Averages, OBV)
- **WHEN** comprehensive analysis is requested for a symbol
- **THEN** the system SHALL analyze all indicators together
- **AND** SHALL identify trends, momentum, volatility, and volume patterns
- **AND** SHALL detect indicator agreements and contradictions

#### Scenario: Daily and weekly timeframe confirmation
- **GIVEN** a symbol with sufficient historical data
- **WHEN** analysis is requested
- **THEN** the system SHALL analyze both daily and weekly timeframes
- **AND** SHALL confirm daily signals against weekly trends
- **AND** SHALL flag any timeframe divergences

### Requirement: 3/4 Signal Confirmation System
The system SHALL implement a 3/4 rule requiring at least 3 out of 4 key signals to agree before confirming a trade direction.

#### Scenario: Bullish signal confirmation
- **GIVEN** the following four signals: SuperTrend direction, price vs 20 SMA, MACD crossover, RSI position
- **WHEN** at least 3 signals indicate bullish (e.g., SuperTrend up, price > 20 SMA, MACD buy, RSI > 50)
- **THEN** the system SHALL confirm a bullish trade signal
- **AND** SHALL provide confidence level based on number of confirming signals

#### Scenario: Bearish signal confirmation
- **GIVEN** the same four signals
- **WHEN** at least 3 signals indicate bearish
- **THEN** the system SHALL confirm a bearish trade signal
- **AND** SHALL provide confidence level

#### Scenario: Insufficient signal confirmation
- **GIVEN** the four signals
- **WHEN** fewer than 3 signals agree on direction
- **THEN** the system SHALL NOT confirm a trade signal
- **AND** SHALL recommend "HOLD" or "NEUTRAL" stance
- **AND** SHALL explain which signals are conflicting

### Requirement: Trade Recommendation Calculator
The system SHALL calculate precise entry zones, stop-loss levels, and take-profit targets based on technical analysis.

#### Scenario: Calculate bullish trade parameters
- **GIVEN** a confirmed bullish signal and current price
- **WHEN** trade parameters are calculated
- **THEN** the system SHALL recommend entry price range
- **AND** SHALL calculate stop-loss as entry - (2 × ATR)
- **AND** SHALL calculate conservative and aggressive profit targets
- **AND** SHALL provide technical justification for each target

#### Scenario: Calculate bearish trade parameters
- **GIVEN** a confirmed bearish signal and current price
- **WHEN** trade parameters are calculated
- **THEN** the system SHALL recommend entry price range
- **AND** SHALL calculate stop-loss as entry + (2 × ATR)
- **AND** SHALL calculate conservative and aggressive profit targets
- **AND** SHALL provide technical justification for each target

### Requirement: Risk-Reward Ratio Calculation
The system SHALL calculate R-multiples for each trade recommendation to assess risk-reward potential.

#### Scenario: Calculate R-multiple for long position
- **GIVEN** entry price, stop-loss, and target price for a long position
- **WHEN** R-multiple is calculated
- **THEN** the system SHALL compute (Target - Entry) ÷ (Entry - StopLoss)
- **AND** SHALL display the result as "XR" format (e.g., "2.5R")
- **AND** SHALL warn if R-multiple is less than 1.5

#### Scenario: Calculate R-multiple for short position
- **GIVEN** entry price, stop-loss, and target price for a short position
- **WHEN** R-multiple is calculated
- **THEN** the system SHALL compute (Entry - Target) ÷ (StopLoss - Entry)
- **AND** SHALL display the result as "XR" format

### Requirement: Target Price Justification
The system SHALL provide technical justification for each target price using recognized technical analysis methods.

#### Scenario: Target based on support/resistance
- **GIVEN** historical price data showing support/resistance levels
- **WHEN** target price is calculated
- **THEN** the system MAY use previous highs/lows as targets
- **AND** SHALL explain "Target at $X based on previous resistance at [date]"

#### Scenario: Target based on Fibonacci levels
- **GIVEN** a significant price move
- **WHEN** target price is calculated
- **THEN** the system MAY use Fibonacci extensions (127.2%, 161.8%) or retracements (38.2%, 50%, 61.8%)
- **AND** SHALL explain "Target at $X based on 161.8% Fibonacci extension"

#### Scenario: Target based on chart patterns
- **GIVEN** identifiable chart patterns (head & shoulders, triangles, flags)
- **WHEN** target price is calculated
- **THEN** the system MAY use pattern measurement targets
- **AND** SHALL explain "Target at $X based on [pattern] height projection"

#### Scenario: Target based on Bollinger Bands
- **GIVEN** Bollinger Bands calculated
- **WHEN** target price is calculated
- **THEN** the system MAY use upper/lower band as targets
- **AND** SHALL explain "Target at $X based on Bollinger Band upper limit"

#### Scenario: Target based on ATR projection
- **GIVEN** ATR calculated
- **WHEN** target price is calculated
- **THEN** the system MAY use 2-3× ATR from entry as target
- **AND** SHALL explain "Target at $X based on 3× ATR volatility projection"

### Requirement: Chinese Analysis Report Generation
The system SHALL generate comprehensive analysis reports in Chinese following a standardized template.

#### Scenario: Generate Chinese daily analysis
- **GIVEN** a symbol with analyzed indicators
- **WHEN** analysis report is requested in Chinese
- **THEN** the system SHALL generate a report in Chinese
- **AND** SHALL include sections: 核心價格分析, 趨勢指標分析, 確認指標分析, 信號確認系統, 交易建議, 風險評估
- **AND** SHALL use proper financial terminology in Chinese
- **AND** SHALL format the report as structured markdown

#### Scenario: Include all indicator analysis sections
- **GIVEN** a complete analysis
- **WHEN** report is generated
- **THEN** the system SHALL include SuperTrend status (上升趨勢/下降趨勢, 綠色/紅色信號)
- **AND** SHALL include Moving Average analysis (20/50/200 SMA positions, golden/death crosses)
- **AND** SHALL include MACD, RSI levels with Chinese status (超買/超賣/中性)
- **AND** SHALL include ATR, Bollinger Bands, Volume, OBV analysis
- **AND** SHALL provide 綜合趨勢判斷 (強烈看漲/看漲/中性/看跌/強烈看跌)

### Requirement: Analysis History Tracking
The system SHALL store generated analyses in the database for future reference and performance tracking.

#### Scenario: Save analysis to database
- **GIVEN** a generated analysis
- **WHEN** analysis is created
- **THEN** the system SHALL store the analysis in the database
- **AND** SHALL include timestamp, symbol, timeframe, all indicator values, recommendations, and calculated targets

#### Scenario: Retrieve analysis history
- **GIVEN** past analyses stored in database
- **WHEN** user requests analysis history for a symbol
- **THEN** the system SHALL return all past analyses ordered by date
- **AND** SHALL allow filtering by symbol and timeframe
- **AND** SHALL include performance tracking (if trade was executed, actual vs predicted outcomes)

### Requirement: Frontend Analysis Display
The system SHALL provide a user-friendly web interface for requesting and viewing comprehensive analyses.

#### Scenario: Request analysis from UI
- **GIVEN** a user on the analysis page
- **WHEN** user selects a symbol and clicks "Generate Analysis"
- **THEN** the system SHALL fetch current market data
- **AND** SHALL calculate all indicators
- **AND** SHALL generate comprehensive analysis
- **AND** SHALL display the Chinese analysis report

#### Scenario: Display trade recommendations visually
- **GIVEN** an analysis with trade recommendations
- **WHEN** analysis is displayed
- **THEN** the system SHALL highlight entry zones in green/red based on direction
- **AND** SHALL show stop-loss level with clear visual indicator
- **AND** SHALL show target prices with technical justification
- **AND** SHALL display R-multiple prominently
- **AND** SHALL show signal confirmation status (e.g., "3/4 signals confirmed")

#### Scenario: Show historical analysis comparison
- **GIVEN** multiple analyses for the same symbol
- **WHEN** user views analysis history
- **THEN** the system SHALL display past analyses in chronological order
- **AND** SHALL allow comparison of recommendations over time
- **AND** SHALL show if previous trade recommendations were profitable

