# Design Document: Performance Tracker

## Overview

The Performance Tracker is a comprehensive trading performance analysis system that tracks individual trades, analyzes accuracy by analysis module, and automatically adjusts recommendation weights based on historical performance. The system enables the Stock Market AI Agent to learn from past trades and continuously improve recommendation accuracy through data-driven weight optimization.

### Key Features

- **Trade Lifecycle Management**: Record complete trade lifecycle from entry to exit with full analysis context
- **Module Performance Analysis**: Analyze accuracy of sentiment, technical, and fundamental analysis modules
- **Automatic Weight Adjustment**: Calculate and apply optimal module weights based on historical accuracy
- **Monthly Reporting**: Generate comprehensive performance reports with module analysis
- **Data Persistence**: Store trade history and reports in JSON format for long-term tracking
- **CLI Integration**: Provide command-line tools for trade management and reporting

### Design Goals

1. **Accuracy Tracking**: Measure which analysis modules produce the most accurate trading signals
2. **Continuous Improvement**: Automatically adjust module weights to improve recommendation quality
3. **Transparency**: Provide detailed performance metrics and reasoning for weight adjustments
4. **Simplicity**: Use straightforward JSON storage and clear data models
5. **Integration**: Seamlessly integrate with existing agent architecture

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        AgentCore                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Initialize PerformanceTracker (if enabled)          │  │
│  │  Auto-adjust weights on startup (if enabled)         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  PerformanceTracker                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • record_entry()                                    │  │
│  │  • record_exit()                                     │  │
│  │  • get_open_trades()                                 │  │
│  │  • get_closed_trades()                               │  │
│  │  • analyze_module_performance()                      │  │
│  │  • calculate_recommended_weights()                   │  │
│  │  • generate_monthly_report()                         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   JSON Storage                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  data/performance.json                               │  │
│  │  {                                                   │  │
│  │    "trades": [...],                                  │  │
│  │    "reports": [...],                                 │  │
│  │    "last_updated": "..."                             │  │
│  │  }                                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │
┌────────────────────────┴────────────────────────────────────┐
│                        CLI                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  • close-trade <trade_id> <exit_price>               │  │
│  │  • open-trades                                       │  │
│  │  • performance [--month M] [--year Y]                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Trade Entry**: When a recommendation is generated, analysis scores are recorded
2. **Trade Exit**: User closes trade via CLI, P/L is calculated and stored
3. **Monthly Analysis**: System analyzes closed trades, calculates module performance
4. **Weight Adjustment**: Recommended weights are calculated based on accuracy scores
5. **Auto-Application**: On next startup, weights are automatically applied (if enabled)

## Components and Interfaces

### TradeRecord Data Model

```python
@dataclass
class TradeRecord:
    """Represents a single trade record."""
    trade_id: str                          # Unique identifier
    symbol: str                            # Stock ticker
    action: str                            # "BUY" or "SELL"
    entry_price: float                     # Entry price
    entry_date: str                        # ISO format datetime
    exit_price: Optional[float]            # Exit price (None if open)
    exit_date: Optional[str]               # ISO format datetime (None if open)
    quantity: int                          # Number of shares
    profit_loss: Optional[float]           # P/L amount (None if open)
    profit_loss_percent: Optional[float]   # P/L percentage (None if open)
    holding_period_days: Optional[int]     # Days held (None if open)
    signal_source: str                     # "sentiment", "technical", "fundamental", "combined"
    sentiment_score: float                 # Sentiment score at entry
    technical_score: float                 # Technical score at entry
    fundamental_score: float               # Fundamental score at entry
    confidence: float                      # Recommendation confidence
    market_state: str                      # Market state at entry
    notes: str                             # Optional notes
```

### ModulePerformance Data Model

```python
@dataclass
class ModulePerformance:
    """Performance metrics for a specific analysis module."""
    module_name: str                       # "sentiment", "technical", "fundamental"
    total_trades: int                      # Total trades influenced by module
    winning_trades: int                    # Number of winning trades
    losing_trades: int                     # Number of losing trades
    win_rate: float                        # Percentage of winning trades
    avg_profit_loss: float                 # Average P/L percentage
    total_profit_loss: float               # Total P/L percentage
    avg_holding_period: float              # Average holding period in days
    accuracy_score: float                  # Composite accuracy score (0.0 to 1.0)
    recommended_weight: float              # Recommended weight for module
```

### PerformanceReport Data Model

```python
@dataclass
class PerformanceReport:
    """Monthly performance report."""
    report_date: str                       # Report generation date
    period_start: str                      # Period start date
    period_end: str                        # Period end date
    total_trades: int                      # Total trades in system
    open_trades: int                       # Number of open trades
    closed_trades: int                     # Number of closed trades in period
    winning_trades: int                    # Number of winning trades
    losing_trades: int                     # Number of losing trades
    win_rate: float                        # Overall win rate
    total_profit_loss: float               # Total P/L for period
    avg_profit_loss: float                 # Average P/L per trade
    best_trade: Optional[Dict]             # Best performing trade
    worst_trade: Optional[Dict]            # Worst performing trade
    module_performance: Dict[str, ModulePerformance]  # Performance by module
    recommended_weights: Dict[str, float]  # Recommended weights
```

### PerformanceTracker Class Interface

```python
class PerformanceTracker:
    """Tracks trading performance and adjusts recommendation weights."""
    
    def __init__(self, storage_path: str = "data/performance.json"):
        """Initialize tracker and load existing data."""
        
    def record_entry(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        quantity: int,
        sentiment_score: float,
        technical_score: float,
        fundamental_score: float,
        confidence: float,
        market_state: str = "neutral",
        signal_source: str = "combined",
        notes: str = ""
    ) -> str:
        """Record a trade entry. Returns trade ID."""
        
    def record_exit(
        self,
        trade_id: str,
        exit_price: float,
        notes: str = ""
    ) -> Optional[TradeRecord]:
        """Record a trade exit. Returns updated TradeRecord or None if not found."""
        
    def get_open_trades(self) -> List[TradeRecord]:
        """Get all open trades."""
        
    def get_closed_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TradeRecord]:
        """Get closed trades within a date range."""
        
    def analyze_module_performance(
        self,
        module_name: str,
        trades: List[TradeRecord]
    ) -> ModulePerformance:
        """Analyze performance for a specific module."""
        
    def calculate_recommended_weights(
        self,
        module_performances: Dict[str, ModulePerformance]
    ) -> Dict[str, float]:
        """Calculate recommended weights based on module performance."""
        
    def generate_monthly_report(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> PerformanceReport:
        """Generate a monthly performance report."""
        
    def get_latest_recommended_weights(self) -> Optional[Dict[str, float]]:
        """Get the latest recommended weights from the most recent report."""
        
    def get_trade_by_id(self, trade_id: str) -> Optional[TradeRecord]:
        """Get a trade by its ID."""
        
    def get_trades_by_symbol(self, symbol: str) -> List[TradeRecord]:
        """Get all trades for a specific symbol."""
```

### Configuration Integration

```python
@dataclass
class Configuration:
    """Configuration with performance tracking settings."""
    # ... existing fields ...
    performance_tracking_enabled: bool = True
    performance_storage_path: str = "data/performance.json"
    auto_adjust_weights: bool = False
    min_trades_for_adjustment: int = 20
    
    def apply_recommended_weights(self, recommended_weights: Dict[str, float]) -> None:
        """Apply recommended weights from performance tracking."""
        if 'sentiment' in recommended_weights:
            self.sentiment_weight = recommended_weights['sentiment']
        if 'technical' in recommended_weights:
            self.technical_weight = recommended_weights['technical']
        if 'fundamental' in recommended_weights:
            self.fundamental_weight = recommended_weights['fundamental']
        self.normalize_weights()
```

### AgentCore Integration

```python
class AgentCore:
    """Main orchestration layer with performance tracking."""
    
    def __init__(self, config: Configuration):
        """Initialize agent with performance tracking."""
        # ... existing initialization ...
        
        # Initialize performance tracker if enabled
        self.performance_tracker = None
        if config.performance_tracking_enabled:
            self.performance_tracker = PerformanceTracker(
                storage_path=config.performance_storage_path
            )
            
            # Auto-adjust weights if enabled
            if config.auto_adjust_weights:
                self._auto_adjust_weights()
    
    def _auto_adjust_weights(self):
        """Automatically adjust weights based on performance."""
        if not self.performance_tracker:
            return
        
        # Get closed trades
        closed_trades = self.performance_tracker.get_closed_trades()
        
        # Check if we have enough trades
        if len(closed_trades) < self.config.min_trades_for_adjustment:
            return
        
        # Get latest recommended weights
        recommended_weights = self.performance_tracker.get_latest_recommended_weights()
        
        if not recommended_weights:
            return
        
        # Apply recommended weights
        self.config.apply_recommended_weights(recommended_weights)
        
        # Update recommendation engine with new weights
        self.recommendation_engine = RecommendationEngine(self.config)
```

## Data Models

### Trade ID Generation

Trade IDs are generated using the format: `{symbol}_{timestamp}`

Example: `AAPL_20250125_143000`

This ensures uniqueness while providing human-readable information.

### Module Signal Strength Detection

A module is considered to have "strong signal influence" on a trade if:
- The module's score magnitude is > 0.3, OR
- The module was explicitly identified as the signal source

This allows the system to attribute trades to the modules that most influenced the decision.

### Accuracy Score Calculation

The accuracy score for a module is a composite metric (0.0 to 1.0) calculated as:

```
accuracy_score = (win_rate_score * 0.4) + (pl_score * 0.4) + (consistency_score * 0.2)

where:
  win_rate_score = win_rate / 100.0
  pl_score = (avg_profit_loss + 20) / 40  # Normalized to 0-1 assuming -20% to +20% range
  consistency_score = max(0.0, 1.0 - (std_dev / 50))  # Lower std dev is better
```

This formula balances:
- **Win Rate (40%)**: Percentage of profitable trades
- **Average P/L (40%)**: Magnitude of profits/losses
- **Consistency (20%)**: Stability of results (lower standard deviation is better)

### Recommended Weight Calculation

Recommended weights are calculated using the following algorithm:

1. **Proportional Distribution**: Weights are initially distributed proportional to accuracy scores
   ```
   initial_weight[module] = accuracy_score[module] / sum(all_accuracy_scores)
   ```

2. **Constraint Application**: Apply minimum (0.15) and maximum (0.50) constraints
   ```
   adjusted_weight[module] = max(0.15, min(0.50, initial_weight[module]))
   ```

3. **Normalization**: Normalize to ensure weights sum to 1.0
   ```
   final_weight[module] = adjusted_weight[module] / sum(all_adjusted_weights)
   ```

4. **Edge Case**: If all accuracy scores are zero, assign equal weights (0.33 each)

The constraints prevent over-reliance on a single module while ensuring all modules maintain minimum influence.

## Storage Format

### JSON Structure

```json
{
  "trades": [
    {
      "trade_id": "AAPL_20250125_143000",
      "symbol": "AAPL",
      "action": "BUY",
      "entry_price": 150.00,
      "entry_date": "2025-01-25T14:30:00",
      "exit_price": 155.00,
      "exit_date": "2025-01-30T10:15:00",
      "quantity": 10,
      "profit_loss": 50.00,
      "profit_loss_percent": 3.33,
      "holding_period_days": 5,
      "signal_source": "technical",
      "sentiment_score": 0.2,
      "technical_score": 0.6,
      "fundamental_score": 0.3,
      "confidence": 0.75,
      "market_state": "bullish",
      "notes": "Strong technical breakout"
    }
  ],
  "reports": [
    {
      "report_date": "2025-02-01T00:00:00",
      "period_start": "2025-01-01T00:00:00",
      "period_end": "2025-01-31T23:59:59",
      "total_trades": 25,
      "open_trades": 3,
      "closed_trades": 22,
      "winning_trades": 15,
      "losing_trades": 7,
      "win_rate": 68.18,
      "total_profit_loss": 45.50,
      "avg_profit_loss": 2.07,
      "best_trade": {
        "symbol": "TSLA",
        "profit_loss_percent": 12.50,
        "entry_date": "2025-01-15T09:30:00",
        "exit_date": "2025-01-20T15:00:00"
      },
      "worst_trade": {
        "symbol": "GOOGL",
        "profit_loss_percent": -5.20,
        "entry_date": "2025-01-10T10:00:00",
        "exit_date": "2025-01-12T14:30:00"
      },
      "module_performance": {
        "sentiment": {
          "module_name": "sentiment",
          "total_trades": 8,
          "winning_trades": 5,
          "losing_trades": 3,
          "win_rate": 62.50,
          "avg_profit_loss": 1.80,
          "total_profit_loss": 14.40,
          "avg_holding_period": 4.5,
          "accuracy_score": 0.65,
          "recommended_weight": 0.30
        },
        "technical": {
          "module_name": "technical",
          "total_trades": 12,
          "winning_trades": 9,
          "losing_trades": 3,
          "win_rate": 75.00,
          "avg_profit_loss": 2.50,
          "total_profit_loss": 30.00,
          "avg_holding_period": 5.2,
          "accuracy_score": 0.78,
          "recommended_weight": 0.45
        },
        "fundamental": {
          "module_name": "fundamental",
          "total_trades": 6,
          "winning_trades": 4,
          "losing_trades": 2,
          "win_rate": 66.67,
          "avg_profit_loss": 1.50,
          "total_profit_loss": 9.00,
          "avg_holding_period": 6.0,
          "accuracy_score": 0.60,
          "recommended_weight": 0.25
        }
      },
      "recommended_weights": {
        "sentiment": 0.30,
        "technical": 0.45,
        "fundamental": 0.25
      }
    }
  ],
  "last_updated": "2025-02-01T00:00:00"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Trade Entry Completeness
*For any* trade entry, all required fields (symbol, action, entry_price, quantity, entry_date, analysis scores, confidence, market_state, signal_source) should be populated in the stored TradeRecord.
**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Trade ID Uniqueness
*For any* set of trades created by the system, all trade IDs should be unique.
**Validates: Requirements 1.5**

### Property 3: Trade Entry Persistence
*For any* trade entry, after recording the entry and reloading from storage, the trade should exist with all original data intact.
**Validates: Requirements 1.6**

### Property 4: Profit/Loss Calculation Accuracy
*For any* closed trade, the profit_loss amount should equal (exit_price - entry_price) * quantity for BUY actions, or (entry_price - exit_price) * quantity for SELL actions.
**Validates: Requirements 2.2**

### Property 5: Profit/Loss Percentage Calculation
*For any* closed trade, the profit_loss_percent should equal ((exit_price - entry_price) / entry_price) * 100 for BUY actions, or ((entry_price - exit_price) / entry_price) * 100 for SELL actions.
**Validates: Requirements 2.3**

### Property 6: Holding Period Calculation
*For any* closed trade, the holding_period_days should equal the number of days between entry_date and exit_date.
**Validates: Requirements 2.4**

### Property 7: Trade Exit Completeness
*For any* trade exit, all exit fields (exit_price, exit_date, profit_loss, profit_loss_percent, holding_period_days) should be populated in the updated TradeRecord.
**Validates: Requirements 2.5**

### Property 8: Trade Exit Persistence
*For any* trade exit, after recording the exit and reloading from storage, the trade should have all exit data intact.
**Validates: Requirements 2.6**

### Property 9: Open Trades Filter
*For any* set of trades containing both open and closed trades, get_open_trades() should return only trades where exit_price is None.
**Validates: Requirements 3.1**

### Property 10: Closed Trades Date Range Filter
*For any* set of closed trades and date range, get_closed_trades(start_date, end_date) should return only trades where exit_date falls within the range.
**Validates: Requirements 3.2**

### Property 11: Trade Retrieval by ID
*For any* trade in the system, get_trade_by_id(trade_id) should return the trade with matching trade_id.
**Validates: Requirements 3.3**

### Property 12: Trade Retrieval by Symbol
*For any* set of trades, get_trades_by_symbol(symbol) should return only trades where the symbol matches.
**Validates: Requirements 3.4**

### Property 13: Module Performance Trade Counting
*For any* set of closed trades and module, analyze_module_performance() should correctly count total_trades, winning_trades (profit_loss_percent > 0), and losing_trades (profit_loss_percent <= 0).
**Validates: Requirements 4.2**

### Property 14: Module Performance Win Rate
*For any* module performance analysis, win_rate should equal (winning_trades / total_trades) * 100.
**Validates: Requirements 4.3**

### Property 15: Module Performance Average P/L
*For any* module performance analysis, avg_profit_loss should equal the mean of all profit_loss_percent values for relevant trades.
**Validates: Requirements 4.4**

### Property 16: Module Performance Total P/L
*For any* module performance analysis, total_profit_loss should equal the sum of all profit_loss_percent values for relevant trades.
**Validates: Requirements 4.5**

### Property 17: Recommended Weights Sum to One
*For any* set of module performances, calculate_recommended_weights() should return weights that sum to 1.0 (within floating point tolerance).
**Validates: Requirements 5.3**

### Property 18: Recommended Weights Minimum Constraint
*For any* set of module performances, calculate_recommended_weights() should return weights where no weight is less than 0.15.
**Validates: Requirements 5.4**

### Property 19: Recommended Weights Maximum Constraint
*For any* set of module performances, calculate_recommended_weights() should return weights where no weight exceeds 0.50.
**Validates: Requirements 5.5**

### Property 20: Monthly Report Trade Counts
*For any* monthly report, the sum of winning_trades and losing_trades should equal closed_trades.
**Validates: Requirements 6.3**

### Property 21: Monthly Report Win Rate
*For any* monthly report with closed trades, win_rate should equal (winning_trades / closed_trades) * 100.
**Validates: Requirements 6.3**

### Property 22: Monthly Report Best Trade Identification
*For any* monthly report with closed trades, best_trade should be the trade with the highest profit_loss_percent.
**Validates: Requirements 6.5**

### Property 23: Monthly Report Worst Trade Identification
*For any* monthly report with closed trades, worst_trade should be the trade with the lowest profit_loss_percent.
**Validates: Requirements 6.6**

### Property 24: Monthly Report Module Coverage
*For any* monthly report, module_performance should contain entries for all three modules: sentiment, technical, and fundamental.
**Validates: Requirements 6.7**

### Property 25: Monthly Report Persistence
*For any* generated monthly report, after reloading from storage, the report should exist with all original data intact.
**Validates: Requirements 6.9**

### Property 26: JSON Storage Round Trip
*For any* set of trades and reports, after saving to storage and reloading, all data should be equivalent to the original.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 27: Configuration Weight Application
*For any* recommended weights applied to configuration, the sentiment_weight, technical_weight, and fundamental_weight should be updated and sum to 1.0.
**Validates: Requirements 8.5, 8.6, 8.7**

### Property 28: Weight Adjustment Threshold
*For any* AgentCore initialization with auto_adjust_weights enabled, weights should only be adjusted if the number of closed trades is >= min_trades_for_adjustment.
**Validates: Requirements 9.5**

## Error Handling

### Trade Exit Errors

1. **Trade Not Found**: If trade_id does not exist, record_exit() returns None and logs an error
2. **Already Closed**: If trade already has exit_price, record_exit() logs a warning and returns the existing trade without modification
3. **Invalid Exit Price**: If exit_price is negative or zero, raise ValueError

### Storage Errors

1. **Load Failure**: If JSON loading fails, log error and start with empty data (graceful degradation)
2. **Save Failure**: If JSON saving fails, log error but continue operation (data remains in memory)
3. **Directory Creation**: Automatically create storage directory if it doesn't exist

### Module Performance Errors

1. **No Relevant Trades**: If no trades match module criteria, return ModulePerformance with zero values
2. **Empty Trade List**: If analyzing empty trade list, return ModulePerformance with zero values

### Weight Calculation Errors

1. **Zero Accuracy Scores**: If all accuracy scores are zero, assign equal weights (0.33 each)
2. **Missing Module**: If module performance is missing, use default weight of 0.33

## Testing Strategy

### Unit Testing

Unit tests should focus on:
- Individual method functionality (record_entry, record_exit, etc.)
- Edge cases (empty data, invalid inputs, boundary conditions)
- Error handling (missing trades, invalid prices, storage failures)
- Data model serialization/deserialization
- Configuration integration
- CLI command execution

### Property-Based Testing

Property-based tests should verify universal properties across randomized inputs. Each test should run a minimum of 100 iterations.

**Test Configuration**: Use Python's `hypothesis` library for property-based testing.

**Property Test 1: Trade Entry Completeness**
- Generate random trade entry parameters
- Record entry
- Verify all fields are populated
- **Feature: performance-tracker, Property 1: Trade Entry Completeness**

**Property Test 2: Trade ID Uniqueness**
- Generate multiple random trade entries
- Verify all trade IDs are unique
- **Feature: performance-tracker, Property 2: Trade ID Uniqueness**

**Property Test 3: Profit/Loss Calculation Accuracy**
- Generate random entry/exit prices and quantities
- Record entry and exit
- Verify P/L calculation matches formula
- **Feature: performance-tracker, Property 4: Profit/Loss Calculation Accuracy**

**Property Test 4: Profit/Loss Percentage Calculation**
- Generate random entry/exit prices
- Record entry and exit
- Verify P/L percentage matches formula
- **Feature: performance-tracker, Property 5: Profit/Loss Percentage Calculation**

**Property Test 5: Recommended Weights Sum to One**
- Generate random module performances
- Calculate recommended weights
- Verify weights sum to 1.0 (within tolerance)
- **Feature: performance-tracker, Property 17: Recommended Weights Sum to One**

**Property Test 6: Recommended Weights Constraints**
- Generate random module performances (including extreme values)
- Calculate recommended weights
- Verify all weights are >= 0.15 and <= 0.50
- **Feature: performance-tracker, Property 18 and 19: Recommended Weights Constraints**

**Property Test 7: JSON Storage Round Trip**
- Generate random trades and reports
- Save to storage
- Reload from storage
- Verify all data is equivalent
- **Feature: performance-tracker, Property 26: JSON Storage Round Trip**

**Property Test 8: Open Trades Filter**
- Generate random mix of open and closed trades
- Query open trades
- Verify only trades with exit_price=None are returned
- **Feature: performance-tracker, Property 9: Open Trades Filter**

**Property Test 9: Module Performance Win Rate**
- Generate random closed trades with known outcomes
- Analyze module performance
- Verify win_rate calculation matches formula
- **Feature: performance-tracker, Property 14: Module Performance Win Rate**

**Property Test 10: Configuration Weight Application**
- Generate random recommended weights
- Apply to configuration
- Verify weights are updated and sum to 1.0
- **Feature: performance-tracker, Property 27: Configuration Weight Application**

### Integration Testing

Integration tests should verify:
- End-to-end trade lifecycle (entry → exit → reporting)
- AgentCore initialization with performance tracking
- CLI commands with actual PerformanceTracker instance
- Storage persistence across multiple operations
- Weight adjustment workflow

### Test Data

Use realistic test data:
- Stock symbols: AAPL, TSLA, GOOGL, MSFT, AMZN
- Price ranges: $50 - $500
- Quantities: 1 - 100 shares
- Analysis scores: -1.0 to +1.0
- Confidence: 0.0 to 1.0
- Holding periods: 1 - 30 days
- P/L percentages: -20% to +20%
