# Implementation Plan: Performance Tracker

## Overview

This implementation plan documents the completed implementation of the Performance Tracker feature. All tasks listed below have been implemented and are marked as complete. This document serves as a retrospective record of the implementation approach.

## Tasks

- [x] 1. Create data models for performance tracking
  - [x] 1.1 Define TradeRecord dataclass with all required fields
    - Implemented in `src/performance_tracker.py`
    - Includes trade lifecycle fields, analysis scores, and P/L calculations
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_
  
  - [x] 1.2 Define ModulePerformance dataclass for module metrics
    - Implemented in `src/performance_tracker.py`
    - Includes win rate, P/L metrics, accuracy score, and recommended weight
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 1.3 Define PerformanceReport dataclass for monthly reports
    - Implemented in `src/performance_tracker.py`
    - Includes overall metrics, best/worst trades, module performance, and recommended weights
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] 2. Implement PerformanceTracker class core functionality
  - [x] 2.1 Implement __init__ with storage path and data loading
    - Implemented in `src/performance_tracker.py`
    - Creates storage directory if needed, loads existing data
    - _Requirements: 7.3, 7.4, 7.7, 7.8_
  
  - [x] 2.2 Implement _load_data() for JSON deserialization
    - Implemented in `src/performance_tracker.py`
    - Handles missing files gracefully, deserializes trades and reports
    - _Requirements: 7.3, 7.4_
  
  - [x] 2.3 Implement _save_data() for JSON serialization
    - Implemented in `src/performance_tracker.py`
    - Serializes trades and reports, includes last_updated timestamp
    - _Requirements: 7.1, 7.2, 7.5, 7.6_

- [x] 3. Implement trade entry recording
  - [x] 3.1 Implement record_entry() method
    - Implemented in `src/performance_tracker.py`
    - Generates unique trade ID, creates TradeRecord, persists to storage
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 3.2 Implement trade ID generation logic
    - Implemented in `src/performance_tracker.py`
    - Format: {symbol}_{timestamp} for uniqueness and readability
    - _Requirements: 1.5_

- [x] 4. Implement trade exit recording
  - [x] 4.1 Implement record_exit() method
    - Implemented in `src/performance_tracker.py`
    - Calculates P/L, holding period, updates trade record, persists to storage
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 4.2 Implement P/L calculation for BUY and SELL actions
    - Implemented in `src/performance_tracker.py`
    - Handles both BUY (long) and SELL (short) positions correctly
    - _Requirements: 2.2, 2.3_
  
  - [x] 4.3 Implement holding period calculation
    - Implemented in `src/performance_tracker.py`
    - Calculates days between entry and exit dates
    - _Requirements: 2.4_
  
  - [x] 4.4 Implement error handling for invalid trade IDs
    - Implemented in `src/performance_tracker.py`
    - Returns None and logs error if trade not found
    - _Requirements: 2.7_
  
  - [x] 4.5 Implement duplicate exit prevention
    - Implemented in `src/performance_tracker.py`
    - Checks if trade already closed, logs warning if so
    - _Requirements: 2.8_

- [x] 5. Implement trade query operations
  - [x] 5.1 Implement get_open_trades() method
    - Implemented in `src/performance_tracker.py`
    - Filters trades where exit_price is None
    - _Requirements: 3.1_
  
  - [x] 5.2 Implement get_closed_trades() with date range filtering
    - Implemented in `src/performance_tracker.py`
    - Supports optional start_date and end_date parameters
    - _Requirements: 3.2_
  
  - [x] 5.3 Implement get_trade_by_id() method
    - Implemented in `src/performance_tracker.py`
    - Returns trade matching the given ID
    - _Requirements: 3.3_
  
  - [x] 5.4 Implement get_trades_by_symbol() method
    - Implemented in `src/performance_tracker.py`
    - Returns all trades for a specific symbol
    - _Requirements: 3.4_

- [x] 6. Implement module performance analysis
  - [x] 6.1 Implement analyze_module_performance() method
    - Implemented in `src/performance_tracker.py`
    - Filters trades by module influence, calculates all metrics
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 6.2 Implement module signal strength detection logic
    - Implemented in `src/performance_tracker.py`
    - Considers trades where module score > 0.3 or module is signal source
    - _Requirements: 4.1_
  
  - [x] 6.3 Implement accuracy score calculation
    - Implemented in `src/performance_tracker.py`
    - Composite score: win_rate (40%) + avg_pl (40%) + consistency (20%)
    - _Requirements: 4.7_

- [x] 7. Implement recommended weight calculation
  - [x] 7.1 Implement calculate_recommended_weights() method
    - Implemented in `src/performance_tracker.py`
    - Distributes weights proportional to accuracy scores
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 7.2 Implement weight constraint enforcement
    - Implemented in `src/performance_tracker.py`
    - Enforces min (0.15) and max (0.50) constraints
    - _Requirements: 5.4, 5.5_
  
  - [x] 7.3 Implement weight normalization
    - Implemented in `src/performance_tracker.py`
    - Ensures weights sum to 1.0 after constraints
    - _Requirements: 5.3_
  
  - [x] 7.4 Implement equal weights fallback for zero scores
    - Implemented in `src/performance_tracker.py`
    - Assigns 0.33 to each module if all scores are zero
    - _Requirements: 5.6_

- [x] 8. Implement monthly performance reporting
  - [x] 8.1 Implement generate_monthly_report() method
    - Implemented in `src/performance_tracker.py`
    - Generates comprehensive monthly report with all metrics
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_
  
  - [x] 8.2 Implement period boundary calculation
    - Implemented in `src/performance_tracker.py`
    - Calculates start/end dates for specified month/year
    - _Requirements: 6.10_
  
  - [x] 8.3 Implement overall metrics calculation
    - Implemented in `src/performance_tracker.py`
    - Calculates win rate, total/avg P/L, trade counts
    - _Requirements: 6.2, 6.3, 6.4_
  
  - [x] 8.4 Implement best/worst trade identification
    - Implemented in `src/performance_tracker.py`
    - Finds trades with max/min profit_loss_percent
    - _Requirements: 6.5, 6.6_
  
  - [x] 8.5 Implement module performance analysis integration
    - Implemented in `src/performance_tracker.py`
    - Analyzes all three modules and includes in report
    - _Requirements: 6.7_
  
  - [x] 8.6 Implement recommended weights integration
    - Implemented in `src/performance_tracker.py`
    - Calculates and includes recommended weights in report
    - _Requirements: 6.8_
  
  - [x] 8.7 Implement report persistence
    - Implemented in `src/performance_tracker.py`
    - Saves report to storage after generation
    - _Requirements: 6.9_
  
  - [x] 8.8 Implement get_latest_recommended_weights() method
    - Implemented in `src/performance_tracker.py`
    - Returns weights from most recent report
    - _Requirements: 5.1_

- [x] 9. Implement configuration integration
  - [x] 9.1 Add performance tracking fields to Configuration dataclass
    - Implemented in `src/config.py`
    - Added performance_tracking_enabled, performance_storage_path, auto_adjust_weights, min_trades_for_adjustment
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 9.2 Implement apply_recommended_weights() method
    - Implemented in `src/config.py`
    - Updates sentiment_weight, technical_weight, fundamental_weight
    - _Requirements: 8.5, 8.6_
  
  - [x] 9.3 Ensure weight normalization in apply_recommended_weights()
    - Implemented in `src/config.py`
    - Calls normalize_weights() after applying weights
    - _Requirements: 8.7_

- [x] 10. Implement AgentCore integration
  - [x] 10.1 Add PerformanceTracker initialization to AgentCore.__init__
    - Implemented in `src/agent_core.py`
    - Creates tracker if performance_tracking_enabled is True
    - _Requirements: 9.1_
  
  - [x] 10.2 Implement _auto_adjust_weights() method
    - Implemented in `src/agent_core.py`
    - Checks trade count threshold, applies weights if sufficient data
    - _Requirements: 9.2, 9.3, 9.5_
  
  - [x] 10.3 Call _auto_adjust_weights() during initialization
    - Implemented in `src/agent_core.py`
    - Calls method if auto_adjust_weights is enabled
    - _Requirements: 9.2_
  
  - [x] 10.4 Implement RecommendationEngine recreation after weight adjustment
    - Implemented in `src/agent_core.py`
    - Recreates engine with updated configuration
    - _Requirements: 9.4_

- [x] 11. Implement CLI close-trade command
  - [x] 11.1 Create close_trade() CLI command function
    - Implemented in `src/cli.py`
    - Accepts trade_id, exit_price, optional config and notes
    - _Requirements: 10.1_
  
  - [x] 11.2 Implement trade exit recording via PerformanceTracker
    - Implemented in `src/cli.py`
    - Calls tracker.record_exit() with provided parameters
    - _Requirements: 10.2_
  
  - [x] 11.3 Implement trade summary display
    - Implemented in `src/cli.py`
    - Displays symbol, action, prices, quantity, P/L, holding period
    - _Requirements: 10.3_
  
  - [x] 11.4 Implement error handling for invalid trade IDs
    - Implemented in `src/cli.py`
    - Displays error message if trade not found
    - _Requirements: 10.2_
  
  - [x] 11.5 Implement notes parameter support
    - Implemented in `src/cli.py`
    - Passes notes to record_exit() method
    - _Requirements: 10.6_

- [x] 12. Implement CLI open-trades command
  - [x] 12.1 Create open_trades() CLI command function
    - Implemented in `src/cli.py`
    - Accepts optional config parameter
    - _Requirements: 10.4_
  
  - [x] 12.2 Implement open trades retrieval and display
    - Implemented in `src/cli.py`
    - Calls tracker.get_open_trades() and displays in table format
    - _Requirements: 10.4, 10.5_
  
  - [x] 12.3 Implement days held calculation for display
    - Implemented in `src/cli.py`
    - Calculates days between entry_date and current date
    - _Requirements: 10.5_

- [x] 13. Implement CLI performance command
  - [x] 13.1 Create performance() CLI command function
    - Implemented in `src/cli.py`
    - Accepts optional config, month, and year parameters
    - _Requirements: 11.1, 11.2_
  
  - [x] 13.2 Implement report generation via PerformanceTracker
    - Implemented in `src/cli.py`
    - Calls tracker.generate_monthly_report() with parameters
    - _Requirements: 11.3_
  
  - [x] 13.3 Implement overall performance metrics display
    - Implemented in `src/cli.py`
    - Displays total trades, win rate, P/L metrics
    - _Requirements: 11.4_
  
  - [x] 13.4 Implement best/worst trade display
    - Implemented in `src/cli.py`
    - Displays best and worst trades with details
    - _Requirements: 11.5_
  
  - [x] 13.5 Implement module performance analysis display
    - Implemented in `src/cli.py`
    - Displays table with all module metrics
    - _Requirements: 11.6_
  
  - [x] 13.6 Implement recommended weights display
    - Implemented in `src/cli.py`
    - Displays recommended weights for next period
    - _Requirements: 11.7_
  
  - [x] 13.7 Implement warning for disabled performance tracking
    - Implemented in `src/cli.py`
    - Displays warning if performance_tracking_enabled is False
    - _Requirements: 11.8_

- [x] 14. Testing and validation
  - [x] 14.1 Create unit tests for TradeRecord data model
    - Test serialization/deserialization
    - Test field validation
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [x] 14.2 Create unit tests for ModulePerformance data model
    - Test metric calculations
    - Test accuracy score formula
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  
  - [x] 14.3 Create unit tests for PerformanceReport data model
    - Test report structure
    - Test serialization/deserialization
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  
  - [x] 14.4 Create unit tests for trade entry recording
    - Test record_entry() with various parameters
    - Test trade ID generation
    - Test persistence
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 14.5 Create unit tests for trade exit recording
    - Test record_exit() with various scenarios
    - Test P/L calculations
    - Test error handling
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  
  - [x] 14.6 Create unit tests for trade query operations
    - Test get_open_trades()
    - Test get_closed_trades() with date ranges
    - Test get_trade_by_id()
    - Test get_trades_by_symbol()
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 14.7 Create unit tests for module performance analysis
    - Test analyze_module_performance() with various trade sets
    - Test signal strength detection
    - Test accuracy score calculation
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_
  
  - [x] 14.8 Create unit tests for recommended weight calculation
    - Test calculate_recommended_weights() with various scores
    - Test constraint enforcement
    - Test normalization
    - Test edge cases (zero scores)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 14.9 Create unit tests for monthly reporting
    - Test generate_monthly_report() with various periods
    - Test metric calculations
    - Test best/worst trade identification
    - Test report persistence
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_
  
  - [x] 14.10 Create unit tests for storage operations
    - Test _load_data() with various scenarios
    - Test _save_data() with various data
    - Test error handling
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_
  
  - [x] 14.11 Create unit tests for configuration integration
    - Test apply_recommended_weights()
    - Test weight normalization
    - _Requirements: 8.5, 8.6, 8.7_
  
  - [x] 14.12 Create unit tests for AgentCore integration
    - Test PerformanceTracker initialization
    - Test _auto_adjust_weights()
    - Test weight adjustment threshold
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 14.13 Create integration tests for end-to-end workflows
    - Test complete trade lifecycle (entry → exit → reporting)
    - Test weight adjustment workflow
    - Test CLI commands with actual tracker
    - _Requirements: All_
  
  - [x] 14.14 Create property-based tests for core algorithms
    - Test P/L calculation with random prices
    - Test weight calculation with random scores
    - Test JSON round-trip with random data
    - Test filter operations with random trade sets
    - _Requirements: 2.2, 2.3, 5.3, 5.4, 5.5, 7.1, 7.2, 3.1, 3.2_

## Notes

- All tasks are marked as complete ([x]) since this is a retrospective spec
- The implementation uses JSON for storage (simple, human-readable, no external dependencies)
- The accuracy score formula balances win rate, average P/L, and consistency
- Weight constraints (0.15 min, 0.50 max) prevent over-reliance on single modules
- The system gracefully handles missing data and storage errors
- CLI commands provide user-friendly interfaces for trade management and reporting
- Property-based testing ensures correctness across wide range of inputs
- Integration with AgentCore enables automatic learning from trading history
