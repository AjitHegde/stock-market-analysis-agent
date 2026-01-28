"""Stock Market AI Agent - A personal trading assistant."""

__version__ = "0.1.0"

from .config import Configuration
from .models import (
    PricePoint,
    StockData,
    SentimentSource,
    SentimentData,
    TechnicalIndicators,
    FundamentalMetrics,
    Recommendation,
    Position,
    ConcentrationRisk,
    CorrelationRisk,
    RiskAssessment,
    AnalysisResult,
)

__all__ = [
    "Configuration",
    "PricePoint",
    "StockData",
    "SentimentSource",
    "SentimentData",
    "TechnicalIndicators",
    "FundamentalMetrics",
    "Recommendation",
    "Position",
    "ConcentrationRisk",
    "CorrelationRisk",
    "RiskAssessment",
    "AnalysisResult",
]
