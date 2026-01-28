"""Performance Tracker for Stock Market AI Agent.

This module tracks trading performance, analyzes accuracy by module,
and automatically adjusts recommendation weights based on historical performance.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import statistics


logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """Represents a single trade record.
    
    Attributes:
        trade_id: Unique identifier for the trade
        symbol: Stock ticker symbol
        action: Trade action ("BUY" or "SELL")
        entry_price: Entry price for the trade
        entry_date: Date when trade was entered
        exit_price: Exit price (None if still open)
        exit_date: Date when trade was exited (None if still open)
        quantity: Number of shares
        profit_loss: Profit/loss amount (None if still open)
        profit_loss_percent: Profit/loss percentage (None if still open)
        holding_period_days: Number of days held (None if still open)
        signal_source: Source of the signal ("sentiment", "technical", "fundamental", "combined")
        sentiment_score: Sentiment score at entry
        technical_score: Technical score at entry
        fundamental_score: Fundamental score at entry
        confidence: Recommendation confidence at entry
        market_state: Market state at entry
        notes: Optional notes about the trade
    """
    trade_id: str
    symbol: str
    action: str
    entry_price: float
    entry_date: str
    exit_price: Optional[float] = None
    exit_date: Optional[str] = None
    quantity: int = 1
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    holding_period_days: Optional[int] = None
    signal_source: str = "combined"
    sentiment_score: float = 0.0
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    confidence: float = 0.0
    market_state: str = "neutral"
    notes: str = ""


@dataclass
class ModulePerformance:
    """Performance metrics for a specific analysis module.
    
    Attributes:
        module_name: Name of the module ("sentiment", "technical", "fundamental")
        total_trades: Total number of trades
        winning_trades: Number of winning trades
        losing_trades: Number of losing trades
        win_rate: Percentage of winning trades
        avg_profit_loss: Average profit/loss percentage
        total_profit_loss: Total profit/loss percentage
        avg_holding_period: Average holding period in days
        accuracy_score: Overall accuracy score (0.0 to 1.0)
        recommended_weight: Recommended weight for this module
    """
    module_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_profit_loss: float = 0.0
    total_profit_loss: float = 0.0
    avg_holding_period: float = 0.0
    accuracy_score: float = 0.0
    recommended_weight: float = 0.33


@dataclass
class PerformanceReport:
    """Monthly performance report.
    
    Attributes:
        report_date: Date of the report
        period_start: Start date of the reporting period
        period_end: End date of the reporting period
        total_trades: Total number of trades in period
        open_trades: Number of open trades
        closed_trades: Number of closed trades
        winning_trades: Number of winning trades
        losing_trades: Number of losing trades
        win_rate: Overall win rate
        total_profit_loss: Total profit/loss
        avg_profit_loss: Average profit/loss per trade
        best_trade: Best performing trade
        worst_trade: Worst performing trade
        module_performance: Performance by module
        recommended_weights: Recommended weights for next period
    """
    report_date: str
    period_start: str
    period_end: str
    total_trades: int
    open_trades: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit_loss: float
    avg_profit_loss: float
    best_trade: Optional[Dict]
    worst_trade: Optional[Dict]
    module_performance: Dict[str, ModulePerformance]
    recommended_weights: Dict[str, float]


class PerformanceTracker:
    """Tracks trading performance and adjusts recommendation weights.
    
    This class maintains a database of trade records, analyzes performance
    by module, and automatically adjusts weights based on historical accuracy.
    """
    
    def __init__(self, storage_path: str = "data/performance.json"):
        """Initialize the performance tracker.
        
        Args:
            storage_path: Path to the JSON storage file
        """
        self.storage_path = Path(storage_path)
        self.trades: List[TradeRecord] = []
        self.reports: List[PerformanceReport] = []
        
        # Create data directory if it doesn't exist
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_data()
        
        logger.info(f"PerformanceTracker initialized: {len(self.trades)} trades loaded")
    
    def _load_data(self):
        """Load trade records and reports from storage."""
        if not self.storage_path.exists():
            logger.info("No existing performance data found, starting fresh")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Load trades
            self.trades = [
                TradeRecord(**trade) for trade in data.get('trades', [])
            ]
            
            # Load reports
            reports_data = data.get('reports', [])
            self.reports = []
            for report_data in reports_data:
                # Convert module_performance dict back to ModulePerformance objects
                module_perf = {}
                for module_name, perf_dict in report_data.get('module_performance', {}).items():
                    module_perf[module_name] = ModulePerformance(**perf_dict)
                
                report_data['module_performance'] = module_perf
                self.reports.append(PerformanceReport(**report_data))
            
            logger.info(f"Loaded {len(self.trades)} trades and {len(self.reports)} reports")
            
        except Exception as e:
            logger.error(f"Failed to load performance data: {str(e)}")
            self.trades = []
            self.reports = []
    
    def _save_data(self):
        """Save trade records and reports to storage."""
        try:
            # Convert trades to dicts
            trades_data = [asdict(trade) for trade in self.trades]
            
            # Convert reports to dicts
            reports_data = []
            for report in self.reports:
                report_dict = asdict(report)
                # Convert ModulePerformance objects to dicts
                module_perf_dict = {}
                for module_name, perf in report.module_performance.items():
                    module_perf_dict[module_name] = asdict(perf)
                report_dict['module_performance'] = module_perf_dict
                reports_data.append(report_dict)
            
            data = {
                'trades': trades_data,
                'reports': reports_data,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(self.trades)} trades and {len(self.reports)} reports")
            
        except Exception as e:
            logger.error(f"Failed to save performance data: {str(e)}")
    
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
        """Record a trade entry.
        
        Args:
            symbol: Stock ticker symbol
            action: Trade action ("BUY" or "SELL")
            entry_price: Entry price
            quantity: Number of shares
            sentiment_score: Sentiment score at entry
            technical_score: Technical score at entry
            fundamental_score: Fundamental score at entry
            confidence: Recommendation confidence
            market_state: Market state at entry
            signal_source: Source of the signal
            notes: Optional notes
            
        Returns:
            Trade ID
        """
        # Generate unique trade ID
        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        trade = TradeRecord(
            trade_id=trade_id,
            symbol=symbol,
            action=action,
            entry_price=entry_price,
            entry_date=datetime.now().isoformat(),
            quantity=quantity,
            signal_source=signal_source,
            sentiment_score=sentiment_score,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            confidence=confidence,
            market_state=market_state,
            notes=notes
        )
        
        self.trades.append(trade)
        self._save_data()
        
        logger.info(f"Recorded entry: {trade_id} - {action} {quantity} {symbol} @ ${entry_price:.2f}")
        
        return trade_id
    
    def record_exit(
        self,
        trade_id: str,
        exit_price: float,
        notes: str = ""
    ) -> Optional[TradeRecord]:
        """Record a trade exit.
        
        Args:
            trade_id: Trade ID to close
            exit_price: Exit price
            notes: Optional notes
            
        Returns:
            Updated TradeRecord or None if not found
        """
        # Find the trade
        trade = None
        for t in self.trades:
            if t.trade_id == trade_id:
                trade = t
                break
        
        if not trade:
            logger.error(f"Trade not found: {trade_id}")
            return None
        
        if trade.exit_price is not None:
            logger.warning(f"Trade already closed: {trade_id}")
            return trade
        
        # Calculate profit/loss
        if trade.action == "BUY":
            profit_loss = (exit_price - trade.entry_price) * trade.quantity
            profit_loss_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
        else:  # SELL
            profit_loss = (trade.entry_price - exit_price) * trade.quantity
            profit_loss_percent = ((trade.entry_price - exit_price) / trade.entry_price) * 100
        
        # Calculate holding period
        entry_date = datetime.fromisoformat(trade.entry_date)
        exit_date = datetime.now()
        holding_period = (exit_date - entry_date).days
        
        # Update trade
        trade.exit_price = exit_price
        trade.exit_date = exit_date.isoformat()
        trade.profit_loss = profit_loss
        trade.profit_loss_percent = profit_loss_percent
        trade.holding_period_days = holding_period
        if notes:
            trade.notes = f"{trade.notes}\nExit: {notes}" if trade.notes else notes
        
        self._save_data()
        
        logger.info(
            f"Recorded exit: {trade_id} - {trade.action} {trade.symbol} @ ${exit_price:.2f} "
            f"(P/L: {profit_loss_percent:+.2f}%, {holding_period} days)"
        )
        
        return trade
    
    def get_open_trades(self) -> List[TradeRecord]:
        """Get all open trades.
        
        Returns:
            List of open TradeRecords
        """
        return [t for t in self.trades if t.exit_price is None]
    
    def get_closed_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TradeRecord]:
        """Get closed trades within a date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of closed TradeRecords
        """
        closed = [t for t in self.trades if t.exit_price is not None]
        
        if start_date or end_date:
            filtered = []
            for trade in closed:
                exit_date = datetime.fromisoformat(trade.exit_date)
                
                if start_date and exit_date < start_date:
                    continue
                if end_date and exit_date > end_date:
                    continue
                
                filtered.append(trade)
            
            return filtered
        
        return closed
    
    def analyze_module_performance(
        self,
        module_name: str,
        trades: List[TradeRecord]
    ) -> ModulePerformance:
        """Analyze performance for a specific module.
        
        Args:
            module_name: Name of the module
            trades: List of closed trades to analyze
            
        Returns:
            ModulePerformance metrics
        """
        if not trades:
            return ModulePerformance(module_name=module_name)
        
        # Filter trades where this module had strong signal
        # Strong signal = module score > 0.3 or module was the signal source
        relevant_trades = []
        for trade in trades:
            if module_name == "sentiment" and (abs(trade.sentiment_score) > 0.3 or trade.signal_source == "sentiment"):
                relevant_trades.append(trade)
            elif module_name == "technical" and (abs(trade.technical_score) > 0.3 or trade.signal_source == "technical"):
                relevant_trades.append(trade)
            elif module_name == "fundamental" and (abs(trade.fundamental_score) > 0.3 or trade.signal_source == "fundamental"):
                relevant_trades.append(trade)
        
        if not relevant_trades:
            return ModulePerformance(module_name=module_name)
        
        # Calculate metrics
        total_trades = len(relevant_trades)
        winning_trades = len([t for t in relevant_trades if t.profit_loss_percent > 0])
        losing_trades = len([t for t in relevant_trades if t.profit_loss_percent <= 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        profit_losses = [t.profit_loss_percent for t in relevant_trades]
        avg_profit_loss = statistics.mean(profit_losses) if profit_losses else 0.0
        total_profit_loss = sum(profit_losses)
        
        holding_periods = [t.holding_period_days for t in relevant_trades if t.holding_period_days is not None]
        avg_holding_period = statistics.mean(holding_periods) if holding_periods else 0.0
        
        # Calculate accuracy score (0.0 to 1.0)
        # Factors: win rate (40%), avg P/L (40%), consistency (20%)
        win_rate_score = win_rate / 100.0
        
        # Normalize avg P/L to 0-1 scale (assume -20% to +20% range)
        pl_score = max(0.0, min(1.0, (avg_profit_loss + 20) / 40))
        
        # Consistency score based on standard deviation (lower is better)
        if len(profit_losses) > 1:
            std_dev = statistics.stdev(profit_losses)
            consistency_score = max(0.0, 1.0 - (std_dev / 50))  # Normalize to 0-1
        else:
            consistency_score = 0.5
        
        accuracy_score = (win_rate_score * 0.4) + (pl_score * 0.4) + (consistency_score * 0.2)
        
        return ModulePerformance(
            module_name=module_name,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit_loss=avg_profit_loss,
            total_profit_loss=total_profit_loss,
            avg_holding_period=avg_holding_period,
            accuracy_score=accuracy_score,
            recommended_weight=0.33  # Will be calculated later
        )
    
    def calculate_recommended_weights(
        self,
        module_performances: Dict[str, ModulePerformance]
    ) -> Dict[str, float]:
        """Calculate recommended weights based on module performance.
        
        Uses accuracy scores to determine optimal weights that sum to 1.0.
        
        Args:
            module_performances: Performance metrics by module
            
        Returns:
            Dictionary of recommended weights
        """
        # Get accuracy scores
        scores = {
            name: perf.accuracy_score
            for name, perf in module_performances.items()
        }
        
        # If all scores are zero, use equal weights
        total_score = sum(scores.values())
        if total_score == 0:
            return {name: 1.0 / len(scores) for name in scores}
        
        # Calculate weights proportional to accuracy scores
        weights = {
            name: score / total_score
            for name, score in scores.items()
        }
        
        # Apply constraints: no weight below 0.15 or above 0.50
        # This prevents over-reliance on a single module
        MIN_WEIGHT = 0.15
        MAX_WEIGHT = 0.50
        
        adjusted_weights = {}
        for name, weight in weights.items():
            adjusted_weights[name] = max(MIN_WEIGHT, min(MAX_WEIGHT, weight))
        
        # Normalize to sum to 1.0
        total_weight = sum(adjusted_weights.values())
        normalized_weights = {
            name: weight / total_weight
            for name, weight in adjusted_weights.items()
        }
        
        return normalized_weights
    
    def generate_monthly_report(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> PerformanceReport:
        """Generate a monthly performance report.
        
        Args:
            month: Month (1-12), defaults to last month
            year: Year, defaults to current year
            
        Returns:
            PerformanceReport
        """
        # Determine reporting period
        now = datetime.now()
        if month is None or year is None:
            # Default to last month
            if now.month == 1:
                month = 12
                year = now.year - 1
            else:
                month = now.month - 1
                year = now.year
        
        # Calculate period boundaries
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Get trades for this period
        closed_trades = self.get_closed_trades(period_start, period_end)
        open_trades = self.get_open_trades()
        
        # Calculate overall metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in closed_trades if t.profit_loss_percent > 0])
        losing_trades = len([t for t in closed_trades if t.profit_loss_percent <= 0])
        win_rate = (winning_trades / len(closed_trades)) * 100 if closed_trades else 0.0
        
        profit_losses = [t.profit_loss_percent for t in closed_trades]
        total_profit_loss = sum(profit_losses) if profit_losses else 0.0
        avg_profit_loss = statistics.mean(profit_losses) if profit_losses else 0.0
        
        # Find best and worst trades
        best_trade = None
        worst_trade = None
        if closed_trades:
            best_trade_obj = max(closed_trades, key=lambda t: t.profit_loss_percent)
            best_trade = {
                'symbol': best_trade_obj.symbol,
                'profit_loss_percent': best_trade_obj.profit_loss_percent,
                'entry_date': best_trade_obj.entry_date,
                'exit_date': best_trade_obj.exit_date
            }
            
            worst_trade_obj = min(closed_trades, key=lambda t: t.profit_loss_percent)
            worst_trade = {
                'symbol': worst_trade_obj.symbol,
                'profit_loss_percent': worst_trade_obj.profit_loss_percent,
                'entry_date': worst_trade_obj.entry_date,
                'exit_date': worst_trade_obj.exit_date
            }
        
        # Analyze module performance
        module_performance = {}
        for module_name in ['sentiment', 'technical', 'fundamental']:
            module_performance[module_name] = self.analyze_module_performance(
                module_name, closed_trades
            )
        
        # Calculate recommended weights
        recommended_weights = self.calculate_recommended_weights(module_performance)
        
        # Update module performance with recommended weights
        for module_name, weight in recommended_weights.items():
            module_performance[module_name].recommended_weight = weight
        
        # Create report
        report = PerformanceReport(
            report_date=now.isoformat(),
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            total_trades=total_trades,
            open_trades=len(open_trades),
            closed_trades=len(closed_trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit_loss=total_profit_loss,
            avg_profit_loss=avg_profit_loss,
            best_trade=best_trade,
            worst_trade=worst_trade,
            module_performance=module_performance,
            recommended_weights=recommended_weights
        )
        
        # Save report
        self.reports.append(report)
        self._save_data()
        
        logger.info(
            f"Generated monthly report for {month}/{year}: "
            f"{len(closed_trades)} trades, {win_rate:.1f}% win rate, "
            f"{total_profit_loss:+.2f}% total P/L"
        )
        
        return report
    
    def get_latest_recommended_weights(self) -> Optional[Dict[str, float]]:
        """Get the latest recommended weights from the most recent report.
        
        Returns:
            Dictionary of recommended weights or None if no reports exist
        """
        if not self.reports:
            return None
        
        latest_report = self.reports[-1]
        return latest_report.recommended_weights
    
    def get_trade_by_id(self, trade_id: str) -> Optional[TradeRecord]:
        """Get a trade by its ID.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            TradeRecord or None if not found
        """
        for trade in self.trades:
            if trade.trade_id == trade_id:
                return trade
        return None
    
    def get_trades_by_symbol(self, symbol: str) -> List[TradeRecord]:
        """Get all trades for a specific symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            List of TradeRecords
        """
        return [t for t in self.trades if t.symbol == symbol]
