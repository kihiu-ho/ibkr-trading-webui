## MODIFIED Requirements
### Requirement: DAG Discovery and Display
The system SHALL discover and display all IBKR workflows in the Airflow monitor page.

#### Scenario: All IBKR workflows visible
- **WHEN** user navigates to Airflow monitor page
- **THEN** all IBKR workflows are discovered and displayed
- **AND** workflows include: ibkr_stock_data_workflow, ibkr_multi_symbol_workflow, ibkr_trading_signal_workflow
- **AND** workflows show correct status (active/paused)
- **AND** workflows can be triggered and viewed

#### Scenario: DAG discovery errors
- **WHEN** DAG has syntax or import errors
- **THEN** errors are logged clearly
- **AND** frontend shows error message if DAGs cannot be loaded
- **AND** user can see which DAGs failed to load

## ADDED Requirements
### Requirement: DAG Discovery Debugging
The system SHALL provide debugging information for DAG discovery issues.

#### Scenario: DAG discovery debugging
- **WHEN** DAGs are not appearing in the monitor
- **THEN** provide clear error messages
- **AND** log DAG parsing errors
- **AND** show which DAGs failed to load and why

