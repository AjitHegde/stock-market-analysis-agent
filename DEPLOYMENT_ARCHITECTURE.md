# Deployment Architecture

Visual guide to the Stock Market AI Agent deployment architecture on AWS Lightsail.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS/HTTP
                             │
                    ┌────────▼────────┐
                    │   User Browser  │
                    │                 │
                    │  Access URL:    │
                    │  http://IP:8501 │
                    └────────┬────────┘
                             │
                             │ Port 8501
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    AWS Lightsail Instance                        │
│                    (Ubuntu 22.04 LTS)                            │
│                    $10/month                                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Docker Container                          │    │
│  │              (stock-market-ai-agent)                   │    │
│  │                                                        │    │
│  │  ┌──────────────────────────────────────────────┐    │    │
│  │  │      Streamlit Web Application               │    │    │
│  │  │      (src/web_ui.py)                         │    │    │
│  │  │                                              │    │    │
│  │  │  Port: 8501                                  │    │    │
│  │  │  Health Check: /_stcore/health               │    │    │
│  │  └──────────────────────────────────────────────┘    │    │
│  │                                                        │    │
│  │  ┌──────────────────────────────────────────────┐    │    │
│  │  │      Application Core                        │    │    │
│  │  │                                              │    │    │
│  │  │  • AgentCore (orchestration)                 │    │    │
│  │  │  • SentimentAnalyzer (FinBERT)               │    │    │
│  │  │  • TechnicalAnalyzer (indicators)            │    │    │
│  │  │  • FundamentalAnalyzer (metrics)             │    │    │
│  │  │  • RecommendationEngine (decisions)          │    │    │
│  │  │  • DataQualityMonitor (validation)           │    │    │
│  │  └──────────────────────────────────────────────┘    │    │
│  │                                                        │    │
│  │  Environment Variables:                                │    │
│  │  • NEWS_API_KEY                                        │    │
│  │  • FINNHUB_API_KEY                                     │    │
│  │  • ALPHA_VANTAGE_API_KEY                               │    │
│  │                                                        │    │
│  │  Volumes:                                              │    │
│  │  • ./data:/app/data (persistent storage)              │    │
│  │                                                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Firewall Rules:                                                │
│  • Port 22 (SSH) - Management                                   │
│  • Port 8501 (HTTP) - Application                               │
│                                                                  │
│  Resources:                                                      │
│  • 2 GB RAM                                                      │
│  • 1 vCPU                                                        │
│  • 60 GB SSD                                                     │
│  • 3 TB Transfer/month                                           │
└──────────────────────────────────────────────────────────────────┘
                             │
                             │ API Calls
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    External Data Sources                         │
│                                                                  │
│  • Yahoo Finance (stock prices, news)                           │
│  • Finnhub API (company news, fundamentals)                     │
│  • NewsAPI (news articles)                                      │
│  • Alpha Vantage (market data)                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Request Flow

```
1. User enters stock symbol in browser
   │
   ▼
2. Browser sends HTTP request to Lightsail IP:8501
   │
   ▼
3. Lightsail firewall allows port 8501
   │
   ▼
4. Docker container receives request
   │
   ▼
5. Streamlit processes request
   │
   ▼
6. AgentCore orchestrates analysis:
   │
   ├─▶ DataProvider fetches data from APIs
   │   ├─▶ Yahoo Finance (prices, news)
   │   ├─▶ Finnhub (news, fundamentals)
   │   └─▶ NewsAPI (news articles)
   │
   ├─▶ SentimentAnalyzer analyzes news (FinBERT)
   │
   ├─▶ TechnicalAnalyzer calculates indicators
   │
   ├─▶ FundamentalAnalyzer evaluates metrics
   │
   ├─▶ DataQualityMonitor validates data
   │
   └─▶ RecommendationEngine generates decision
   │
   ▼
7. Results rendered in Streamlit UI
   │
   ▼
8. HTML response sent to browser
   │
   ▼
9. User sees analysis results (25-30 seconds)
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Input                               │
│                    (Stock Symbol: AAPL)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Collection                             │
│                                                                  │
│  Yahoo Finance          Finnhub API         NewsAPI              │
│  ├─ Current Price       ├─ Company News     ├─ News Articles    │
│  ├─ Historical Data     ├─ Fundamentals     └─ Headlines        │
│  └─ Basic News          └─ Metrics                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Quality Check                            │
│                                                                  │
│  • News availability (critical)                                  │
│  • Price freshness (major)                                       │
│  • Indicator completeness (major)                                │
│  • Fundamental completeness (minor)                              │
│  • API failures (varies)                                         │
│                                                                  │
│  → Confidence penalties applied if issues found                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Parallel Analysis                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Sentiment   │  │  Technical   │  │ Fundamental  │         │
│  │   Analysis   │  │   Analysis   │  │   Analysis   │         │
│  │              │  │              │  │              │         │
│  │  FinBERT     │  │  RSI, MACD   │  │  P/E, P/B    │         │
│  │  News Score  │  │  MA, Trends  │  │  Growth      │         │
│  │              │  │              │  │              │         │
│  │  Score: +0.45│  │  Score: +0.32│  │  Score: +0.28│         │
│  │  Conf:  85%  │  │  Conf:  78%  │  │  Conf:  72%  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Recommendation Engine                           │
│                                                                  │
│  • Weighted combination of scores                                │
│  • Dynamic weight adjustment (market context)                    │
│  • Risk adjustments (volatility, market state)                   │
│  • No-trade zone detection                                       │
│  • Confidence calculation                                        │
│                                                                  │
│  → Final Recommendation: BUY (78% confidence)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      UI Rendering                                │
│                                                                  │
│  • Current price & volume                                        │
│  • Recommendation (BUY/SELL/HOLD)                                │
│  • Confidence breakdown                                          │
│  • Analyzer scores                                               │
│  • Market context                                                │
│  • Data quality warnings                                         │
│  • Interactive charts                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      User Display                                │
│                   (Browser Interface)                            │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layers                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  Presentation Layer                     │    │
│  │                                                        │    │
│  │  • Streamlit Web UI (src/web_ui.py)                   │    │
│  │  • CLI Interface (src/cli.py)                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  Orchestration Layer                    │    │
│  │                                                        │    │
│  │  • AgentCore (src/agent_core.py)                      │    │
│  │    - Coordinates all analyzers                        │    │
│  │    - Manages data flow                                │    │
│  │    - Handles caching                                  │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                   Analysis Layer                        │    │
│  │                                                        │    │
│  │  • SentimentAnalyzer (src/sentiment_analyzer.py)      │    │
│  │  • TechnicalAnalyzer (src/technical_analyzer.py)      │    │
│  │  • FundamentalAnalyzer (src/fundamental_analyzer.py)  │    │
│  │  • MarketContextAnalyzer (src/market_context_analyzer.py) │ │
│  │  • DataQualityMonitor (src/data_quality_monitor.py)   │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  Decision Layer                         │    │
│  │                                                        │    │
│  │  • RecommendationEngine (src/recommendation_engine.py) │    │
│  │  • RiskManager (src/risk_manager.py)                  │    │
│  │  • NoTradeDetector (src/no_trade_detector.py)         │    │
│  │  • ReversalWatchDetector (src/reversal_watch_detector.py) │ │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                    Data Layer                           │    │
│  │                                                        │    │
│  │  • DataProvider (src/data_provider.py)                │    │
│  │  • SymbolLookup (src/symbol_lookup.py)                │    │
│  │  • Configuration (src/config.py)                      │    │
│  │  • Models (src/models.py)                             │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  External APIs                          │    │
│  │                                                        │    │
│  │  • Yahoo Finance                                       │    │
│  │  • Finnhub                                             │    │
│  │  • NewsAPI                                             │    │
│  │  • Alpha Vantage                                       │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Options Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    Deployment Options                            │
└─────────────────────────────────────────────────────────────────┘

Option 1: Local Development
┌──────────────────────────┐
│  Your Computer           │
│  • Free                  │
│  • 25-30s response       │
│  • Manual start/stop     │
│  • No public access      │
└──────────────────────────┘

Option 2: Docker Local
┌──────────────────────────┐
│  Your Computer + Docker  │
│  • Free                  │
│  • 25-30s response       │
│  • Containerized         │
│  • No public access      │
└──────────────────────────┘

Option 3: AWS Lightsail (RECOMMENDED)
┌──────────────────────────┐
│  AWS Cloud Instance      │
│  • $10/month             │
│  • 25-30s response       │
│  • Always available      │
│  • Public access         │
│  • No cold starts        │
└──────────────────────────┘

Option 4: AWS Lambda
┌──────────────────────────┐
│  AWS Serverless          │
│  • $2-20/month           │
│  • 40-50s response       │
│  • Auto-scaling          │
│  • Cold starts (5-15s)   │
└──────────────────────────┘

Option 5: Streamlit Cloud
┌──────────────────────────┐
│  Streamlit Hosting       │
│  • Free                  │
│  • 30-40s response       │
│  • Public access         │
│  • Security concerns     │
└──────────────────────────┘
```

## Resource Usage

```
┌─────────────────────────────────────────────────────────────────┐
│                    Resource Utilization                          │
│                                                                  │
│  CPU Usage:                                                      │
│  ├─ Idle:           5-10%                                        │
│  ├─ Analysis:       60-80%                                       │
│  └─ Peak:           90-100% (brief)                              │
│                                                                  │
│  Memory Usage:                                                   │
│  ├─ Base:           800 MB                                       │
│  ├─ Analysis:       1.2-1.5 GB                                   │
│  └─ Peak:           1.8 GB                                       │
│                                                                  │
│  Disk Usage:                                                     │
│  ├─ Application:    1.5 GB                                       │
│  ├─ Docker Images:  500 MB                                       │
│  ├─ Data/Cache:     100 MB                                       │
│  └─ Total:          ~2 GB                                        │
│                                                                  │
│  Network Usage:                                                  │
│  ├─ Per Analysis:   5-10 MB                                      │
│  ├─ Daily (10 analyses): 50-100 MB                               │
│  └─ Monthly:        1.5-3 GB                                     │
│                                                                  │
│  Performance:                                                    │
│  ├─ Cold Start:     N/A (always-on)                              │
│  ├─ First Analysis: 30-35s (model loading)                       │
│  ├─ Cached:         25-30s                                       │
│  └─ Concurrent:     1 user (single instance)                     │
└─────────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                             │
│                                                                  │
│  Layer 1: AWS Lightsail Firewall                                │
│  ├─ Port 22 (SSH): Key-based authentication only                │
│  ├─ Port 8501 (HTTP): Public access                             │
│  └─ All other ports: Blocked                                     │
│                                                                  │
│  Layer 2: Docker Container Isolation                             │
│  ├─ Isolated network namespace                                   │
│  ├─ Limited host access                                          │
│  └─ Resource limits (CPU, memory)                                │
│                                                                  │
│  Layer 3: Environment Variables                                  │
│  ├─ API keys stored in .env file                                 │
│  ├─ Not committed to git                                         │
│  ├─ File permissions: 600 (owner only)                           │
│  └─ Loaded at container runtime                                  │
│                                                                  │
│  Layer 4: Application Security                                   │
│  ├─ No user authentication (single user)                         │
│  ├─ No data persistence (stateless)                              │
│  ├─ Input validation (symbol lookup)                             │
│  └─ API rate limiting (external)                                 │
│                                                                  │
│  Optional Enhancements:                                          │
│  ├─ HTTPS with SSL certificate                                   │
│  ├─ Nginx reverse proxy                                          │
│  ├─ Basic authentication                                         │
│  └─ IP whitelisting                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Scaling Considerations

```
Current Setup (Single Instance):
┌──────────────────────────┐
│  Lightsail $10/month     │
│  • 1 concurrent user     │
│  • 25-30s per analysis   │
│  • ~100 analyses/day     │
└──────────────────────────┘

Future Scaling Options:

Option 1: Vertical Scaling
┌──────────────────────────┐
│  Lightsail $20/month     │
│  • 4 GB RAM              │
│  • 2 vCPU                │
│  • 2-3 concurrent users  │
│  • Faster analysis       │
└──────────────────────────┘

Option 2: Horizontal Scaling
┌──────────────────────────┐
│  Multiple Instances      │
│  • Load balancer         │
│  • 5+ concurrent users   │
│  • High availability     │
│  • $50-100/month         │
└──────────────────────────┘

Option 3: Serverless
┌──────────────────────────┐
│  AWS Lambda + API GW     │
│  • Auto-scaling          │
│  • Pay per use           │
│  • Cold starts           │
│  • $20-50/month          │
└──────────────────────────┘
```

---

## Summary

The deployment architecture provides:

- ✅ **Simple**: Single Docker container on Lightsail
- ✅ **Fast**: 25-30 second response, no cold starts
- ✅ **Reliable**: Always-on availability
- ✅ **Secure**: Multi-layer security
- ✅ **Cost-effective**: $10/month
- ✅ **Scalable**: Easy to upgrade or scale out

Perfect for personal use with room to grow!
