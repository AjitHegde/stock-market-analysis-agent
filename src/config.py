"""Configuration management for Stock Market AI Agent."""

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv


@dataclass
class Configuration:
    """Configuration settings for the Stock Market AI Agent.
    
    Attributes:
        api_keys: Dictionary of API keys for various data providers
        risk_tolerance: Risk tolerance level (conservative, moderate, aggressive)
        sentiment_weight: Weight for sentiment analysis (0.0 to 1.0)
        technical_weight: Weight for technical analysis (0.0 to 1.0)
        fundamental_weight: Weight for fundamental analysis (0.0 to 1.0)
        cache_ttl_seconds: Time-to-live for cached data in seconds
        performance_tracking_enabled: Enable performance tracking
        performance_storage_path: Path to performance data storage
        auto_adjust_weights: Automatically adjust weights based on performance
        min_trades_for_adjustment: Minimum trades before adjusting weights
    """
    
    api_keys: Dict[str, str] = field(default_factory=dict)
    risk_tolerance: str = "moderate"
    sentiment_weight: float = 0.5
    technical_weight: float = 0.3
    fundamental_weight: float = 0.2
    cache_ttl_seconds: int = 300
    performance_tracking_enabled: bool = True
    performance_storage_path: str = "data/performance.json"
    auto_adjust_weights: bool = False
    min_trades_for_adjustment: int = 20
    
    def __post_init__(self):
        """Load API keys from environment variables if not provided."""
        load_dotenv()
        
        # Load API keys from environment if not already set
        env_keys = {
            'news_api': 'NEWS_API_KEY',
            'alpha_vantage': 'ALPHA_VANTAGE_API_KEY',
            'twitter': 'TWITTER_API_KEY',
            'reddit': 'REDDIT_API_KEY',
            'finnhub': 'FINNHUB_API_KEY',
        }
        
        for key_name, env_var in env_keys.items():
            if key_name not in self.api_keys or not self.api_keys[key_name]:
                env_value = os.getenv(env_var)
                if env_value:
                    self.api_keys[key_name] = env_value
        
        # Also check for direct finnhub_api_key attribute
        if not hasattr(self, 'finnhub_api_key') or not self.finnhub_api_key:
            self.finnhub_api_key = os.getenv('FINNHUB_API_KEY', self.api_keys.get('finnhub', ''))
    
    @classmethod
    def load(cls, config_path: str = "config.json") -> "Configuration":
        """Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration instance loaded from file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        path = Path(config_path)
        
        if not path.exists():
            # Return default configuration if file doesn't exist
            return cls()
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls(**data)
    
    def save(self, config_path: str = "config.json") -> None:
        """Save configuration to a JSON file.
        
        Args:
            config_path: Path where configuration will be saved
        """
        path = Path(config_path)
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    def validate_weights(self) -> bool:
        """Validate that analysis weights are in valid range [0.0, 1.0].
        
        Returns:
            True if all weights are valid, False otherwise
        """
        weights = [self.sentiment_weight, self.technical_weight, self.fundamental_weight]
        return all(0.0 <= w <= 1.0 for w in weights)
    
    def normalize_weights(self) -> None:
        """Normalize analysis weights to sum to 1.0."""
        total = self.sentiment_weight + self.technical_weight + self.fundamental_weight
        
        if total == 0:
            # If all weights are 0, set to default
            self.sentiment_weight = 0.5
            self.technical_weight = 0.3
            self.fundamental_weight = 0.2
        elif total != 1.0:
            # Normalize to sum to 1.0
            self.sentiment_weight /= total
            self.technical_weight /= total
            self.fundamental_weight /= total
    
    def apply_recommended_weights(self, recommended_weights: Dict[str, float]) -> None:
        """Apply recommended weights from performance tracking.
        
        Args:
            recommended_weights: Dictionary with 'sentiment', 'technical', 'fundamental' keys
        """
        if 'sentiment' in recommended_weights:
            self.sentiment_weight = recommended_weights['sentiment']
        if 'technical' in recommended_weights:
            self.technical_weight = recommended_weights['technical']
        if 'fundamental' in recommended_weights:
            self.fundamental_weight = recommended_weights['fundamental']
        
        # Ensure weights are normalized
        self.normalize_weights()
