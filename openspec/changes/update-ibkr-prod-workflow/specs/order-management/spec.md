## ADDED Requirements
### Requirement: Limit Price Normalization
The order placement pipeline SHALL normalize limit prices before submitting orders to IBKR so that actionable signals never fail due to missing or invalid pricing.

#### Scenario: Derive limit price from signal or market data
- **WHEN** `place_order` constructs a limit order for `ibkr_trading_signal_workflow`
- **THEN** it SHALL prefer the LLM-provided `suggested_entry_price` when it is a positive decimal
- **AND** if the signal omits that value, it SHALL fall back to the latest close price from the previously fetched market data snapshot
- **AND** it SHALL persist the normalized price in XCom/artifacts for downstream auditing

#### Scenario: Reject invalid limit prices before IBKR
- **WHEN** neither the signal nor the market data snapshot can produce a positive limit price
- **THEN** the workflow SHALL mark the signal as non-actionable, skip IBKR order submission, and log the reason
- **AND** it SHALL surface the failure via task logs/artifacts so operators can debug without checking IBKR rejections
