"""
Configuration settings for the Price Comparison Tool.

Environment variables override defaults for deployment (e.g. Render).
"""
import os
import random
from typing import List, Dict


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


# Search query configuration
SEARCH_QUERY = os.getenv('SEARCH_QUERY', 'HP Pavilion laptop')

# Maximum items per site (default: 10)
MAX_ITEMS_PER_SITE = _env_int('MAX_ITEMS_PER_SITE', 10)

# Timeout settings (in seconds)
TIMEOUT = _env_int('TIMEOUT', 10)
WAIT_TIME = _env_int('WAIT_TIME', 3)
PAGE_LOAD_TIMEOUT = _env_int('PAGE_LOAD_TIMEOUT', 30)

# User-agent rotation for better scraping
USER_AGENTS: List[str] = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def get_random_user_agent() -> str:
    """Get a random user agent from the list."""
    return random.choice(USER_AGENTS)


# Rate limiting settings (respect robots.txt)
RATE_LIMIT_DELAY = _env_int('RATE_LIMIT_DELAY', 2)
RATE_LIMIT_ENABLED = _env_bool('RATE_LIMIT_ENABLED', True)

# Robots.txt respect
RESPECT_ROBOTS_TXT = _env_bool('RESPECT_ROBOTS_TXT', True)

# Selenium settings
HEADLESS = _env_bool('HEADLESS', True)
IMPLICIT_WAIT = _env_int('IMPLICIT_WAIT', 10)
USE_WEBDRIVER_MANAGER = _env_bool('USE_WEBDRIVER_MANAGER', True)

# Demo mode — use sample data instead of live scraping
DEMO_MODE = _env_bool('DEMO_MODE', False)

# E-commerce sites configuration
SITES: Dict[str, Dict] = {
    'amazon': {
        'base_url': os.getenv('AMAZON_BASE_URL', 'https://www.amazon.in'),
        'enabled': _env_bool('AMAZON_ENABLED', True),
        'rate_limit_delay': 2,
    },
    'flipkart': {
        'base_url': os.getenv('FLIPKART_BASE_URL', 'https://www.flipkart.com'),
        'enabled': _env_bool('FLIPKART_ENABLED', True),
        'rate_limit_delay': 2,
    },
}

# Output paths
OUTPUT_BASE_DIR = os.getenv('OUTPUT_BASE_DIR', 'data/output')
CSV_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, 'csv')
EXCEL_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, 'excel')
IMAGES_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, 'images')

# Data filters
MIN_PRICE = _env_int('MIN_PRICE', 0)
MAX_PRICE = _env_int('MAX_PRICE', 200000)
MIN_RATING = _env_int('MIN_RATING', 0)

# Logging
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# ChromeDriver settings
CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH')

# Ensure output directories exist at import time for server deployments
for _dir in (CSV_OUTPUT_DIR, EXCEL_OUTPUT_DIR, IMAGES_OUTPUT_DIR, LOG_DIR):
    os.makedirs(_dir, exist_ok=True)
