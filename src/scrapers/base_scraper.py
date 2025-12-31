"""
Abstract base class for all e-commerce scrapers.

This module provides a production-ready base scraper with:
- Abstract methods for child class implementation
- Robust error handling and retry logic
- Rate limiting and user-agent rotation
- Data validation and cleaning
- Comprehensive logging
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException
)
from bs4 import BeautifulSoup, Tag
import time
import re
import random
from urllib.parse import urljoin, urlparse

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.logger import setup_logger
from config.settings import (
    get_random_user_agent,
    USE_WEBDRIVER_MANAGER,
    RATE_LIMIT_DELAY,
    RATE_LIMIT_ENABLED,
    TIMEOUT,
    PAGE_LOAD_TIMEOUT
)

logger = setup_logger()


class BaseScraper(ABC):
    """
    Abstract base class for all e-commerce scrapers.
    
    Provides common functionality for:
    - Page fetching with retry logic
    - Rate limiting
    - User-agent rotation
    - Data extraction and validation
    - Error handling
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # Exponential backoff base
    
    # Rate limiting
    MIN_RATE_LIMIT = 2  # Minimum seconds between requests
    MAX_RATE_LIMIT = 3  # Maximum seconds between requests
    
    def __init__(self, search_query: str, max_results: int = 10, base_url: Optional[str] = None):
        """
        Initialize base scraper.
        
        Args:
            search_query: Product search query
            max_results: Maximum number of results to scrape (default: 10)
            base_url: Base URL of the e-commerce site (optional, can be set by child class)
        """
        self.search_query = search_query
        self.max_results = max_results
        self.base_url = base_url
        self.driver: Optional[webdriver.Chrome] = None
        self.session: Optional[requests.Session] = None
        self.current_user_agent = get_random_user_agent()
        self.products: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized scraper with query: '{search_query}', max_results: {max_results}")
    
    def _setup_session(self) -> requests.Session:
        """
        Set up requests session with retry strategy.
        
        Returns:
            Configured requests Session
        """
        session = requests.Session()
        
        # Retry strategy for network errors
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.RETRY_BACKOFF_BASE,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent
        session.headers.update({
            'User-Agent': self.current_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        logger.debug(f"Session configured with User-Agent: {self.current_user_agent[:50]}...")
        return session
    
    def _setup_driver(self) -> webdriver.Chrome:
        """
        Set up Selenium WebDriver with Chrome options.
        
        Returns:
            Configured Chrome WebDriver
            
        Raises:
            WebDriverException: If driver setup fails
        """
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'user-agent={self.current_user_agent}')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            if USE_WEBDRIVER_MANAGER and WEBDRIVER_MANAGER_AVAILABLE:
                logger.info("Using webdriver-manager for ChromeDriver")
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                logger.info("Using system ChromeDriver")
                driver = webdriver.Chrome(options=chrome_options)
            
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            driver.implicitly_wait(TIMEOUT)
            
            logger.info("WebDriver setup successful")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}", exc_info=True)
            raise WebDriverException(f"WebDriver setup failed: {e}") from e
    
    def _rotate_user_agent(self) -> str:
        """
        Rotate to a new random user agent.
        
        Returns:
            New user agent string
        """
        self.current_user_agent = get_random_user_agent()
        logger.debug(f"Rotated to new User-Agent: {self.current_user_agent[:50]}...")
        return self.current_user_agent
    
    def _apply_rate_limit(self):
        """
        Apply rate limiting with random delay between MIN and MAX.
        """
        if RATE_LIMIT_ENABLED:
            delay = random.uniform(self.MIN_RATE_LIMIT, self.MAX_RATE_LIMIT)
            logger.debug(f"Rate limiting: sleeping for {delay:.2f} seconds")
            time.sleep(delay)
        else:
            time.sleep(RATE_LIMIT_DELAY)
    
    def fetch_page(self, url: str, use_selenium: bool = True) -> Optional[str]:
        """
        Fetch page content with retry logic and error handling.
        
        Args:
            url: URL to fetch
            use_selenium: Whether to use Selenium (True) or requests (False)
            
        Returns:
            HTML content as string, or None if all retries fail
            
        Raises:
            TimeoutException: If request times out
            requests.RequestException: For HTTP errors
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching URL (attempt {attempt}/{self.MAX_RETRIES}): {url}")
                
                if use_selenium:
                    if not self.driver:
                        self.driver = self._setup_driver()
                    
                    # Rotate user agent every few requests
                    if attempt > 1:
                        self._rotate_user_agent()
                        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                            "userAgent": self.current_user_agent
                        })
                    
                    self.driver.get(url)
                    time.sleep(2)  # Wait for dynamic content
                    html = self.driver.page_source
                    
                else:
                    # Use requests library
                    if not self.session:
                        self.session = self._setup_session()
                    
                    # Rotate user agent on retry
                    if attempt > 1:
                        self._rotate_user_agent()
                        self.session.headers.update({'User-Agent': self.current_user_agent})
                    
                    response = self.session.get(url, timeout=PAGE_LOAD_TIMEOUT)
                    
                    # Check for blocking
                    if response.status_code == 403:
                        logger.warning(f"Access forbidden (403) for {url}")
                        if attempt < self.MAX_RETRIES:
                            self._rotate_user_agent()
                            continue
                        raise requests.RequestException(f"Access forbidden: {response.status_code}")
                    
                    if response.status_code == 429:
                        logger.warning(f"Rate limited (429) for {url}, waiting longer...")
                        wait_time = self.RETRY_BACKOFF_BASE ** attempt
                        time.sleep(wait_time)
                        if attempt < self.MAX_RETRIES:
                            continue
                        raise requests.RequestException(f"Rate limited: {response.status_code}")
                    
                    response.raise_for_status()
                    html = response.text
                
                logger.info(f"Successfully fetched page: {url}")
                self._apply_rate_limit()
                return html
                
            except TimeoutException as e:
                logger.warning(f"Timeout on attempt {attempt}/{self.MAX_RETRIES}: {e}")
                if attempt == self.MAX_RETRIES:
                    logger.error(f"All retry attempts failed for {url}")
                    raise
                wait_time = self.RETRY_BACKOFF_BASE ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
            except requests.RequestException as e:
                logger.warning(f"Request error on attempt {attempt}/{self.MAX_RETRIES}: {e}")
                if attempt == self.MAX_RETRIES:
                    logger.error(f"All retry attempts failed for {url}")
                    raise
                wait_time = self.RETRY_BACKOFF_BASE ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}/{self.MAX_RETRIES}: {e}", exc_info=True)
                if attempt == self.MAX_RETRIES:
                    raise
                wait_time = self.RETRY_BACKOFF_BASE ** attempt
                time.sleep(wait_time)
        
        return None
    
    def clean_price(self, price_string: str) -> Optional[float]:
        """
        Clean and convert price string to float.
        
        Handles:
        - Currency symbols (₹, $, etc.)
        - Commas in numbers
        - Missing or invalid prices
        
        Args:
            price_string: Raw price string from website
            
        Returns:
            Price as float, or None if invalid/missing
        """
        if not price_string:
            logger.debug("Empty price string provided")
            return None
        
        try:
            # Remove currency symbols and whitespace
            cleaned = price_string.replace('₹', '').replace('$', '').replace('€', '').replace('£', '')
            cleaned = cleaned.replace(',', '').strip()
            
            # Extract numeric value (handles cases like "45,999.50" or "₹45,999")
            match = re.search(r'(\d+\.?\d*)', cleaned)
            if match:
                price = float(match.group(1))
                logger.debug(f"Cleaned price: '{price_string}' -> {price}")
                return price
            else:
                logger.warning(f"Could not extract price from: '{price_string}'")
                return None
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error cleaning price '{price_string}': {e}")
            return None
    
    def extract_name(self, element: Any, selectors: List[str]) -> Optional[str]:
        """
        Extract product name with fallback handling.
        
        Args:
            element: BeautifulSoup element or Selenium element
            selectors: List of CSS selectors to try in order
            
        Returns:
            Product name as string, or None if not found
        """
        if not element:
            logger.debug("No element provided for name extraction")
            return None
        
        for selector in selectors:
            try:
                if isinstance(element, Tag):
                    # BeautifulSoup element
                    found = element.select_one(selector)
                    if found and found.get_text(strip=True):
                        name = found.get_text(strip=True)
                        logger.debug(f"Extracted name using selector '{selector}': {name[:50]}...")
                        return name
                else:
                    # Selenium element
                    found = element.find_element(By.CSS_SELECTOR, selector)
                    if found and found.text.strip():
                        name = found.text.strip()
                        logger.debug(f"Extracted name using selector '{selector}': {name[:50]}...")
                        return name
                        
            except (AttributeError, NoSuchElementException) as e:
                logger.debug(f"Selector '{selector}' not found: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error extracting name with selector '{selector}': {e}")
                continue
        
        logger.warning("Could not extract product name with any selector")
        return None
    
    def extract_price(self, element: Any, selectors: List[str]) -> Optional[float]:
        """
        Extract product price with fallback handling.
        
        Args:
            element: BeautifulSoup element or Selenium element
            selectors: List of CSS selectors to try in order
            
        Returns:
            Price as float, or None if not found
        """
        if not element:
            logger.debug("No element provided for price extraction")
            return None
        
        for selector in selectors:
            try:
                if isinstance(element, Tag):
                    # BeautifulSoup element
                    found = element.select_one(selector)
                    if found:
                        price_text = found.get_text(strip=True)
                        price = self.clean_price(price_text)
                        if price:
                            logger.debug(f"Extracted price using selector '{selector}': {price}")
                            return price
                else:
                    # Selenium element
                    found = element.find_element(By.CSS_SELECTOR, selector)
                    if found and found.text.strip():
                        price_text = found.text.strip()
                        price = self.clean_price(price_text)
                        if price:
                            logger.debug(f"Extracted price using selector '{selector}': {price}")
                            return price
                            
            except (AttributeError, NoSuchElementException) as e:
                logger.debug(f"Selector '{selector}' not found: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error extracting price with selector '{selector}': {e}")
                continue
        
        logger.warning("Could not extract product price with any selector")
        return None
    
    def extract_rating(self, element: Any, selectors: List[str]) -> Optional[float]:
        """
        Extract product rating with fallback handling.
        
        Args:
            element: BeautifulSoup element or Selenium element
            selectors: List of CSS selectors to try in order
            
        Returns:
            Rating as float, or None if not found
        """
        if not element:
            logger.debug("No element provided for rating extraction")
            return None
        
        for selector in selectors:
            try:
                if isinstance(element, Tag):
                    # BeautifulSoup element
                    found = element.select_one(selector)
                    if found:
                        rating_text = found.get_text(strip=True)
                        # Extract numeric value
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating = float(match.group(1))
                            logger.debug(f"Extracted rating using selector '{selector}': {rating}")
                            return rating
                else:
                    # Selenium element
                    found = element.find_element(By.CSS_SELECTOR, selector)
                    if found and found.text.strip():
                        rating_text = found.text.strip()
                        match = re.search(r'(\d+\.?\d*)', rating_text)
                        if match:
                            rating = float(match.group(1))
                            logger.debug(f"Extracted rating using selector '{selector}': {rating}")
                            return rating
                            
            except (AttributeError, NoSuchElementException) as e:
                logger.debug(f"Selector '{selector}' not found: {e}")
                continue
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing rating with selector '{selector}': {e}")
                continue
            except Exception as e:
                logger.warning(f"Error extracting rating with selector '{selector}': {e}")
                continue
        
        logger.debug("Could not extract product rating with any selector")
        return None
    
    def validate_data(self, product_dict: Dict[str, Any]) -> bool:
        """
        Validate that product dictionary has required fields.
        
        Args:
            product_dict: Product data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['title', 'price']
        
        for field in required_fields:
            if field not in product_dict or product_dict[field] is None:
                logger.warning(f"Product missing required field: {field}")
                return False
        
        # Validate price is numeric and positive
        if not isinstance(product_dict['price'], (int, float)) or product_dict['price'] <= 0:
            logger.warning(f"Invalid price value: {product_dict.get('price')}")
            return False
        
        # Validate title is not empty
        if not product_dict['title'] or not product_dict['title'].strip():
            logger.warning("Product title is empty")
            return False
        
        logger.debug(f"Product data validated: {product_dict.get('title', 'Unknown')[:50]}...")
        return True
    
    @abstractmethod
    def parse_product_data(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML and extract product data.
        
        This method must be implemented by child classes.
        
        Args:
            html: HTML content of the page
            
        Returns:
            List of product dictionaries
        """
        pass
    
    @abstractmethod
    def build_search_url(self) -> str:
        """
        Build search URL from query.
        
        This method must be implemented by child classes.
        
        Returns:
            Complete search URL
        """
        pass
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main method that orchestrates the scraping process.
        
        Returns:
            List of validated product dictionaries
            
        Raises:
            Exception: If scraping fails completely
        """
        logger.info("=" * 60)
        logger.info(f"Starting scrape for query: '{self.search_query}'")
        logger.info(f"Maximum results: {self.max_results}")
        logger.info("=" * 60)
        
        try:
            # Build search URL
            search_url = self.build_search_url()
            logger.info(f"Search URL: {search_url}")
            
            # Fetch page
            html = self.fetch_page(search_url, use_selenium=True)
            
            if not html:
                logger.error("Failed to fetch page content")
                return []
            
            # Check for empty results
            if len(html) < 100:
                logger.warning("Received very short HTML response, possible error page")
                return []
            
            # Parse product data
            logger.info("Parsing product data from HTML...")
            products = self.parse_product_data(html)
            
            if not products:
                logger.warning("No products found in parsed data")
                return []
            
            # Validate and clean products
            validated_products = []
            for product in products:
                if self.validate_data(product):
                    validated_products.append(product)
                else:
                    logger.warning(f"Skipping invalid product: {product.get('title', 'Unknown')}")
            
            # Limit results
            validated_products = validated_products[:self.max_results]
            
            logger.info(f"Successfully scraped {len(validated_products)} products")
            self.products = validated_products
            
            return validated_products
            
        except TimeoutException as e:
            logger.error(f"Scraping timed out: {e}")
            return []
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}", exc_info=True)
            return []
        finally:
            self.close()
    
    def close(self):
        """Close WebDriver and session resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("WebDriver closed")
        except Exception as e:
            logger.warning(f"Error closing WebDriver: {e}")
        
        try:
            if self.session:
                self.session.close()
                self.session = None
                logger.debug("Session closed")
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
