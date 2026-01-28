# Requirements Document

## Introduction

This document specifies requirements for the News-Driven Stock Discovery feature, which replaces the hardcoded stock list with a dynamic discovery mechanism based on recent market news. The system will scan news articles from the last 24 hours, extract mentioned companies and stock symbols, and analyze those stocks using the existing analysis pipeline to provide actionable trading recommendations.

## Glossary

- **News_Discovery_System**: The component responsible for fetching and parsing news articles to extract stock symbols
- **Symbol_Extractor**: The component that identifies company names and ticker symbols from news text
- **Stock_Scanner**: The existing component that performs comprehensive stock analysis
- **News_Provider**: External APIs (NewsAPI, Yahoo Finance, Finnhub) that supply market news
- **Analysis_Pipeline**: The existing system that performs sentiment, technical, and fundamental analysis
- **Actionable_Recommendation**: A BUY or SELL recommendation with sufficient confidence for next-day trading

## Requirements

### Requirement 1: News Article Retrieval

**User Story:** As a trader, I want the system to fetch recent market news, so that I can discover stocks that are currently relevant in the market.

#### Acceptance Criteria

1. WHEN the scan command is executed, THE News_Discovery_System SHALL fetch general market news from the last 24 hours
2. THE News_Discovery_System SHALL query NewsAPI, Yahoo Finance, and Finnhub for market news
3. WHEN a News_Provider is unavailable or returns an error, THE News_Discovery_System SHALL continue with remaining providers
4. THE News_Discovery_System SHALL respect API rate limits for each News_Provider
5. WHEN NewsAPI rate limit is reached, THE News_Discovery_System SHALL skip NewsAPI and use remaining providers

### Requirement 2: Stock Symbol Extraction

**User Story:** As a trader, I want the system to identify stock symbols and company names from news articles, so that I know which stocks are being discussed in the market.

#### Acceptance Criteria

1. WHEN news articles are retrieved, THE Symbol_Extractor SHALL parse article titles and descriptions for stock symbols
2. THE Symbol_Extractor SHALL identify explicit ticker symbols in the format of 1-5 uppercase letters
3. THE Symbol_Extractor SHALL identify company names using the existing Symbol_Lookup component
4. WHEN a company name is found, THE Symbol_Extractor SHALL map it to its corresponding stock symbol
5. THE Symbol_Extractor SHALL extract symbols from both article titles and article content

### Requirement 3: Symbol Validation and Deduplication

**User Story:** As a trader, I want the system to validate and deduplicate discovered symbols, so that I only analyze legitimate stocks without redundancy.

#### Acceptance Criteria

1. WHEN symbols are extracted, THE News_Discovery_System SHALL remove duplicate symbols
2. THE News_Discovery_System SHALL validate that each symbol exists in the Symbol_Lookup registry
3. WHEN a symbol appears in multiple news articles, THE News_Discovery_System SHALL track the mention count
4. THE News_Discovery_System SHALL prioritize symbols with higher mention counts across different sources
5. WHEN invalid or unrecognized symbols are found, THE News_Discovery_System SHALL exclude them from analysis

### Requirement 4: Stock Analysis Integration

**User Story:** As a trader, I want discovered stocks to be analyzed using the existing analysis pipeline, so that I receive consistent and comprehensive recommendations.

#### Acceptance Criteria

1. WHEN symbols are validated, THE Stock_Scanner SHALL analyze each symbol using the existing analyze_stock method
2. THE Stock_Scanner SHALL perform sentiment analysis on each discovered stock
3. THE Stock_Scanner SHALL perform technical analysis on each discovered stock
4. THE Stock_Scanner SHALL perform fundamental analysis on each discovered stock
5. THE Stock_Scanner SHALL generate recommendations using the existing recommendation engine

### Requirement 5: Recommendation Filtering

**User Story:** As a trader, I want to see only actionable recommendations, so that I can focus on high-confidence trading opportunities.

#### Acceptance Criteria

1. WHEN analysis is complete, THE Stock_Scanner SHALL filter results to include only BUY or SELL recommendations
2. THE Stock_Scanner SHALL exclude HOLD recommendations from the final output
3. THE Stock_Scanner SHALL prioritize recommendations with higher confidence scores
4. WHEN no actionable recommendations are found, THE Stock_Scanner SHALL inform the user
5. THE Stock_Scanner SHALL sort results by recommendation confidence and news mention count

### Requirement 6: Performance and Scalability

**User Story:** As a trader, I want the scan to complete in a reasonable time, so that I can make timely trading decisions.

#### Acceptance Criteria

1. THE News_Discovery_System SHALL limit the number of stocks analyzed to prevent excessive scan times
2. WHEN more than 50 unique symbols are discovered, THE News_Discovery_System SHALL analyze only the top 50 by mention count
3. THE Stock_Scanner SHALL complete the entire scan process within 5 minutes for typical use cases
4. THE News_Discovery_System SHALL provide progress updates during the scan process
5. WHEN analysis takes longer than expected, THE News_Discovery_System SHALL allow user interruption

### Requirement 7: CLI Interface Integration

**User Story:** As a CLI user, I want to use the scan command with news-driven discovery, so that I can access the feature from the command line.

#### Acceptance Criteria

1. WHEN the scan command is executed without arguments, THE CLI SHALL use news-driven discovery by default
2. THE CLI SHALL display discovered symbols before starting analysis
3. THE CLI SHALL show progress indicators during news fetching and stock analysis
4. THE CLI SHALL display results in a formatted table with symbol, recommendation, confidence, and mention count
5. WHEN the scan completes, THE CLI SHALL provide a summary of total stocks discovered and analyzed

### Requirement 8: Web UI Integration

**User Story:** As a web UI user, I want to use the scan feature through the web interface, so that I can access the feature with a visual interface.

#### Acceptance Criteria

1. WHEN the scan page is accessed, THE Web_UI SHALL provide a button to trigger news-driven discovery
2. THE Web_UI SHALL display a loading indicator during the scan process
3. THE Web_UI SHALL show discovered symbols in a list before analysis begins
4. THE Web_UI SHALL display results in a sortable table with symbol, recommendation, confidence, and news mentions
5. WHEN the scan completes, THE Web_UI SHALL allow users to click on symbols for detailed analysis

### Requirement 9: Error Handling and Resilience

**User Story:** As a user, I want the system to handle errors gracefully, so that temporary failures don't prevent me from getting results.

#### Acceptance Criteria

1. WHEN a News_Provider fails, THE News_Discovery_System SHALL log the error and continue with other providers
2. WHEN symbol extraction fails for an article, THE News_Discovery_System SHALL skip that article and continue
3. WHEN stock analysis fails for a symbol, THE Stock_Scanner SHALL log the error and continue with remaining symbols
4. IF all News_Providers fail, THEN THE News_Discovery_System SHALL inform the user and suggest fallback options
5. THE News_Discovery_System SHALL provide meaningful error messages for common failure scenarios

### Requirement 10: Backward Compatibility

**User Story:** As an existing user, I want the existing analyze and recommend commands to continue working, so that my workflow is not disrupted.

#### Acceptance Criteria

1. THE CLI SHALL maintain the existing analyze command functionality
2. THE CLI SHALL maintain the existing recommend command functionality
3. WHEN the scan command is used with explicit symbol arguments, THE Stock_Scanner SHALL analyze those symbols instead of using news discovery
4. THE Analysis_Pipeline SHALL remain unchanged and continue to work with all existing commands
5. THE Web_UI SHALL maintain existing single-stock analysis functionality
