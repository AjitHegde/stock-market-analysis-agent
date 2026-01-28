"""Unit tests for DataQualityMonitor component."""

import pytest
from datetime import datetime, timedelta
from src.data_quality_monitor import (
    DataQualityMonitor,
    DataQualityIssue,
    DataQualityReport
)


class TestDataQualityIssue:
    """Tests for DataQualityIssue dataclass."""
    
    def test_valid_issue_creation(self):
        """Test creating a valid data quality issue."""
        issue = DataQualityIssue(
            source="News API",
            severity="major",
            reason="Limited news sources",
            impact="Sentiment confidence reduced",
            confidence_penalty=0.15
        )
        
        assert issue.source == "News API"
        assert issue.severity == "major"
        assert issue.confidence_penalty == 0.15
    
    def test_invalid_severity(self):
        """Test that invalid severity raises ValueError."""
        with pytest.raises(ValueError, match="Severity must be"):
            DataQualityIssue(
                source="Test",
                severity="invalid",
                reason="Test",
                impact="Test",
                confidence_penalty=0.1
            )
    
    def test_invalid_penalty_too_high(self):
        """Test that penalty > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence penalty must be between"):
            DataQualityIssue(
                source="Test",
                severity="major",
                reason="Test",
                impact="Test",
                confidence_penalty=1.5
            )
    
    def test_invalid_penalty_negative(self):
        """Test that negative penalty raises ValueError."""
        with pytest.raises(ValueError, match="Confidence penalty must be between"):
            DataQualityIssue(
                source="Test",
                severity="major",
                reason="Test",
                impact="Test",
                confidence_penalty=-0.1
            )


class TestDataQualityReport:
    """Tests for DataQualityReport dataclass."""
    
    def test_report_with_no_issues(self):
        """Test report with no issues."""
        report = DataQualityReport(
            issues=[],
            total_confidence_penalty=0.0,
            has_critical_issues=False,
            timestamp=datetime.now()
        )
        
        assert len(report.issues) == 0
        assert report.total_confidence_penalty == 0.0
        assert not report.has_critical_issues
        assert report.get_banner_message() is None
    
    def test_report_with_critical_issue(self):
        """Test report with critical issue."""
        issue = DataQualityIssue(
            source="Price Data",
            severity="critical",
            reason="No price data available",
            impact="Analysis unavailable",
            confidence_penalty=0.30
        )
        
        report = DataQualityReport(
            issues=[issue],
            total_confidence_penalty=0.30,
            has_critical_issues=True,
            timestamp=datetime.now()
        )
        
        assert len(report.issues) == 1
        assert report.has_critical_issues
        
        banner = report.get_banner_message()
        assert banner is not None
        assert "Critical Data Issue" in banner
        assert "No price data available" in banner
    
    def test_report_with_major_issue(self):
        """Test report with major issue."""
        issue = DataQualityIssue(
            source="News API",
            severity="major",
            reason="Limited news sources",
            impact="Sentiment confidence reduced",
            confidence_penalty=0.15
        )
        
        report = DataQualityReport(
            issues=[issue],
            total_confidence_penalty=0.15,
            has_critical_issues=False,
            timestamp=datetime.now()
        )
        
        banner = report.get_banner_message()
        assert banner is not None
        assert "Limited Data Available" in banner
    
    def test_report_with_minor_issue(self):
        """Test report with minor issue."""
        issue = DataQualityIssue(
            source="Fundamental Data",
            severity="minor",
            reason="Missing some metrics",
            impact="Fundamental analysis slightly limited",
            confidence_penalty=0.05
        )
        
        report = DataQualityReport(
            issues=[issue],
            total_confidence_penalty=0.05,
            has_critical_issues=False,
            timestamp=datetime.now()
        )
        
        banner = report.get_banner_message()
        assert banner is not None
        assert "Minor Data Issues" in banner


class TestDataQualityMonitor:
    """Tests for DataQualityMonitor class."""
    
    def test_initialization(self):
        """Test monitor initialization."""
        monitor = DataQualityMonitor()
        assert len(monitor.issues) == 0
    
    def test_reset(self):
        """Test resetting the monitor."""
        monitor = DataQualityMonitor()
        
        # Add an issue
        monitor.check_news_availability([], expected_minimum=3)
        assert len(monitor.issues) > 0
        
        # Reset
        monitor.reset()
        assert len(monitor.issues) == 0
    
    def test_check_news_availability_no_sources(self):
        """Test checking news availability with no sources."""
        monitor = DataQualityMonitor()
        monitor.check_news_availability([], expected_minimum=3)
        
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "critical"
        assert issue.confidence_penalty == 0.30
        assert "No news sources" in issue.reason
    
    def test_check_news_availability_limited_sources(self):
        """Test checking news availability with limited sources."""
        monitor = DataQualityMonitor()
        monitor.check_news_availability([1, 2], expected_minimum=5)
        
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "major"
        assert issue.confidence_penalty == 0.15
        assert "Limited news sources" in issue.reason
    
    def test_check_news_availability_sufficient_sources(self):
        """Test checking news availability with sufficient sources."""
        monitor = DataQualityMonitor()
        monitor.check_news_availability([1, 2, 3, 4, 5], expected_minimum=3)
        
        assert len(monitor.issues) == 0
    
    def test_check_price_freshness_fresh(self):
        """Test checking price freshness with fresh data."""
        monitor = DataQualityMonitor()
        fresh_timestamp = datetime.now() - timedelta(hours=1)
        monitor.check_price_freshness(fresh_timestamp, max_age_hours=24)
        
        assert len(monitor.issues) == 0
    
    def test_check_price_freshness_stale(self):
        """Test checking price freshness with stale data."""
        monitor = DataQualityMonitor()
        stale_timestamp = datetime.now() - timedelta(hours=48)
        monitor.check_price_freshness(stale_timestamp, max_age_hours=24)
        
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "major"
        assert "hours old" in issue.reason
    
    def test_check_indicator_completeness_all_present(self):
        """Test checking indicator completeness with all indicators."""
        monitor = DataQualityMonitor()
        indicators = {
            'rsi': True,
            'macd': True,
            'ma_20': True,
            'ma_50': True
        }
        required = ['rsi', 'macd', 'ma_20', 'ma_50']
        
        monitor.check_indicator_completeness(indicators, required)
        assert len(monitor.issues) == 0
    
    def test_check_indicator_completeness_some_missing(self):
        """Test checking indicator completeness with some missing."""
        monitor = DataQualityMonitor()
        indicators = {
            'rsi': True,
            'macd': None,
            'ma_20': True,
            'ma_50': None
        }
        required = ['rsi', 'macd', 'ma_20', 'ma_50']
        
        monitor.check_indicator_completeness(indicators, required)
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "critical"  # More than half missing
        assert "macd" in issue.reason
        assert "ma_50" in issue.reason
    
    def test_check_indicator_completeness_few_missing(self):
        """Test checking indicator completeness with few missing."""
        monitor = DataQualityMonitor()
        indicators = {
            'rsi': True,
            'macd': None,
            'ma_20': True,
            'ma_50': True
        }
        required = ['rsi', 'macd', 'ma_20', 'ma_50']
        
        monitor.check_indicator_completeness(indicators, required)
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "major"  # Less than half missing
    
    def test_check_fundamental_completeness_all_present(self):
        """Test checking fundamental completeness with all metrics."""
        monitor = DataQualityMonitor()
        metrics = {
            'pe_ratio': 15.5,
            'pb_ratio': 2.3,
            'revenue_growth': 12.5
        }
        required = ['pe_ratio', 'pb_ratio', 'revenue_growth']
        
        monitor.check_fundamental_completeness(metrics, required)
        assert len(monitor.issues) == 0
    
    def test_check_fundamental_completeness_some_missing(self):
        """Test checking fundamental completeness with some missing."""
        monitor = DataQualityMonitor()
        metrics = {
            'pe_ratio': None,
            'pb_ratio': None,
            'revenue_growth': 12.5
        }
        required = ['pe_ratio', 'pb_ratio', 'revenue_growth']
        
        monitor.check_fundamental_completeness(metrics, required)
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "major"  # More than half missing
    
    def test_check_fundamental_completeness_few_missing(self):
        """Test checking fundamental completeness with few missing."""
        monitor = DataQualityMonitor()
        metrics = {
            'pe_ratio': None,
            'pb_ratio': 2.3,
            'revenue_growth': 12.5
        }
        required = ['pe_ratio', 'pb_ratio', 'revenue_growth']
        
        monitor.check_fundamental_completeness(metrics, required)
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "minor"  # Less than half missing
    
    def test_check_api_failures_news(self):
        """Test recording news API failure."""
        monitor = DataQualityMonitor()
        monitor.check_api_failures("NewsAPI", "Rate limit exceeded")
        
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "major"
        assert issue.confidence_penalty == 0.15
        assert "Rate limit exceeded" in issue.reason
    
    def test_check_api_failures_price(self):
        """Test recording price API failure."""
        monitor = DataQualityMonitor()
        monitor.check_api_failures("Yahoo Finance", "Connection timeout")
        
        assert len(monitor.issues) == 1
        issue = monitor.issues[0]
        assert issue.severity == "critical"
        assert issue.confidence_penalty == 0.30
    
    def test_generate_report_no_issues(self):
        """Test generating report with no issues."""
        monitor = DataQualityMonitor()
        report = monitor.generate_report()
        
        assert len(report.issues) == 0
        assert report.total_confidence_penalty == 0.0
        assert not report.has_critical_issues
    
    def test_generate_report_with_issues(self):
        """Test generating report with multiple issues."""
        monitor = DataQualityMonitor()
        
        # Add multiple issues
        monitor.check_news_availability([1], expected_minimum=5)
        monitor.check_api_failures("NewsAPI", "Rate limit")
        
        report = monitor.generate_report()
        
        assert len(report.issues) == 2
        assert report.total_confidence_penalty > 0
    
    def test_generate_report_penalty_capped(self):
        """Test that total penalty is capped at 50%."""
        monitor = DataQualityMonitor()
        
        # Add many issues that would exceed 50%
        monitor.check_news_availability([], expected_minimum=5)  # 0.30
        monitor.check_api_failures("Yahoo Finance", "Error")  # 0.30
        monitor.check_api_failures("NewsAPI", "Error")  # 0.15
        
        report = monitor.generate_report()
        
        # Total would be 0.75, but should be capped at 0.5
        assert report.total_confidence_penalty == 0.5
    
    def test_generate_report_detects_critical(self):
        """Test that report correctly detects critical issues."""
        monitor = DataQualityMonitor()
        monitor.check_news_availability([], expected_minimum=5)
        
        report = monitor.generate_report()
        assert report.has_critical_issues
    
    def test_apply_confidence_penalty_no_penalty(self):
        """Test applying confidence penalty with no issues."""
        monitor = DataQualityMonitor()
        report = monitor.generate_report()
        
        adjusted = monitor.apply_confidence_penalty(0.8, report)
        assert adjusted == 0.8
    
    def test_apply_confidence_penalty_with_penalty(self):
        """Test applying confidence penalty with issues."""
        monitor = DataQualityMonitor()
        monitor.check_news_availability([1], expected_minimum=5)  # 0.15 penalty
        
        report = monitor.generate_report()
        
        # Original confidence 0.8, penalty 0.15
        # Adjusted = 0.8 * (1 - 0.15) = 0.8 * 0.85 = 0.68
        adjusted = monitor.apply_confidence_penalty(0.8, report)
        assert adjusted == pytest.approx(0.68, rel=0.01)
    
    def test_apply_confidence_penalty_bounds(self):
        """Test that adjusted confidence stays within bounds."""
        monitor = DataQualityMonitor()
        
        # Add many issues
        monitor.check_news_availability([], expected_minimum=5)
        monitor.check_api_failures("Yahoo Finance", "Error")
        
        report = monitor.generate_report()
        
        # Even with high penalty, should not go below 0
        adjusted = monitor.apply_confidence_penalty(0.3, report)
        assert 0.0 <= adjusted <= 1.0
    
    def test_multiple_checks_accumulate(self):
        """Test that multiple checks accumulate issues."""
        monitor = DataQualityMonitor()
        
        # Add multiple different issues
        monitor.check_news_availability([1], expected_minimum=5)
        monitor.check_price_freshness(
            datetime.now() - timedelta(hours=48),
            max_age_hours=24
        )
        monitor.check_indicator_completeness(
            {'rsi': None, 'macd': True},
            ['rsi', 'macd']
        )
        
        assert len(monitor.issues) == 3
        
        report = monitor.generate_report()
        assert len(report.issues) == 3
        assert report.total_confidence_penalty > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
