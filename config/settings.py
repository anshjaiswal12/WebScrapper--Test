"""
Configuration settings for the Price Comparison Tool.
"""
import random
from typing import List, Dict

# Search query configuration
SEARCH_QUERY = "HP Pavilion laptop"

# Maximum items per site (default: 10)
MAX_ITEMS_PER_SITE = 10

# Timeout settings (in seconds)
TIMEOUT = 10
WAIT_TIME = 3
PAGE_LOAD_TIMEOUT = 30

# User-agent rotation for better scraping
USER_AGENTS: List[str] = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_random_user_agent() -> str:
    """Get a random user agent from the list."""
    return random.choice(USER_AGENTS)

# Rate limiting settings (respect robots.txt)
RATE_LIMIT_DELAY = 2  # Delay between requests in seconds
RATE_LIMIT_ENABLED = True

# Robots.txt respect
RESPECT_ROBOTS_TXT = True

# Selenium settings
HEADLESS = True  # Run browser in headless mode
IMPLICIT_WAIT = 10  # Implicit wait time for elements

# E-commerce sites configuration
SITES: Dict[str, Dict] = {
    'amazon': {
        'base_url': 'https://www.amazon.in',
        'enabled': True,
        'rate_limit_delay': 2
    },
    'flipkart': {
        'base_url': 'https://www.flipkart.com',
        'enabled': True,
        'rate_limit_delay': 2
    }
}

# Output paths
OUTPUT_BASE_DIR = 'data/output'
CSV_OUTPUT_DIR = 'data/output/csv'
EXCEL_OUTPUT_DIR = 'data/output/excel'
IMAGES_OUTPUT_DIR = 'data/output/images'

# Data filters
MIN_PRICE = 0
MAX_PRICE = 200000
MIN_RATING = 0

# Logging
LOG_DIR = 'logs'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR

# ChromeDriver settings
CHROMEDRIVER_PATH = None  # None = auto-detect or use webdriver-manager
USE_WEBDRIVER_MANAGER = True  # Use webdriver-manager for automatic ChromeDriver management

