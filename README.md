# Stock Market AI Agent

A comprehensive personal trading assistant that analyzes financial markets using sentiment analysis, technical indicators, and fundamental data to provide actionable trading recommendations. Available as both a command-line interface (CLI) and an interactive web application.

## Features

### Core Analysis
- **Sentiment Analysis**: Analyzes news articles from multiple sources (Yahoo Finance, Finnhub, NewsAPI) using FinBERT
- **Technical Analysis**: Calculates moving averages, RSI, MACD, and identifies support/resistance levels
- **Fundamental Analysis**: Evaluates company financials (P/E, P/B, Debt/Equity, Revenue Growth)
- **Risk Management**: Assesses portfolio risk and suggests position sizing
- **Multi-currency Support**: Automatic currency detection (₹ for Indian stocks, $ for US stocks)
- **Smart Symbol Lookup**: Use company names instead of ticker symbols (e.g., "Apple" → AAPL, "HDFC Bank" → HDFCBANK.NS)

### Interfaces
- **Command-Line Interface (CLI)**: Fast, scriptable interface with rich formatting
- **Web UI**: Interactive Streamlit-based web application with charts and visualizations
- **Stock Scanner**: Automatically scan popular stocks for BUY opportunities

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Setup

1. Clone the repository and navigate to the project directory

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Configure your API keys in the `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

### Manual Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the example environment file and configure your API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

## Configuration

### API Keys (Optional but Recommended)

Add these to your `.env` file for enhanced functionality:

- **Finnhub API**: Get your free key at https://finnhub.io/
  - Provides company news for US stocks
  - Free tier: 60 API calls/minute
  
- **NewsAPI**: Get your free key at https://newsapi.org/
  - Provides comprehensive news coverage
  - Free tier: 100 requests/day

**Note**: Yahoo Finance works without any API key and provides basic news coverage.

### Configuration File

Create a `config.json` file for custom settings:

```json
{
  "risk_tolerance": "moderate",
  "sentiment_weight": 0.5,
  "technical_weight": 0.3,
  "fundamental_weight": 0.2,
  "cache_ttl_seconds": 300
}
```

## Usage

### Command-Line Interface (CLI)

The CLI provides fast, scriptable access to all features:

#### Analyze a Stock
```bash
# Use ticker symbols
./stock-agent analyze AAPL

# Or use company names
./stock-agent analyze "apple"
./stock-agent analyze "idfc first bank"
./stock-agent analyze "tesla"

# Indian stocks work with names too
./stock-agent analyze HDFCBANK.NS  # Symbol
./stock-agent analyze "hdfc bank"  # Company name
```

#### Get Trading Recommendation
```bash
./stock-agent recommend TSLA
```

#### View Sentiment Analysis
```bash
./stock-agent sentiment MSFT
```

#### Scan for BUY Opportunities
```bash
./stock-agent scan
./stock-agent scan --min-confidence 0.7 --limit 10
```

#### Assess Portfolio Risk
```bash
./stock-agent portfolio --config my_config.json
```

### Web UI (Interactive Interface)

Launch the web application for an interactive experience:

```bash
./run_web_ui.sh
```

Or directly:
```bash
streamlit run src/web_ui.py
```

The web UI will open automatically at `http://localhost:8501`

#### Authentication

The web UI includes built-in authentication to protect your application.

**Default Credentials** (change in production):
- Username: `admin`
- Password: `changeme`

**Configure Authentication**:
```bash
# Edit .env file
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_secure_password

# Or use password hash (more secure)
python src/auth.py "your_password"
# Copy hash to .env as AUTH_PASSWORD_HASH
```

See [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) for complete authentication setup.

#### Web UI Features
- 📊 **Stock Analysis**: Comprehensive analysis with interactive charts
- 🔍 **Stock Scanner**: Automated scanning of popular stocks
- 📈 **Interactive Charts**: Candlestick charts with volume analysis
- 💡 **Plain English Summaries**: Easy-to-understand recommendations
- 🎨 **Color-coded Metrics**: Visual indicators for quick insights

See [WEB_UI_README.md](WEB_UI_README.md) for detailed web UI documentation.

## Supported Stock Exchanges

### US Stocks
Use the standard ticker symbol:
- `AAPL` - Apple Inc.
- `TSLA` - Tesla Inc.
- `MSFT` - Microsoft Corporation

### Indian Stocks
Add exchange suffix:
- `.NS` for NSE (National Stock Exchange): `HDFCBANK.NS`, `RELIANCE.NS`
- `.BO` for BSE (Bombay Stock Exchange): `HDFCBANK.BO`, `RELIANCE.BO`

## Project Structure

```
.
├── src/                          # Source code
│   ├── __init__.py
│   ├── agent_core.py            # Main agent orchestration
│   ├── cli.py                   # Command-line interface
│   ├── web_ui.py                # Web interface (Streamlit)
│   ├── config.py                # Configuration management
│   ├── data_provider.py         # Data fetching from APIs
│   ├── models.py                # Data models
│   ├── sentiment_analyzer.py   # Sentiment analysis
│   ├── technical_analyzer.py   # Technical indicators
│   ├── fundamental_analyzer.py # Fundamental metrics
│   ├── recommendation_engine.py # Trading recommendations
│   └── risk_manager.py          # Risk assessment
├── tests/                       # Unit tests (115 tests)
│   ├── test_agent_core.py
│   ├── test_sentiment_analyzer.py
│   ├── test_technical_analyzer.py
│   ├── test_fundamental_analyzer.py
│   ├── test_recommendation_engine.py
│   └── test_risk_manager.py
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── stock-agent                  # CLI executable
├── run_web_ui.sh               # Web UI launcher
├── setup.sh                     # Setup script
├── README.md                    # This file
└── WEB_UI_README.md            # Web UI documentation
```

## Examples

### CLI Examples

**Analyze Apple stock:**
```bash
$ ./stock-agent analyze AAPL

Analyzing AAPL...

💰 Current Price
Price:    $150.25 USD
Volume:   52,847,392

📊 Sentiment Analysis
Score:        +0.45
Confidence:   85.00%
Sources:      127

📈 Technical Analysis
Technical Score:        +0.32
RSI:                    58.23 🟡 Neutral
MACD:                   +2.15 🟢 Bullish

🎯 Recommendation
Action:       BUY
Confidence:   78.00%
```

**Scan for opportunities:**
```bash
$ ./stock-agent scan --min-confidence 0.7

Scanning 38 popular stocks for BUY opportunities...

✅ Found 5 BUY opportunities!

NVDA - BUY (89% confidence)
MSFT - BUY (82% confidence)
AAPL - BUY (78% confidence)
```

### Web UI Examples

1. **Stock Analysis**: Enter `AAPL` → Click "Analyze" → View comprehensive report
2. **Stock Scanner**: Click "Start Scan" → Wait for results → Review BUY opportunities
3. **Interactive Charts**: Zoom, pan, and explore price history
4. **News Analysis**: Expand "Recent News" to see sentiment-scored articles

## Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

All 115 unit tests pass successfully.

## Performance

- **First Analysis**: 10-15 seconds (fetching data from APIs)
- **Cached Analysis**: 1-2 seconds (using cached data)
- **Stock Scanner**: 2-3 minutes for 38 stocks
- **Cache Duration**: 5 minutes (configurable)

## Troubleshooting

### "Invalid symbol" error
- Verify the stock symbol is correct
- For Indian stocks, add `.NS` or `.BO` suffix

### No news articles
- Check your API keys in `.env` file
- Yahoo Finance works without API key

### Slow performance
- First load fetches data from APIs
- Subsequent loads use cache (5 minutes)
- Check your internet connection

### Web UI not starting
- Ensure Streamlit is installed: `pip install streamlit`
- Check if port 8501 is available
- Try: `streamlit run src/web_ui.py --server.port 8502`

## Disclaimers

⚠️ **IMPORTANT DISCLAIMER**

This Stock Market AI Agent is provided for **EDUCATIONAL and INFORMATIONAL PURPOSES ONLY**.

- This tool is **NOT financial advice**
- Past performance does **NOT** guarantee future results
- All investment decisions carry **RISK**
- **Consult with qualified financial professionals** before making investment decisions
- The creators assume **NO LIABILITY** for financial losses

By using this tool, you acknowledge these limitations and agree to use it responsibly.

## License

This project is for personal and educational use only.

## Contributing

This is a personal project. Feel free to fork and modify for your own use.

## Deployment

### 🚀 Streamlit Community Cloud (Recommended - FREE!)

Deploy to Streamlit Cloud for **completely free** hosting with automatic HTTPS!

- **Cost**: FREE (no credit card required)
- **Performance**: 25-30 second analysis
- **Setup Time**: 2 minutes
- **URL**: Get your own `yourapp.streamlit.app` subdomain
- **Always-on**: No cold starts (sleeps after 7 days of inactivity)

**Quick Deploy:**
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `AjitHegde/stock-market-analysis-agent`
5. Main file: `src/web_ui.py`
6. Add your API keys in Settings → Secrets
7. Deploy! ✅

See [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md) for detailed instructions.

### Docker Deployment

The application is fully containerized and ready for deployment.

#### Quick Local Test with Docker

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 2. Build and run
docker-compose up -d --build

# 3. Access application
# Open http://localhost:8501
```

See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for detailed Docker instructions.

#### AWS Lightsail Deployment

Deploy to AWS Lightsail for fast, consistent performance:

- **Cost**: $10/month
- **Performance**: 25-30 second analysis (no cold starts)
- **Availability**: Always-on server
- **Setup Time**: 5-7 minutes (AWS CLI) or 15-20 minutes (Manual)

**Option 1: Automated AWS CLI Deployment (Fastest)**
```bash
# From your local machine
./deploy-aws-cli.sh
# Follow prompts, done in 5-7 minutes!
```

**Option 2: Manual Deployment**
```bash
# On your Lightsail instance
git clone <your-repo-url>
cd stock-market-ai-agent
cp .env.example .env
# Edit .env with your API keys
./deploy.sh
```

See [AWS_CLI_DEPLOYMENT.md](AWS_CLI_DEPLOYMENT.md) for AWS CLI guide or [LIGHTSAIL_DEPLOYMENT.md](LIGHTSAIL_DEPLOYMENT.md) for manual deployment.

### Deployment Options Comparison

| Option | Cost | Response Time | Setup Complexity | Best For |
|--------|------|---------------|------------------|----------|
| **Streamlit Cloud** | ✅ FREE | 25-30s | ⭐ Easiest | Public apps, demos, sharing |
| **Local** | Free | 25-30s | Easy | Development/Testing |
| **Docker Local** | Free | 25-30s | Easy | Testing Production Setup |
| **AWS Lightsail** | $10/mo | 25-30s | Medium | Private production use |
| **Render.com** | Free/$7/mo | 30-40s | Easy | Alternative to Streamlit |
| **Railway.app** | $5 credit | 25-30s | Easy | Quick deploys |

**Recommendation**: Use **Streamlit Cloud** for free public hosting, or **AWS Lightsail** if you need private deployment with full control.

## Acknowledgments

- **FinBERT**: Sentiment analysis model for financial text
- **yfinance**: Yahoo Finance data provider
- **Finnhub**: Financial data API
- **NewsAPI**: News aggregation service
- **Streamlit**: Web application framework
- **Rich**: Terminal formatting library

