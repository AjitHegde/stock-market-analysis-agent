# Requirements Document: Performance Tracker

## Introduction

The Performance Tracker feature provides comprehensive trading performance analysis for the Stock Market AI Agent. It tracks individual trades from entry to exit, analyzes accuracy by analysis module (sentiment, technical, fundamental), and automatically adjusts recommendation weights based on historical performance. This enables the agent to learn from past trades and continuously improve its recommendation accuracy.

## Glossary

- **Trade**: A complete buy or sell transaction with entry and exit points
- **Trade_Record**: Data structure storing all information about a single trade
- **Module**: An analysis component (sentiment, technical, or fundamental analyzer)
- **Module_Performance**: Performance metrics for a specific analysis module
- **Accuracy_Score**: Composite metric (0.0 to 1.0) measuring module effectiveness
- **Recommended_Weight**: Suggested weight for a module based on historical accuracy
- **Performance_Report**: Monthly summary of trading performance and module analysis
- **Signal_Source**: The primary module that triggered a trade recommendation
- **Win_Rate**: Percentage of trades that resulted in profit
- **Profit_Loss_Percent**: Percentage gain or loss on a trade
- **Holding_Period**: Number of days a position was held
- **Performance_Tracker**: System component that manages trade tracking and analysis

## Requirements

### Requirement 1: Trade Entry Recording

**User Story:** As a trader, I want to record trade entries with complete analysis context, so that I can track which signals led to each trade.

#### Acceptance Criteria

1. WHEN a trade is entered, THE Performance_Tracker SHALL record the symbol, action, entry price, quantity, and entry date
2. WHEN a trade is entered, THE Performance_Tracker SHALL record all analysis scores (sentiment, technical, fundamental) at entry time
3. WHEN a trade is entered, THE Performance_Tracker SHALL record the confidence level and market state at entry
4. WHEN a trade is entered, THE Performance_Tracker SHALL record the signal source that triggered the trade
5. WHEN a trade is entered, THE Performance_Tracker SHALL generate a unique trade ID
6. WHEN a trade is entered, THE Performance_Tracker SHALL persist the trade record to storage immediately

### Requirement 2: Trade Exit Recording

**User Story:** As a trader, I want to record trade exits and automatically calculate profit/loss, so that I can track trading outcomes.

#### Acceptance Criteria

1. WHEN a trade is exited, THE Performance_Tracker SHALL record the exit price and exit date
2. WHEN a trade is exited, THE Performance_Tracker SHALL calculate profit/loss amount based on entry/exit prices and quantity
3. WHEN a trade is exited, THE Performance_Tracker SHALL calculate profit/loss percentage
4. WHEN a trade is exited, THE Performance_Tracker SHALL calculate holding period in days
5. WHEN a trade is exited, THE Performance_Tracker SHALL update the trade record with exit information
6. WHEN a trade is exited, THE Performance_Tracker SHALL persist the updated trade record to storage immediately
7. IF a trade ID does not exist, THEN THE Performance_Tracker SHALL return an error
8. IF a trade is already closed, THEN THE Performance_Tracker SHALL prevent duplicate exit recording

### Requirement 3: Trade Query Operations

**User Story:** As a trader, I want to query my trades by various criteria, so that I can review specific trading activity.

#### Acceptance Criteria

1. THE Performance_Tracker SHALL provide a method to retrieve all open trades
2. THE Performance_Tracker SHALL provide a method to retrieve closed trades within a date range
3. THE Performance_Tracker SHALL provide a method to retrieve a trade by its unique ID
4. THE Performance_Tracker SHALL provide a method to retrieve all trades for a specific symbol
5. WHEN querying trades, THE Performance_Tracker SHALL return trade records with all stored information

### Requirement 4: Module Performance Analysis

**User Story:** As a system administrator, I want to analyze performance by analysis module, so that I can identify which modules are most accurate.

#### Acceptance Criteria

1. WHEN analyzing module performance, THE Performance_Tracker SHALL identify trades where the module had strong signal influence
2. WHEN analyzing module performance, THE Performance_Tracker SHALL calculate total trades, winning trades, and losing trades for the module
3. WHEN analyzing module performance, THE Performance_Tracker SHALL calculate win rate as percentage of winning trades
4. WHEN analyzing module performance, THE Performance_Tracker SHALL calculate average profit/loss percentage
5. WHEN analyzing module performance, THE Performance_Tracker SHALL calculate total profit/loss percentage
6. WHEN analyzing module performance, THE Performance_Tracker SHALL calculate average holding period
7. WHEN analyzing module performance, THE Performance_Tracker SHALL calculate an accuracy score based on win rate, average P/L, and consistency
8. THE Performance_Tracker SHALL analyze performance for sentiment, technical, and fundamental modules

### Requirement 5: Recommended Weight Calculation

**User Story:** As a system administrator, I want the system to calculate optimal module weights based on performance, so that recommendations can be automatically improved.

#### Acceptance Criteria

1. WHEN calculating recommended weights, THE Performance_Tracker SHALL use accuracy scores from module performance analysis
2. WHEN calculating recommended weights, THE Performance_Tracker SHALL distribute weights proportional to accuracy scores
3. WHEN calculating recommended weights, THE Performance_Tracker SHALL ensure all weights sum to 1.0
4. WHEN calculating recommended weights, THE Performance_Tracker SHALL enforce minimum weight of 0.15 per module
5. WHEN calculating recommended weights, THE Performance_Tracker SHALL enforce maximum weight of 0.50 per module
6. IF all accuracy scores are zero, THEN THE Performance_Tracker SHALL assign equal weights to all modules

### Requirement 6: Monthly Performance Reporting

**User Story:** As a trader, I want to generate monthly performance reports, so that I can review my trading results and module effectiveness.

#### Acceptance Criteria

1. WHEN generating a monthly report, THE Performance_Tracker SHALL calculate overall metrics for the period
2. WHEN generating a monthly report, THE Performance_Tracker SHALL include total trades, open trades, and closed trades counts
3. WHEN generating a monthly report, THE Performance_Tracker SHALL include winning trades, losing trades, and win rate
4. WHEN generating a monthly report, THE Performance_Tracker SHALL include total profit/loss and average profit/loss
5. WHEN generating a monthly report, THE Performance_Tracker SHALL identify the best performing trade
6. WHEN generating a monthly report, THE Performance_Tracker SHALL identify the worst performing trade
7. WHEN generating a monthly report, THE Performance_Tracker SHALL include module performance analysis for all modules
8. WHEN generating a monthly report, THE Performance_Tracker SHALL include recommended weights for the next period
9. WHEN generating a monthly report, THE Performance_Tracker SHALL persist the report to storage
10. THE Performance_Tracker SHALL support generating reports for any specified month and year

### Requirement 7: Data Persistence

**User Story:** As a system administrator, I want trade data and reports to be persisted to disk, so that performance history is preserved across sessions.

#### Acceptance Criteria

1. THE Performance_Tracker SHALL store trade records in JSON format
2. THE Performance_Tracker SHALL store performance reports in JSON format
3. WHEN initializing, THE Performance_Tracker SHALL load existing trade records from storage
4. WHEN initializing, THE Performance_Tracker SHALL load existing reports from storage
5. WHEN trade data changes, THE Performance_Tracker SHALL save to storage immediately
6. WHEN a report is generated, THE Performance_Tracker SHALL save to storage immediately
7. THE Performance_Tracker SHALL create the storage directory if it does not exist
8. IF storage file does not exist, THEN THE Performance_Tracker SHALL start with empty data

### Requirement 8: Configuration Integration

**User Story:** As a system administrator, I want to configure performance tracking behavior, so that I can control how the system operates.

#### Acceptance Criteria

1. THE Configuration SHALL include a performance_tracking_enabled flag
2. THE Configuration SHALL include a performance_storage_path setting
3. THE Configuration SHALL include an auto_adjust_weights flag
4. THE Configuration SHALL include a min_trades_for_adjustment setting
5. THE Configuration SHALL provide a method to apply recommended weights to module weights
6. WHEN applying recommended weights, THE Configuration SHALL update sentiment_weight, technical_weight, and fundamental_weight
7. WHEN applying recommended weights, THE Configuration SHALL normalize weights to sum to 1.0

### Requirement 9: Agent Core Integration

**User Story:** As a system administrator, I want the agent to automatically initialize performance tracking and adjust weights, so that the system learns from experience.

#### Acceptance Criteria

1. WHEN AgentCore initializes, IF performance tracking is enabled, THEN THE AgentCore SHALL create a PerformanceTracker instance
2. WHEN AgentCore initializes, IF auto_adjust_weights is enabled, THEN THE AgentCore SHALL check for sufficient trade data
3. WHEN AgentCore initializes, IF sufficient trades exist, THEN THE AgentCore SHALL apply recommended weights from latest report
4. WHEN AgentCore initializes, IF weights are adjusted, THEN THE AgentCore SHALL recreate the RecommendationEngine with new weights
5. THE AgentCore SHALL require at least min_trades_for_adjustment closed trades before adjusting weights

### Requirement 10: CLI Trade Management

**User Story:** As a trader, I want CLI commands to manage trades, so that I can record exits and view open positions.

#### Acceptance Criteria

1. THE CLI SHALL provide a close-trade command that accepts trade ID and exit price
2. WHEN close-trade is executed, THE CLI SHALL record the trade exit using PerformanceTracker
3. WHEN close-trade is executed, THE CLI SHALL display trade summary with profit/loss
4. THE CLI SHALL provide an open-trades command to list all open positions
5. WHEN open-trades is executed, THE CLI SHALL display trade ID, symbol, action, entry price, quantity, entry date, and days held
6. THE CLI SHALL support optional notes when closing trades

### Requirement 11: CLI Performance Reporting

**User Story:** As a trader, I want a CLI command to generate performance reports, so that I can review my trading results.

#### Acceptance Criteria

1. THE CLI SHALL provide a performance command to generate monthly reports
2. THE CLI SHALL support optional month and year parameters for the performance command
3. WHEN performance is executed, THE CLI SHALL generate a report using PerformanceTracker
4. WHEN performance is executed, THE CLI SHALL display overall performance metrics
5. WHEN performance is executed, THE CLI SHALL display best and worst trades
6. WHEN performance is executed, THE CLI SHALL display module performance analysis
7. WHEN performance is executed, THE CLI SHALL display recommended weights for next period
8. IF performance tracking is not enabled, THEN THE CLI SHALL display a warning message
