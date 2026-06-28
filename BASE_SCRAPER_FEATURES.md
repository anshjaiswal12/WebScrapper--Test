# BaseScraper Features Documentation

## ✅ All Required Features Implemented

### 1. Abstract Methods (Child Classes Must Implement)
- ✅ `parse_product_data(html: str)` - Abstract method for parsing HTML
- ✅ `build_search_url()` - Abstract method to build search URL

### 2. Robust Error Handling
- ✅ Try-except blocks throughout all methods
- ✅ Specific exception handling for:
  - `TimeoutException` - Network timeouts
  - `WebDriverException` - Selenium errors
  - `NoSuchElementException` - Missing HTML elements
  - `requests.RequestException` - HTTP errors
  - `ValueError`, `AttributeError` - Invalid data formats
  - Generic `Exception` for unexpected errors

### 3. Rate Limiting
- ✅ Configurable rate limiting (2-3 seconds between requests)
- ✅ Random delay between MIN_RATE_LIMIT and MAX_RATE_LIMIT
- ✅ Respects `RATE_LIMIT_ENABLED` from settings

### 4. User-Agent Rotation
- ✅ Automatic user-agent rotation on retries
- ✅ Uses `get_random_user_agent()` from settings
- ✅ Updates both Selenium and requests session headers
- ✅ 6 different user agents available

### 5. Retry Logic with Exponential Backoff
- ✅ 3 retry attempts (configurable via `MAX_RETRIES`)
- ✅ Exponential backoff: `2^attempt` seconds
- ✅ Handles:
  - Network timeouts
  - HTTP 429 (Rate Limited)
  - HTTP 403 (Forbidden)
  - HTTP 5xx errors
- ✅ Logs each retry attempt

### 6. Data Validation and Cleaning
- ✅ `validate_data()` - Ensures required fields exist
- ✅ `clean_price()` - Removes ₹, commas, converts to float
- ✅ Validates price is numeric and positive
- ✅ Validates title is not empty

### 7. Comprehensive Logging
- ✅ Logs each request with URL and attempt number
- ✅ Logs successful extractions
- ✅ Logs errors with full details (exc_info=True)
- ✅ Logs retry attempts with wait times
- ✅ Debug logs for data extraction steps
- ✅ Warning logs for missing/invalid data

## Required Methods - All Implemented

### ✅ `__init__(search_query, max_results=10)`
- Initializes scraper with query and result limit
- Sets up base URL, user agent, and product storage
- Logs initialization

### ✅ `fetch_page(url, use_selenium=True)`
- Handles HTTP requests with error handling
- Supports both Selenium and requests library
- Implements retry logic with exponential backoff
- Handles status codes 403, 429
- Applies rate limiting after successful fetch
- Rotates user agent on retries

### ✅ `parse_product_data(html)` - Abstract
- Must be implemented by child classes
- Returns list of product dictionaries

### ✅ `extract_name(element, selectors)` 
- Extracts product name with fallback handling
- Tries multiple selectors in order
- Works with both BeautifulSoup and Selenium elements
- Returns None if not found (with logging)

### ✅ `extract_price(element, selectors)`
- Handles ₹, commas, missing prices
- Uses `clean_price()` for processing
- Tries multiple selectors
- Returns float or None

### ✅ `extract_rating(element, selectors)`
- Handles missing ratings gracefully
- Converts to float
- Tries multiple selectors
- Returns float or None

### ✅ `scrape()` - Main Orchestration Method
- Builds search URL
- Fetches page with retry logic
- Parses product data
- Validates all products
- Limits results to max_results
- Handles all exceptions
- Returns list of validated products
- Closes resources in finally block

### ✅ `validate_data(product_dict)`
- Ensures required fields exist ('title', 'price')
- Validates price is numeric and positive
- Validates title is not empty
- Returns boolean

### ✅ `clean_price(price_string)`
- Removes ₹, $, €, £ symbols
- Removes commas
- Extracts numeric value using regex
- Converts to float
- Returns None for invalid/missing prices

## Error Handling Coverage

### ✅ Network Timeouts
- Catches `TimeoutException`
- Retries with exponential backoff
- Logs timeout details

### ✅ Missing HTML Elements
- Catches `NoSuchElementException`
- Catches `AttributeError`
- Tries fallback selectors
- Returns None gracefully

### ✅ Invalid Data Formats
- Catches `ValueError` when converting to float
- Catches `TypeError` for type mismatches
- Validates data before returning

### ✅ Blocked Requests (403/429)
- Detects 403 (Forbidden) status
- Detects 429 (Rate Limited) status
- Rotates user agent on retry
- Increases wait time for 429

### ✅ Empty Search Results
- Checks HTML length
- Validates parsed products list
- Returns empty list with warning

## Additional Production-Ready Features

- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Resource cleanup (close WebDriver/session)
- ✅ Session management with retry strategy
- ✅ WebDriver manager integration
- ✅ Chrome options for anti-detection
- ✅ CDP commands for user-agent override
- ✅ Proper exception chaining
- ✅ Logging at appropriate levels (DEBUG, INFO, WARNING, ERROR)

## Usage Example

```python
from src.scrapers.base_scraper import BaseScraper

class MyScraper(BaseScraper):
    def build_search_url(self):
        return f"{self.base_url}/search?q={self.search_query}"
    
    def parse_product_data(self, html):
        # Implementation here
        pass

# Usage
scraper = MyScraper("HP Pavilion laptop", max_results=10)
products = scraper.scrape()
```

## Status: ✅ PRODUCTION READY

All requirements have been implemented with comprehensive error handling, logging, and validation.

