# Design Document: News-Driven Stock Discovery

## Overview

The News-Driven Stock Discovery feature transforms the stock scanning system from analyzing a hardcoded list of stocks to dynamically discovering stocks mentioned in recent market news. The system fetches news from multiple providers (NewsAPI, Yahoo Finance, Finnhub), extracts stock symbols and company names using natural language processing, validates and deduplicates the discovered symbols, and analyzes them using the existing analysis pipeline to generate actionable trading recommendations.

This design leverages the existing `data_provider.py`, `symbol_lookup.py`, and `agent_core.py` components while introducing a new `news_discovery.py` module to orchestrate the news-to-symbols workflow.

## Architecture

### High-Level Flow

```
┌─────────────────┐
│  User Triggers  │
│  Scan Command   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     News Discovery Orchestrator         │
│  (news_discovery.py)                    │
└────────┬────────────────────────────────┘
         │
         ├──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
┌──────────────────┐            ┌──────────────────┐
│  News Fetcher    │            │ Symbol Extractor │
│  (fetch from     │───────────▶│  (parse articles │
│   NewsAPI,       │            │   extract symbols│
│   Yahoo, Finnhub)│            │   & companies)   │
└──────────────────┘            └────────┬─────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │ Symbol Validator     │
                              │ (dedupe, validate,   │
                              │  prioritize)         │
                              └────────┬─────────────┘
                                       │
                                       ▼
                              ┌──────────────────────┐
                              │  Stock Analyzer      │
                              │  (existing pipeline: │
                              │   sentiment, tech,   │
                              │   fundamental)       │
                              └────────┬─────────────┘
                                       │
                                       ▼
                              ┌──────────────────────┐
                              │ Recommendation Filter│
                              │ (BUY/SELL only,      │
                              │  sort by confidence) │
                              └────────┬─────────────┘
                                       │
                                       ▼
                              ┌──────────────────────┐
                              │  Display Results     │
                              │  (CLI or Web UI)     │
                              └──────────────────────┘
```

### Component Responsibilities

**News Discovery Orchestrator** (`news_discovery.py`)
- Coordinates the entire news-to-recommendations workflow
- Manages error handling and fallback logic
- Provides progress updates to the UI layer

**News Fetcher**
- Queries multiple news providers (NewsAPI, Yahoo Finance, Finnhub)
- Handles API rate limits and errors gracefully
- Returns unified news article format

**Symbol Extractor**
- Parses article text using regex and NLP techniques
- Identifies explicit ticker symbols (1-5 uppercase letters)
- Maps company names to symbols using `symbol_lookup.py`
- Tracks mention counts per symbol

**Symbol Validator**
- Deduplicates discovered symbols
- Validates symbols against the symbol lookup registry
- Prioritizes symbols by mention count and source diversity
- Limits to top N symbols (default 50) for performance

**Stock Analyzer**
- Reuses existing `agent_core.analyze_stock()` method
- No changes to existing analysis pipeline

**Recommendation Filter**
- Filters for BUY/SELL recommendations only
- Sorts by confidence score and mention count
- Formats results for display

## Components and Interfaces

### NewsDiscovery Class

```python
class NewsDiscovery:
    """Orchestrates news-driven stock discovery."""
    
    def __init__(self, data_provider: DataProvider, 
                 symbol_lookup: SymbolLookup,
                 max_symbols: int = 50):
        """
        Initialize news discovery system.
        
        Args:
            data_provider: Provider for fetching news
            symbol_lookup: Symbol lookup service
            max_symbols: Maximum symbols to analyze
        """
        
    def discover_stocks(self, hours_back: int = 24) -> List[DiscoveredStock]:
        """
        Discover stocks from recent news.
        
        Args:
            hours_back: How many hours of news to fetch
            
        Returns:
            List of discovered stocks with metadata
        """
        
    def _fetch_news(self, hours_back: int) -> List[NewsArticle]:
        """Fetch news from all providers."""
        
    def _extract_symbols(self, articles: List[NewsArticle]) -> Dict[str, SymbolMention]:
        """Extract and count symbol mentions."""
        
    def _validate_and_prioritize(self, mentions: Dict[str, SymbolMention]) -> List[str]:
        """Validate, deduplicate, and prioritize symbols."""
```

### SymbolExtractor Class

```python
class SymbolExtractor:
    """Extracts stock symbols from news text."""
    
    def __init__(self, symbol_lookup: SymbolLookup):
        """Initialize with symbol lookup service."""
        
    def extract_from_text(self, text: str) -> Set[str]:
        """
        Extract symbols from text.
        
        Args:
            text: Article title or content
            
        Returns:
            Set of discovered symbols
        """
        
    def _find_ticker_symbols(self, text: str) -> Set[str]:
        """Find explicit ticker symbols using regex."""
        
    def _find_company_names(self, text: str) -> Set[str]:
        """Find company names and map to symbols."""
```

### Data Models

```python
@dataclass
class NewsArticle:
    """Represents a news article."""
    title: str
    description: str
    source: str
    published_at: datetime
    url: str

@dataclass
class SymbolMention:
    """Tracks symbol mentions across articles."""
    symbol: str
    mention_count: int
    sources: Set[str]  # Which news providers mentioned it
    articles: List[NewsArticle]

@dataclass
class DiscoveredStock:
    """Represents a discovered stock with metadata."""
    symbol: str
    mention_count: int
    sources: List[str]
    sample_articles: List[NewsArticle]  # Up to 3 articles
```

### Integration Points

**CLI Integration** (`cli.py`)
```python
@click.command()
@click.option('--symbols', multiple=True, help='Specific symbols to scan')
def scan(symbols):
    """Scan stocks for trading opportunities."""
    if symbols:
        # Use provided symbols (backward compatibility)
        results = scan_specific_symbols(symbols)
    else:
        # Use news-driven discovery (new default)
        discovery = NewsDiscovery(data_provider, symbol_lookup)
        discovered = discovery.discover_stocks()
        results = analyze_discovered_stocks(discovered)
    
    display_results(results)
```

**Web UI Integration** (`web_ui.py`)
```python
@app.route('/scan', methods=['POST'])
def scan_stocks_page():
    """Handle stock scanning via web UI."""
    discovery = NewsDiscovery(data_provider, symbol_lookup)
    discovered = discovery.discover_stocks()
    
    # Show discovered symbols to user
    render_template('scan_progress.html', discovered=discovered)
    
    # Analyze stocks
    results = analyze_discovered_stocks(discovered)
    
    return render_template('scan_results.html', results=results)
```

## Data Models

### Symbol Extraction Pattern

The system uses a two-phase approach for symbol extraction:

**Phase 1: Explicit Ticker Symbols**
- Regex pattern: `\b[A-Z]{1,5}\b` (1-5 uppercase letters as word boundaries)
- Filters out common English words (THE, AND, OR, etc.)
- Validates against symbol lookup registry

**Phase 2: Company Name Mapping**
- Searches for known company names from symbol lookup
- Uses case-insensitive matching
- Handles variations (e.g., "Apple" vs "Apple Inc.")

### News Article Aggregation

Articles are fetched from three providers with the following structure:

```python
# NewsAPI format
{
    "title": "Apple announces new product",
    "description": "Apple Inc. revealed...",
    "source": {"name": "TechCrunch"},
    "publishedAt": "2025-01-15T10:30:00Z",
    "url": "https://..."
}

# Yahoo Finance format (via data_provider)
{
    "title": "...",
    "summary": "...",
    "publisher": "...",
    "providerPublishTime": 1705318200,
    "link": "..."
}

# Finnhub format (via data_provider)
{
    "headline": "...",
    "summary": "...",
    "source": "...",
    "datetime": 1705318200,
    "url": "..."
}
```

The system normalizes these into a unified `NewsArticle` format.

### Symbol Prioritization Algorithm

Symbols are prioritized using a weighted score:

```
score = (mention_count * 2) + (unique_sources * 3)
```

This favors symbols mentioned across multiple sources over those with many mentions from a single source.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: News Time Range Accuracy

*For any* execution of the discover_stocks method with a specified hours_back parameter, the system should query news providers for articles published within that time range from the current time.

**Validates: Requirements 1.1**

### Property 2: Multi-Provider Query

*For any* news discovery execution, the system should attempt to query all three news providers (NewsAPI, Yahoo Finance, Finnhub) regardless of individual provider success or failure.

**Validates: Requirements 1.2**

### Property 3: Provider Failure Resilience

*For any* combination of provider failures (one or more providers unavailable), the system should continue execution and return results from the remaining successful providers without throwing exceptions.

**Validates: Requirements 1.3, 9.1**

### Property 4: Comprehensive Text Extraction

*For any* news article, the symbol extraction process should parse both the title and description fields, ensuring no symbols are missed due to only checking one field.

**Validates: Requirements 2.1, 2.5**

### Property 5: Ticker Symbol Pattern Recognition

*For any* text containing uppercase letter sequences of 1-5 characters surrounded by word boundaries, the extractor should identify all valid ticker symbols while excluding common English words.

**Validates: Requirements 2.2**

### Property 6: Company Name to Symbol Mapping

*For any* text containing known company names from the symbol lookup registry, the extractor should correctly map each company name to its corresponding stock symbol.

**Validates: Requirements 2.3, 2.4**

### Property 7: Symbol Deduplication

*For any* list of extracted symbols containing duplicates, the validation process should produce a deduplicated list where each symbol appears exactly once.

**Validates: Requirements 3.1**

### Property 8: Symbol Validation Filter

*For any* list of extracted symbols containing both valid and invalid symbols, the validation process should exclude all symbols not present in the symbol lookup registry.

**Validates: Requirements 3.2, 3.5**

### Property 9: Mention Count Accuracy

*For any* symbol appearing in multiple articles, the system should accurately count the total number of mentions across all articles and sources.

**Validates: Requirements 3.3**

### Property 10: Mention-Based Prioritization

*For any* set of discovered symbols with different mention counts, the prioritization algorithm should order symbols in descending order by their weighted score (mention_count * 2 + unique_sources * 3).

**Validates: Requirements 3.4**

### Property 11: Analysis Pipeline Integration

*For any* list of validated symbols, the system should call the existing analyze_stock method exactly once for each symbol in the list.

**Validates: Requirements 4.1**

### Property 12: Actionable Recommendation Filtering

*For any* set of analysis results containing mixed recommendation types (BUY, SELL, HOLD), the filtering process should return only results with BUY or SELL recommendations, excluding all HOLD recommendations.

**Validates: Requirements 5.1, 5.2**

### Property 13: Confidence-Based Sorting

*For any* set of filtered recommendations with different confidence scores, the results should be sorted in descending order by confidence score.

**Validates: Requirements 5.3**

### Property 14: Multi-Criteria Result Sorting

*For any* set of recommendations with both confidence scores and mention counts, the final results should be sorted first by confidence score (descending), then by mention count (descending) as a tiebreaker.

**Validates: Requirements 5.5**

### Property 15: Symbol Limit Enforcement

*For any* discovery execution that finds more than max_symbols unique symbols, the system should analyze only the top max_symbols symbols by priority score, discarding the rest.

**Validates: Requirements 6.1**

### Property 16: CLI Output Completeness

*For any* scan result displayed in the CLI, the output should include all required fields: symbol, recommendation type, confidence score, and mention count.

**Validates: Requirements 7.4**

### Property 17: Summary Count Accuracy

*For any* completed scan, the summary counts for total stocks discovered and total stocks analyzed should exactly match the actual number of unique symbols discovered and the number of symbols that completed analysis.

**Validates: Requirements 7.5**

### Property 18: Extraction Error Resilience

*For any* batch of articles where some articles cause extraction errors, the system should successfully extract symbols from all non-failing articles and continue execution without throwing exceptions.

**Validates: Requirements 9.2**

### Property 19: Analysis Error Resilience

*For any* list of symbols where some symbols cause analysis failures, the system should successfully analyze all non-failing symbols and return results for those symbols without throwing exceptions.

**Validates: Requirements 9.3**

## Error Handling

### News Provider Failures

The system implements a fail-safe approach where provider failures are logged but don't halt execution:

```python
def _fetch_news(self, hours_back: int) -> List[NewsArticle]:
    """Fetch news from all providers with error handling."""
    all_articles = []
    
    for provider_name, fetch_func in self.providers.items():
        try:
            articles = fetch_func(hours_back)
            all_articles.extend(articles)
            logger.info(f"Fetched {len(articles)} articles from {provider_name}")
        except RateLimitError as e:
            logger.warning(f"{provider_name} rate limit reached, skipping")
        except Exception as e:
            logger.error(f"Failed to fetch from {provider_name}: {e}")
            continue
    
    if not all_articles:
        raise NoNewsAvailableError("All news providers failed")
    
    return all_articles
```

### Symbol Extraction Failures

Individual article extraction failures are isolated:

```python
def _extract_symbols(self, articles: List[NewsArticle]) -> Dict[str, SymbolMention]:
    """Extract symbols with per-article error handling."""
    mentions = {}
    
    for article in articles:
        try:
            symbols = self.extractor.extract_from_text(
                f"{article.title} {article.description}"
            )
            for symbol in symbols:
                # Track mention...
        except Exception as e:
            logger.warning(f"Failed to extract from article: {e}")
            continue
    
    return mentions
```

### Stock Analysis Failures

Analysis failures for individual stocks don't prevent other stocks from being analyzed:

```python
def analyze_discovered_stocks(discovered: List[DiscoveredStock]) -> List[AnalysisResult]:
    """Analyze stocks with per-stock error handling."""
    results = []
    
    for stock in discovered:
        try:
            result = agent_core.analyze_stock(stock.symbol)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to analyze {stock.symbol}: {e}")
            continue
    
    return results
```

### Common Error Scenarios

**Scenario 1: All News Providers Fail**
- System raises `NoNewsAvailableError`
- CLI/Web UI displays error message
- Suggests checking API keys and network connectivity

**Scenario 2: No Valid Symbols Extracted**
- System returns empty list
- CLI/Web UI displays "No stocks discovered in recent news"
- Suggests trying again later or checking news sources

**Scenario 3: No Actionable Recommendations**
- System returns empty results after filtering
- CLI/Web UI displays "No BUY/SELL opportunities found"
- Shows count of stocks analyzed with HOLD recommendations

**Scenario 4: Rate Limit Exceeded**
- System logs warning and continues with other providers
- Results may have fewer articles but still functional
- User is informed which providers were skipped

## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific examples and edge cases with property-based tests for universal correctness properties. This ensures both concrete behavior validation and comprehensive input coverage.

### Unit Testing Focus

Unit tests should cover:

**Specific Examples:**
- Parsing a known news article with "Apple" and "AAPL" returns symbol "AAPL"
- Extracting "TSLA" from "Tesla (TSLA) stock rises 5%"
- Validating that "XYZ123" is rejected as invalid symbol

**Edge Cases:**
- Empty news article list returns empty symbol list
- Article with no recognizable symbols returns empty set
- Symbol mentioned in title but not description is still extracted
- All providers fail scenario triggers appropriate error

**Integration Points:**
- CLI scan command with no arguments triggers news discovery
- CLI scan command with explicit symbols bypasses news discovery
- Web UI scan button triggers news discovery workflow
- Existing analyze and recommend commands remain functional

**Error Conditions:**
- NewsAPI rate limit error is caught and logged
- Invalid JSON from provider is handled gracefully
- Network timeout doesn't crash the system
- Malformed article data is skipped

### Property-Based Testing Focus

Property tests should verify universal correctness properties across randomized inputs. Each property test should:
- Run minimum 100 iterations
- Use a property-based testing library (e.g., Hypothesis for Python)
- Reference the design document property in a comment tag

**Property Test Configuration:**

```python
from hypothesis import given, strategies as st
import pytest

@given(st.lists(st.text(min_size=1, max_size=100)))
def test_property_7_deduplication(symbol_lists):
    """
    Feature: news-driven-stock-discovery, Property 7: Symbol Deduplication
    
    For any list of extracted symbols containing duplicates,
    the validation process should produce a deduplicated list
    where each symbol appears exactly once.
    """
    # Test implementation...
```

**Key Properties to Test:**
- Property 1: Time range accuracy (generate random hours_back values)
- Property 4: Text extraction completeness (generate random articles)
- Property 5: Ticker pattern recognition (generate text with embedded symbols)
- Property 7: Deduplication (generate lists with random duplicates)
- Property 8: Validation filtering (generate mixed valid/invalid symbols)
- Property 9: Mention count accuracy (generate articles with repeated symbols)
- Property 10: Prioritization ordering (generate symbols with random mention counts)
- Property 12: Recommendation filtering (generate mixed recommendation types)
- Property 15: Symbol limit enforcement (generate more symbols than limit)

### Test Data Generation

**For Property Tests:**
- Use Hypothesis strategies to generate random but valid inputs
- Generate realistic news article structures
- Create symbol lists with controlled characteristics (duplicates, invalid symbols)
- Generate recommendation results with varying confidence scores

**For Unit Tests:**
- Use real examples from actual news articles
- Include edge cases discovered during development
- Test with actual API response formats from each provider

### Testing Backward Compatibility

Ensure existing functionality remains intact:

```python
def test_analyze_command_unchanged():
    """Verify analyze command still works as before."""
    result = cli_runner.invoke(cli, ['analyze', 'AAPL'])
    assert result.exit_code == 0
    assert 'AAPL' in result.output

def test_recommend_command_unchanged():
    """Verify recommend command still works as before."""
    result = cli_runner.invoke(cli, ['recommend', 'AAPL'])
    assert result.exit_code == 0
    assert 'recommendation' in result.output.lower()

def test_scan_with_explicit_symbols():
    """Verify scan command with symbols bypasses news discovery."""
    result = cli_runner.invoke(cli, ['scan', '--symbols', 'AAPL', 'GOOGL'])
    assert result.exit_code == 0
    # Should not fetch news, should analyze provided symbols
```

### Performance Testing

While not part of automated unit/property tests, manual performance testing should verify:
- Scan completes within 5 minutes for typical use cases (20-30 discovered stocks)
- Memory usage remains reasonable with 50+ articles
- API rate limits are respected
- Progress updates appear at reasonable intervals

### Test Organization

```
tests/
├── test_news_discovery.py          # NewsDiscovery class tests
├── test_symbol_extractor.py        # SymbolExtractor class tests
├── test_cli_integration.py         # CLI integration tests
├── test_web_ui_integration.py      # Web UI integration tests
├── test_backward_compatibility.py  # Existing functionality tests
└── property_tests/
    ├── test_extraction_properties.py
    ├── test_validation_properties.py
    ├── test_filtering_properties.py
    └── test_error_handling_properties.py
```
