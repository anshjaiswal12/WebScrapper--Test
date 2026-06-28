"""
Flipkart scraper for laptop price comparison.

This scraper extends BaseScraper to extract product information from Flipkart.com
search results. Flipkart uses JavaScript for dynamic content loading, requiring
Selenium WebDriver for proper scraping.
"""
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
import time
import random
import os
from datetime import datetime

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

from src.scrapers.base_scraper import BaseScraper
from src.utils.logger import setup_logger
from config.settings import (
    USE_WEBDRIVER_MANAGER,
    HEADLESS,
    TIMEOUT,
    PAGE_LOAD_TIMEOUT,
    RATE_LIMIT_ENABLED,
    get_random_user_agent
)

logger = setup_logger()


class FlipkartScraper(BaseScraper):
    """
    Scraper for Flipkart.com search results.
    
    Extends BaseScraper to provide Flipkart-specific parsing logic using Selenium
    for dynamic content loading.
    """
    
    BASE_URL = "https://www.flipkart.com"
    
    # Flipkart-specific wait times
    DYNAMIC_CONTENT_WAIT = 5  # Wait for dynamic content to load
    SCROLL_PAUSE = 2  # Pause between scrolls
    COOKIE_WAIT = 3  # Wait for cookie popup
    
    def __init__(self, search_query: str, max_results: int = 10):
        """
        Initialize Flipkart scraper.
        
        Args:
            search_query: Product search query
            max_results: Maximum number of results to scrape (default: 10)
        """
        super().__init__(search_query, max_results, base_url=self.BASE_URL)
        self.wait: Optional[WebDriverWait] = None
        logger.info(f"Initialized FlipkartScraper for query: '{search_query}'")
    
    def _setup_selenium_driver(self) -> webdriver.Chrome:
        """
        Set up Selenium WebDriver with Flipkart-specific optimizations.
        
        Includes:
        - Headless mode for production
        - Window size for consistent rendering
        - Disabled images for faster loading
        - Stealth options to avoid detection
        - webdriver_manager for automatic driver management
        
        Returns:
            Configured Chrome WebDriver
        """
        chrome_options = Options()
        
        # Headless mode for production
        if HEADLESS:
            chrome_options.add_argument('--headless')
        
        # Basic options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        
        # Window size for consistent rendering (important for dynamic content)
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Disable images for faster loading (optional, can be enabled if needed)
        prefs = {
            'profile.managed_default_content_settings.images': 2,  # 2 = block images
            'profile.default_content_setting_values.notifications': 2
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Stealth options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
        
        try:
            if USE_WEBDRIVER_MANAGER and WEBDRIVER_MANAGER_AVAILABLE:
                logger.info("Using webdriver-manager for ChromeDriver")
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                logger.info("Using system ChromeDriver")
                driver = webdriver.Chrome(options=chrome_options)
            
            # Set timeouts
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            driver.implicitly_wait(TIMEOUT)
            
            # Execute stealth script to avoid detection
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            logger.info("Selenium WebDriver setup successful for Flipkart")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to setup Selenium WebDriver: {e}", exc_info=True)
            raise
    
    def build_search_url(self) -> str:
        """
        Build Flipkart search URL from query.
        
        Flipkart search URL format: https://www.flipkart.com/search?q={query}
        The 'q' parameter is the search keyword.
        
        Returns:
            Complete search URL with encoded query
        """
        encoded_query = quote_plus(self.search_query)
        search_url = f"{self.BASE_URL}/search?q={encoded_query}"
        logger.debug(f"Built search URL: {search_url}")
        return search_url
    
    def _handle_cookie_popup(self, driver: webdriver.Chrome):
        """
        Handle Flipkart cookie consent popup/banner.
        
        Flipkart often shows a cookie consent popup that needs to be closed
        before scraping can proceed.
        
        Args:
            driver: Selenium WebDriver instance
        """
        try:
            # Wait for cookie popup to appear (if it does)
            # Common selectors for cookie popups
            cookie_selectors = [
                "//button[contains(text(), '✕')]",  # Close button
                "//button[contains(@class, '_2KpZ6l')]",  # Close button class
                "//span[contains(text(), '✕')]",  # Close span
                "//button[contains(text(), 'Close')]"
            ]
            
            for selector in cookie_selectors:
                try:
                    # Wait up to 3 seconds for popup
                    close_button = WebDriverWait(driver, self.COOKIE_WAIT).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    close_button.click()
                    logger.info("Closed cookie popup")
                    time.sleep(1)  # Brief pause after closing
                    return
                except TimeoutException:
                    continue
            
            logger.debug("No cookie popup found or already closed")
            
        except Exception as e:
            logger.debug(f"Error handling cookie popup (may not exist): {e}")
    
    def _scroll_to_load_content(self, driver: webdriver.Chrome):
        """
        Scroll page to load lazy-loaded content.
        
        Flipkart uses lazy loading, so we need to scroll to trigger
        content loading. This is a best practice for dynamic content.
        
        Args:
            driver: Selenium WebDriver instance
        """
        try:
            # Get initial page height
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down gradually
            scroll_pause = self.SCROLL_PAUSE
            scroll_increment = 500  # Scroll 500px at a time
            
            current_position = 0
            max_scrolls = 3  # Limit scrolls to avoid infinite loading
            
            for _ in range(max_scrolls):
                # Scroll down
                current_position += scroll_increment
                driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Wait for content to load
                time.sleep(scroll_pause)
                
                # Check if new content loaded
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            logger.debug("Scrolled page to load dynamic content")
            
        except Exception as e:
            logger.warning(f"Error scrolling page: {e}")
    
    def _take_screenshot_on_error(self, driver: webdriver.Chrome, error_msg: str):
        """
        Take screenshot for debugging when error occurs.
        
        Args:
            driver: Selenium WebDriver instance
            error_msg: Error message for filename
        """
        try:
            screenshot_dir = "logs/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{screenshot_dir}/flipkart_error_{timestamp}.png"
            
            driver.save_screenshot(filename)
            logger.info(f"Screenshot saved to {filename}")
            
        except Exception as e:
            logger.warning(f"Could not save screenshot: {e}")
    
    def parse_product_data(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML and extract product data from Flipkart search results.
        
        Note: This method receives HTML from Selenium, but Flipkart's dynamic
        content is best extracted directly from Selenium elements. However,
        we implement this to satisfy the abstract method requirement.
        
        Args:
            html: HTML content (from Selenium page_source)
            
        Returns:
            List of product dictionaries
        """
        # For Flipkart, we'll use Selenium directly in scrape() method
        # This method is called by BaseScraper.scrape(), but we override
        # the behavior to use Selenium elements directly
        return []
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method with Selenium for dynamic content.
        
        Overrides BaseScraper.scrape() to use Selenium-specific logic
        for Flipkart's dynamic content.
        
        Returns:
            List of validated product dictionaries
        """
        logger.info("=" * 60)
        logger.info(f"Starting Flipkart scrape for query: '{self.search_query}'")
        logger.info(f"Maximum results: {self.max_results}")
        logger.info("=" * 60)
        
        driver = None
        products = []
        
        try:
            # Build search URL
            search_url = self.build_search_url()
            logger.info(f"Search URL: {search_url}")
            
            # Setup Selenium driver
            driver = self._setup_selenium_driver()
            self.driver = driver  # Store for BaseScraper.close()
            self.wait = WebDriverWait(driver, TIMEOUT)
            
            # Navigate to search page
            logger.info("Navigating to Flipkart search page...")
            driver.get(search_url)
            
            # Apply rate limiting
            self._apply_rate_limit()
            
            # Handle cookie popup
            self._handle_cookie_popup(driver)
            
            # Wait for product containers to load (explicit wait - best practice)
            logger.info("Waiting for product containers to load...")
            try:
                # Wait for at least one product container to appear
                self.wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 
                        'div._1AtVbE, div._13oc-S'
                    ))
                )
                logger.info("Product containers loaded")
            except TimeoutException:
                logger.warning("Product containers not found - possible empty results or page structure change")
                self._take_screenshot_on_error(driver, "no_products")
                return []
            
            # Scroll to load lazy content
            self._scroll_to_load_content(driver)
            
            # Additional wait for dynamic content
            time.sleep(self.DYNAMIC_CONTENT_WAIT)
            
            # Extract products using Selenium
            products = self._extract_products_with_selenium(driver)
            
            # Validate products
            validated_products = []
            for product in products:
                if self.validate_data(product):
                    validated_products.append(product)
                else:
                    logger.warning(f"Skipping invalid product: {product.get('product_name', 'Unknown')}")
            
            # Limit results
            validated_products = validated_products[:self.max_results]
            
            logger.info(f"Successfully scraped {len(validated_products)} products from Flipkart")
            self.products = validated_products
            
            return validated_products
            
        except TimeoutException as e:
            logger.error(f"Scraping timed out: {e}")
            if driver:
                self._take_screenshot_on_error(driver, "timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}", exc_info=True)
            if driver:
                self._take_screenshot_on_error(driver, "unexpected_error")
            return []
        finally:
            # Close browser properly (best practice)
            if driver:
                try:
                    driver.quit()
                    logger.info("Selenium WebDriver closed")
                except Exception as e:
                    logger.warning(f"Error closing WebDriver: {e}")
                finally:
                    self.driver = None
    
    def _extract_products_with_selenium(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """
        Extract products directly from Selenium elements.
        
        This is the preferred method for Flipkart as it handles dynamic content
        better than parsing HTML.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        try:
            # Find product containers using explicit wait
            # Primary selector: 'div._1AtVbE' - Flipkart's product container class
            # Fallback: 'div._13oc-S' - Alternative container class
            container_selectors = [
                'div._1AtVbE',
                'div._13oc-S',
                'div[data-id]'  # Generic data-id attribute
            ]
            
            containers = []
            for selector in container_selectors:
                try:
                    containers = driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        logger.info(f"Found {len(containers)} product containers using selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
                    continue
            
            if not containers:
                logger.warning("No product containers found")
                return []
            
            # Extract data from each container
            for container in containers:
                try:
                    # Scroll element into view (ensures it's loaded)
                    driver.execute_script("arguments[0].scrollIntoView(true);", container)
                    time.sleep(0.5)  # Brief pause for rendering
                    
                    product = self._extract_product_from_selenium_element(container)
                    
                    if product and product.get('price') and product.get('product_name'):
                        products.append(product)
                        
                        # Limit to max_results
                        if len(products) >= self.max_results:
                            break
                            
                except StaleElementReferenceException:
                    logger.debug("Stale element reference, skipping product")
                    continue
                except Exception as e:
                    logger.warning(f"Error extracting product: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting products with Selenium: {e}", exc_info=True)
        
        return products
    
    def _extract_product_from_selenium_element(self, container) -> Optional[Dict[str, Any]]:
        """
        Extract product information from a Selenium WebElement.
        
        Args:
            container: Selenium WebElement containing product data
            
        Returns:
            Product dictionary or None if extraction fails
        """
        product = {
            'source': 'Flipkart',
            'product_name': None,
            'price': None,
            'rating': None,
            'url': None,
            'sponsored': False
        }
        
        try:
            # Extract product name
            # Primary selector: 'div._4rR01T' - Flipkart's product title class
            # Fallback: 'a.s1Q9rs' - Alternative title selector
            name_selectors = [
                'div._4rR01T',
                'a.s1Q9rs',
                'a.IRpwTa',
                'div[class*="4rR01T"]'  # Partial class match
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = container.find_element(By.CSS_SELECTOR, selector)
                    if name_elem and name_elem.text.strip():
                        product['product_name'] = name_elem.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            if not product['product_name']:
                logger.debug("Could not extract product name")
                return None
            
            # Extract price
            # Primary selector: 'div._30jeq3' - Flipkart's price class
            # Fallback: 'div._30jeq3._1_WHN1' - Price with additional class
            price_selectors = [
                'div._30jeq3',
                'div._30jeq3._1_WHN1',
                'div[class*="30jeq3"]'  # Partial class match
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = container.find_element(By.CSS_SELECTOR, selector)
                    if price_elem and price_elem.text.strip():
                        price_text = price_elem.text.strip()
                        product['price'] = self.clean_price(price_text)
                        if product['price']:
                            break
                except NoSuchElementException:
                    continue
            
            # Extract rating
            # Selector: 'div._3LWZlK' - Flipkart's rating class
            rating_selectors = ['div._3LWZlK', 'div[class*="3LWZlK"]']
            product['rating'] = self.extract_rating(container, rating_selectors)
            
            # Extract product URL
            try:
                # Look for product link
                link_elem = container.find_element(By.CSS_SELECTOR, 'a')
                if link_elem:
                    href = link_elem.get_attribute('href')
                    if href:
                        if href.startswith('/'):
                            product['url'] = urljoin(self.BASE_URL, href)
                        elif href.startswith('http'):
                            product['url'] = href
                        else:
                            product['url'] = urljoin(self.BASE_URL, '/' + href)
            except NoSuchElementException:
                pass
            
            # Check if sponsored (Flipkart doesn't always mark sponsored clearly)
            # Look for ad indicators
            try:
                sponsored_indicators = container.find_elements(
                    By.CSS_SELECTOR, 
                    '[class*="ad"], [class*="sponsored"], [data-ad]'
                )
                product['sponsored'] = len(sponsored_indicators) > 0
            except:
                product['sponsored'] = False
            
            # Check stock status (Flipkart shows "Out of Stock" text)
            try:
                out_of_stock = container.find_elements(
                    By.XPATH,
                    "//*[contains(text(), 'Out of Stock') or contains(text(), 'Currently Unavailable')]"
                )
                product['in_stock'] = len(out_of_stock) == 0
            except:
                product['in_stock'] = True  # Default to in stock if can't determine
            
        except StaleElementReferenceException:
            logger.debug("Stale element reference during extraction")
            return None
        except Exception as e:
            logger.warning(f"Error extracting product data: {e}")
            return None
        
        return product
