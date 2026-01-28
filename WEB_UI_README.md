# Stock Market AI Agent - Web UI

An interactive web interface for the Stock Market AI Agent, built with Streamlit.

## Features

### 📊 Stock Analysis
- **Comprehensive Analysis**: Get detailed insights on any stock with a single click
- **Interactive Charts**: Visualize price history with candlestick charts and volume
- **Real-time Data**: Fetch current prices, news, and market sentiment
- **Plain English Summaries**: Understand recommendations without financial jargon
- **Multi-currency Support**: Automatic currency detection (₹ for Indian stocks, $ for US stocks)

### 🔍 Stock Scanner
- **Automated Scanning**: Scan 38+ popular stocks across different sectors
- **Smart Filtering**: Find BUY opportunities based on confidence threshold
- **Customizable Results**: Adjust minimum confidence and result limits
- **Quick Overview**: See all key metrics at a glance

### 📈 Visual Analytics
- **Candlestick Charts**: Interactive price history with zoom and pan
- **Volume Analysis**: Track trading volume alongside price movements
- **Technical Indicators**: Visual representation of RSI, MACD, and moving averages
- **Color-coded Metrics**: Easy-to-understand green/yellow/red indicators

## Quick Start

### Option 1: Using the launcher script (Recommended)
```bash
./run_web_ui.sh
```

### Option 2: Direct Streamlit command
```bash
streamlit run src/web_ui.py
```

The web UI will automatically open in your default browser at `http://localhost:8501`

## Usage Guide

### Analyzing a Stock

1. Navigate to **📊 Stock Analysis** page (default)
2. Enter a stock symbol in the text input:
   - US stocks: `AAPL`, `TSLA`, `MSFT`
   - Indian stocks: `HDFCBANK.NS`, `RELIANCE.NS`, `TCS.NS`
3. Click **🔍 Analyze** button
4. View comprehensive analysis including:
   - Current price and volume
   - BUY/SELL/HOLD recommendation with confidence
   - Sentiment, technical, and fundamental scores
   - Interactive price chart
   - Recent news articles

### Scanning for Opportunities

1. Navigate to **🔍 Stock Scanner** page
2. Adjust settings:
   - **Minimum Confidence**: Set threshold (default: 60%)
   - **Max Results**: Number of stocks to display (default: 5)
3. Click **🚀 Start Scan** button
4. Wait for the scan to complete (progress bar shows status)
5. Review BUY opportunities sorted by confidence

## Configuration

The web UI uses the same configuration as the CLI:

- **Environment Variables**: Set in `.env` file
  - `FINNHUB_API_KEY`: Your Finnhub API key
  - `NEWS_API_KEY`: Your NewsAPI key

- **Config File**: Create `config.json` for custom settings

## Features Comparison

| Feature | CLI | Web UI |
|---------|-----|--------|
| Stock Analysis | ✅ | ✅ |
| Stock Scanner | ✅ | ✅ |
| Sentiment Analysis | ✅ | ✅ |
| Portfolio Risk | ✅ | ⏳ Coming Soon |
| Interactive Charts | ❌ | ✅ |
| Real-time Updates | ❌ | ✅ |
| Multi-tab Interface | ❌ | ✅ |
| Export Results | ❌ | ⏳ Coming Soon |

## Tips

### Performance
- First analysis may take 10-15 seconds (fetching data)
- Subsequent analyses are faster due to caching
- Scanner takes 2-3 minutes to analyze all stocks

### Best Practices
- Use specific stock symbols (e.g., `AAPL` not `Apple`)
- For Indian stocks, always add `.NS` (NSE) or `.BO` (BSE) suffix
- Check the disclaimer before making investment decisions
- Combine multiple analysis methods for better insights

### Troubleshooting

**Issue**: "Invalid symbol" error
- **Solution**: Verify the stock symbol is correct and includes exchange suffix for non-US stocks

**Issue**: Slow loading
- **Solution**: First load fetches data from APIs. Subsequent loads use cache.

**Issue**: No news articles
- **Solution**: Check your API keys in `.env` file. Yahoo Finance works without API key.

**Issue**: Charts not displaying
- **Solution**: Ensure Plotly is installed: `pip install plotly`

## Keyboard Shortcuts

- `Ctrl/Cmd + R`: Refresh the page
- `Ctrl/Cmd + K`: Focus on search/input field
- `Esc`: Close modals and expanders

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Chromium (Recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

## Advanced Usage

### Custom Watchlist for Scanner

Edit `src/web_ui.py` and modify the `watchlist` array in `scan_stocks_page()`:

```python
watchlist = [
    "AAPL", "MSFT", "GOOGL",  # Your custom symbols
    "HDFCBANK.NS", "RELIANCE.NS"  # Indian stocks
]
```

### Changing Default Settings

Modify the default values in the UI components:

```python
# In scan_stocks_page()
min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.7, 0.05)  # Change 0.6 to 0.7
limit = st.number_input("Max Results", 1, 20, 10)  # Change 5 to 10
```

## Screenshots

### Stock Analysis Page
- Clean, professional interface
- Color-coded recommendations (Green=BUY, Yellow=HOLD, Red=SELL)
- Interactive charts with zoom and pan
- Expandable sections for detailed information

### Stock Scanner Page
- Progress bar showing scan status
- Results sorted by confidence
- Quick overview of all key metrics
- One-click access to detailed analysis

## Support

For issues or questions:
1. Check the main README.md
2. Review the CLI documentation
3. Verify your API keys are configured correctly

## License

Same as the main project - Educational purposes only. Not financial advice.
