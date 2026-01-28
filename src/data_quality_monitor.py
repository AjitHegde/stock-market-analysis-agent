"""Data Quality Monitor for Stock Market AI Agent.

This module monitors data quality and availability across all data sources,
tracking issues and automatically adjusting confidence when data is missing.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DataQualityIssue:
    """Represents a data quality issue.
    
    Attributes:
        source: Name of the data source (e.g., "NewsAPI", "Price Data")
        severity: Severity level ("critical", "major", "minor")
        reason: Human-readable reason for the issue
        impact: Description of the impact on analysis
        confidence_penalty: Percentage to reduce confidence (0.0 to 1.0)
    """
    source: str
    severity: str
    reason: str
    impact: str
    confidence_penalty: float
    
    def __post_init__(self):
        """Validate data quality issue."""
        if self.severity not in ["critical", "major", "minor"]:
            raise ValueError("Severity must be 'critical', 'major', or 'minor'")
        if not 0.0 <= self.confidence_penalty <= 1.0:
            raise ValueError("Confidence penalty must be between 0.0 and 1.0")


@dataclass
class DataQualityReport:
    """Represents a complete data quality report.
    
    Attributes:
        issues: List of data quality issues found
        total_confidence_penalty: Total confidence reduction (0.0 to 1.0)
        has_critical_issues: Whether any critical issues exist
        timestamp: When the report was generated
    """
    issues: List[DataQualityIssue]
    total_confidence_penalty: float
    has_critical_issues: bool
    timestamp: datetime
    
    def get_banner_message(self) -> Optional[str]:
        """Get banner message if issues exist.
        
        Returns:
            Banner message string or None if no issues
        """
        if not self.issues:
            return None
        
        # Get the most severe issue for the banner
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        major_issues = [i for i in self.issues if i.severity == "major"]
        
        if critical_issues:
            issue = critical_issues[0]
            return f"⚠️ Critical Data Issue: {issue.reason}\nImpact: {issue.impact}"
        elif major_issues:
            issue = major_issues[0]
            return f"⚠️ Limited Data Available: {issue.reason}\nImpact: {issue.impact}"
        else:
            return f"ℹ️ Minor Data Issues: {len(self.issues)} data quality issues detected"


class DataQualityMonitor:
    """Monitors data quality and availability across all sources."""
    
    def __init__(self):
        """Initialize the data quality monitor."""
        self.issues: List[DataQualityIssue] = []
    
    def check_news_availability(
        self,
        news_sources: List,
        expected_minimum: int = 3
    ) -> None:
        """Check if sufficient news sources are available.
        
        Args:
            news_sources: List of news sources retrieved
            expected_minimum: Minimum expected number of sources
        """
        if len(news_sources) == 0:
            self.issues.append(DataQualityIssue(
                source="News Data",
                severity="critical",
                reason="No news sources available",
                impact="Sentiment analysis unavailable, confidence severely reduced",
                confidence_penalty=0.30
            ))
            logger.error("Critical: No news sources available for sentiment analysis")
        elif len(news_sources) < expected_minimum:
            self.issues.append(DataQualityIssue(
                source="News Data",
                severity="major",
                reason=f"Limited news sources ({len(news_sources)} of {expected_minimum} expected)",
                impact="Sentiment confidence reduced due to limited data",
                confidence_penalty=0.15
            ))
            logger.warning(f"Major: Only {len(news_sources)} news sources available (expected {expected_minimum})")
    
    def check_price_freshness(
        self,
        price_timestamp: datetime,
        max_age_hours: int = 24
    ) -> None:
        """Check if price data is fresh.
        
        Args:
            price_timestamp: Timestamp of the price data
            max_age_hours: Maximum acceptable age in hours
        """
        age = datetime.now() - price_timestamp
        
        if age > timedelta(hours=max_age_hours):
            hours_old = age.total_seconds() / 3600
            self.issues.append(DataQualityIssue(
                source="Price Data",
                severity="major",
                reason=f"Price data is {hours_old:.1f} hours old",
                impact="Technical analysis may be outdated",
                confidence_penalty=0.10
            ))
            logger.warning(f"Major: Price data is {hours_old:.1f} hours old")
    
    def check_indicator_completeness(
        self,
        technical_indicators: dict,
        required_indicators: List[str]
    ) -> None:
        """Check if all required technical indicators are available.
        
        Args:
            technical_indicators: Dictionary of available indicators
            required_indicators: List of required indicator names
        """
        missing = []
        for indicator in required_indicators:
            if indicator not in technical_indicators or technical_indicators[indicator] is None:
                missing.append(indicator)
        
        if missing:
            if len(missing) >= len(required_indicators) / 2:
                # More than half missing = critical
                self.issues.append(DataQualityIssue(
                    source="Technical Indicators",
                    severity="critical",
                    reason=f"Missing critical indicators: {', '.join(missing)}",
                    impact="Technical analysis severely limited",
                    confidence_penalty=0.25
                ))
                logger.error(f"Critical: Missing indicators: {missing}")
            else:
                # Less than half missing = major
                self.issues.append(DataQualityIssue(
                    source="Technical Indicators",
                    severity="major",
                    reason=f"Missing indicators: {', '.join(missing)}",
                    impact="Technical analysis partially limited",
                    confidence_penalty=0.10
                ))
                logger.warning(f"Major: Missing indicators: {missing}")
    
    def check_fundamental_completeness(
        self,
        fundamental_metrics: dict,
        required_metrics: List[str]
    ) -> None:
        """Check if all required fundamental metrics are available.
        
        Args:
            fundamental_metrics: Dictionary of available metrics
            required_metrics: List of required metric names
        """
        missing = []
        for metric in required_metrics:
            if metric not in fundamental_metrics or fundamental_metrics[metric] is None:
                missing.append(metric)
        
        if missing:
            if len(missing) >= len(required_metrics) / 2:
                # More than half missing = major
                self.issues.append(DataQualityIssue(
                    source="Fundamental Data",
                    severity="major",
                    reason=f"Missing key metrics: {', '.join(missing)}",
                    impact="Fundamental analysis limited",
                    confidence_penalty=0.15
                ))
                logger.warning(f"Major: Missing fundamental metrics: {missing}")
            else:
                # Less than half missing = minor
                self.issues.append(DataQualityIssue(
                    source="Fundamental Data",
                    severity="minor",
                    reason=f"Missing some metrics: {', '.join(missing)}",
                    impact="Fundamental analysis slightly limited",
                    confidence_penalty=0.05
                ))
                logger.info(f"Minor: Missing fundamental metrics: {missing}")
    
    def check_api_failures(
        self,
        api_name: str,
        error_message: str
    ) -> None:
        """Record an API failure.
        
        Args:
            api_name: Name of the API that failed
            error_message: Error message from the API
        """
        # Determine severity based on API
        if "news" in api_name.lower():
            severity = "major"
            impact = "Sentiment analysis unavailable or limited"
            penalty = 0.15
        elif "price" in api_name.lower() or "yahoo" in api_name.lower():
            severity = "critical"
            impact = "Price and technical analysis unavailable"
            penalty = 0.30
        else:
            severity = "major"
            impact = "Some analysis features unavailable"
            penalty = 0.10
        
        self.issues.append(DataQualityIssue(
            source=api_name,
            severity=severity,
            reason=f"API failure: {error_message}",
            impact=impact,
            confidence_penalty=penalty
        ))
        logger.error(f"{severity.capitalize()}: {api_name} API failure: {error_message}")
    
    def generate_report(self) -> DataQualityReport:
        """Generate a data quality report.
        
        Returns:
            DataQualityReport with all issues and penalties
        """
        # Calculate total confidence penalty (capped at 0.5 = 50%)
        total_penalty = min(0.5, sum(issue.confidence_penalty for issue in self.issues))
        
        # Check for critical issues
        has_critical = any(issue.severity == "critical" for issue in self.issues)
        
        report = DataQualityReport(
            issues=self.issues.copy(),
            total_confidence_penalty=total_penalty,
            has_critical_issues=has_critical,
            timestamp=datetime.now()
        )
        
        if self.issues:
            logger.info(
                f"Data quality report: {len(self.issues)} issues found, "
                f"total confidence penalty: {total_penalty:.1%}"
            )
        
        return report
    
    def reset(self) -> None:
        """Reset the monitor for a new analysis."""
        self.issues.clear()
    
    def apply_confidence_penalty(
        self,
        original_confidence: float,
        report: DataQualityReport
    ) -> float:
        """Apply confidence penalty from data quality issues.
        
        Args:
            original_confidence: Original confidence score (0.0 to 1.0)
            report: Data quality report with penalties
        
        Returns:
            Adjusted confidence score (0.0 to 1.0)
        """
        adjusted = original_confidence * (1.0 - report.total_confidence_penalty)
        
        # Ensure it stays within bounds
        adjusted = max(0.0, min(1.0, adjusted))
        
        if report.total_confidence_penalty > 0:
            logger.info(
                f"Applied confidence penalty: {original_confidence:.1%} → {adjusted:.1%} "
                f"(penalty: {report.total_confidence_penalty:.1%})"
            )
        
        return adjusted
