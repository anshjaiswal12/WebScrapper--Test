"""
Amazon India scraper for laptop price comparison.

This scraper extends BaseScraper to extract product information from Amazon.in
search results. It handles sponsored results, unavailable products, and various
price formats.
"""
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup, Tag
import re

from src.scrapers.base_scraper import BaseScraper
from src.utils.logger import setup_logger

logger = setup_logger()


class AmazonScraper(BaseScraper):
    """
    Scraper for Amazon India search results.
    
    Extends BaseScraper to provide Amazon-specific parsing logic.
    """
    
    BASE_URL = "https://www.amazon.in"
    
    def __init__(self, search_query: str, max_results: int = 10):
        """
        Initialize Amazon scraper.
        
        Args:
            search_query: Product search query
            max_results: Maximum number of results to scrape (default: 10)
        """
        super().__init__(search_query, max_results, base_url=self.BASE_URL)
        logger.info(f"Initialized AmazonScraper for query: '{search_query}'")
    
    def build_search_url(self) -> str:
        """
        Build Amazon India search URL from query.
        
        Amazon search URL format: https://www.amazon.in/s?k={query}
        The 'k' parameter is the search keyword.
        
        Returns:
            Complete search URL with encoded query
        """
        encoded_query = quote_plus(self.search_query)
        search_url = f"{self.BASE_URL}/s?k={encoded_query}"
        logger.debug(f"Built search URL: {search_url}")
        return search_url
    
    def parse_product_data(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML and extract product data from Amazon search results.
        
        This method:
        1. Finds all product containers using Amazon's data attribute
        2. Extracts product information from each container
        3. Handles sponsored vs organic results
        4. Filters out unavailable products
        5. Extracts discount information if available
        
        Args:
            html: HTML content of the Amazon search results page
            
        Returns:
            List of product dictionaries with required fields
        """
        products = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check for captcha or blocking
            if self._detect_captcha(soup):
                logger.warning("Captcha detected on Amazon page - may need manual intervention")
                return []
            
            # Primary selector: Amazon uses data-component-type="s-search-result" for product containers
            # This is the most reliable selector as it's a data attribute that doesn't change
            product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            if not product_containers:
                # Fallback selector: class-based selector (may change with UI updates)
                product_containers = soup.find_all('div', class_='s-result-item')
                logger.warning("Using fallback selector for product containers")
            
            if not product_containers:
                logger.warning("No product containers found - possible empty results or page structure change")
                return []
            
            logger.info(f"Found {len(product_containers)} product containers")
            
            # Process each product container
            for container in product_containers:
                try:
                    product = self._extract_product_from_container(container)
                    
                    # Only add products with valid data
                    if product and product.get('price') and product.get('product_name'):
                        products.append(product)
                        
                        # Limit to max_results
                        if len(products) >= self.max_results:
                            break
                            
                except Exception as e:
                    logger.warning(f"Error extracting product from container: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(products)} products from Amazon")
            
        except Exception as e:
            logger.error(f"Error parsing Amazon HTML: {e}", exc_info=True)
        
        return products
    
    def _detect_captcha(self, soup: BeautifulSoup) -> bool:
        """
        Detect if Amazon is showing a captcha page.
        
        Amazon captcha pages typically contain specific text or form elements.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            True if captcha is detected, False otherwise
        """
        # Check for common captcha indicators
        captcha_indicators = [
            soup.find('form', {'action': re.compile(r'captcha', re.I)}),
            soup.find(string=re.compile(r'enter the characters', re.I)),
            soup.find(string=re.compile(r'type the characters', re.I)),
            soup.find('div', {'id': re.compile(r'captcha', re.I)})
        ]
        
        return any(captcha_indicators)
    
    def _extract_product_from_container(self, container: Tag) -> Optional[Dict[str, Any]]:
        """
        Extract product information from a single product container.
        
        Args:
            container: BeautifulSoup Tag element containing product data
            
        Returns:
            Product dictionary or None if extraction fails
        """
        product = {
            'source': 'Amazon',
            'product_name': None,
            'price': None,
            'rating': None,
            'url': None,
            'sponsored': False
        }
        
        try:
            # Extract product name
            # Primary selector: 'h2 a span' - Amazon wraps product titles in h2 > a > span
            # Fallback: '.a-text-normal' - Alternative class for product names
            name_selectors = ['h2 a span', '.a-text-normal', 'h2 span']
            product['product_name'] = self.extract_name(container, name_selectors)
            
            if not product['product_name']:
                logger.debug("Could not extract product name, skipping product")
                return None
            
            # Check if product is unavailable
            if self._is_unavailable(container):
                logger.debug(f"Product unavailable: {product['product_name'][:50]}...")
                return None
            
            # Extract price
            # Primary selector: 'span.a-price-whole' - Amazon shows whole price separately
            # This selector gets the main price (without decimals)
            price_selectors = [
                'span.a-price-whole',  # Whole number part
                'span.a-price .a-offscreen',  # Hidden price (more reliable)
                'span.a-price',  # Price container
                '.a-price-whole'  # Alternative class
            ]
            product['price'] = self.extract_price(container, price_selectors)
            
            # If price not found with whole selector, try to get from price container
            if not product['price']:
                price_container = container.select_one('span.a-price')
                if price_container:
                    # Try to extract from price container's text
                    price_text = price_container.get_text(strip=True)
                    product['price'] = self.clean_price(price_text)
            
            # Extract rating
            # Primary selector: 'span.a-icon-alt' - Contains "X out of 5 stars" text
            # Fallback: 'i.a-star-small span' - Alternative rating display
            rating_selectors = [
                'span.a-icon-alt',
                'i.a-star-small span',
                '.a-icon-alt',
                'span[aria-label*="stars"]'
            ]
            product['rating'] = self.extract_rating(container, rating_selectors)
            
            # Extract product URL
            product['url'] = self._extract_product_url(container)
            
            # Check if sponsored
            product['sponsored'] = self._is_sponsored(container)
            
            # Check stock status
            product['in_stock'] = not self._is_unavailable(container)
            
            # Extract discount if available (optional field)
            discount = self._extract_discount(container)
            if discount:
                product['discount'] = discount
            
            # Extract MRP and Deal Price if available
            mrp = self._extract_mrp(container)
            if mrp:
                product['mrp'] = mrp
            
        except Exception as e:
            logger.warning(f"Error extracting product data: {e}")
            return None
        
        return product
    
    def _is_unavailable(self, container: Tag) -> bool:
        """
        Check if product is currently unavailable.
        
        Amazon shows "Currently unavailable" text for out-of-stock items.
        
        Args:
            container: Product container element
            
        Returns:
            True if product is unavailable, False otherwise
        """
        unavailable_indicators = [
            container.find(string=re.compile(r'currently unavailable', re.I)),
            container.find(string=re.compile(r'out of stock', re.I)),
            container.find('span', string=re.compile(r'unavailable', re.I)),
            # Check for missing price as indicator
            not container.select_one('span.a-price-whole') and 
            not container.select_one('span.a-price')
        ]
        
        return any(unavailable_indicators)
    
    def _is_sponsored(self, container: Tag) -> bool:
        """
        Check if product is a sponsored/ad result.
        
        Amazon marks sponsored results with specific attributes or text.
        
        Args:
            container: Product container element
            
        Returns:
            True if sponsored, False otherwise
        """
        sponsored_indicators = [
            # Check for sponsored badge/attribute
            container.find('span', string=re.compile(r'sponsored', re.I)),
            container.find('div', {'data-component-type': 'sp-sponsored-result'}),
            # Check parent for sponsored class
            container.find_parent('div', class_=re.compile(r'sponsored', re.I)),
            # Check for ad indicator in data attributes
            container.get('data-ad-type') is not None,
            # Some sponsored results have specific classes
            'AdHolder' in str(container.get('class', []))
        ]
        
        return any(sponsored_indicators)
    
    def _extract_product_url(self, container: Tag) -> Optional[str]:
        """
        Extract product URL from container.
        
        Amazon product links are typically in h2 > a or have class 'a-link-normal'.
        
        Args:
            container: Product container element
            
        Returns:
            Product URL or None
        """
        try:
            # Primary: Look for link in h2 (product title link)
            link_elem = container.select_one('h2 a')
            
            if not link_elem:
                # Fallback: Look for any product link
                link_elem = container.select_one('a.a-link-normal')
            
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                
                # Amazon uses relative URLs, need to make absolute
                if href.startswith('/'):
                    return urljoin(self.BASE_URL, href)
                elif href.startswith('http'):
                    return href
                else:
                    return urljoin(self.BASE_URL, '/' + href)
            
        except Exception as e:
            logger.debug(f"Error extracting product URL: {e}")
        
        return None
    
    def _extract_discount(self, container: Tag) -> Optional[float]:
        """
        Extract discount percentage if available.
        
        Amazon shows discounts like "Save ₹X (Y%)" or just percentage.
        
        Args:
            container: Product container element
            
        Returns:
            Discount percentage as float, or None
        """
        try:
            # Look for discount text patterns
            discount_text = container.find(string=re.compile(r'\d+%', re.I))
            
            if discount_text:
                # Extract percentage number
                match = re.search(r'(\d+)%', discount_text)
                if match:
                    discount = float(match.group(1))
                    logger.debug(f"Found discount: {discount}%")
                    return discount
            
            # Alternative: Look in savings span
            savings_elem = container.select_one('span.a-size-base.a-color-price')
            if savings_elem:
                savings_text = savings_elem.get_text()
                match = re.search(r'(\d+)%', savings_text)
                if match:
                    return float(match.group(1))
        
        except Exception as e:
            logger.debug(f"Error extracting discount: {e}")
        
        return None
    
    def _extract_mrp(self, container: Tag) -> Optional[float]:
        """
        Extract MRP (Maximum Retail Price) if available.
        
        Amazon sometimes shows both MRP and Deal Price.
        
        Args:
            container: Product container element
            
        Returns:
            MRP as float, or None
        """
        try:
            # Look for MRP text
            mrp_elem = container.find(string=re.compile(r'MRP', re.I))
            
            if mrp_elem:
                # Find price near MRP text
                parent = mrp_elem.find_parent()
                if parent:
                    price_text = parent.get_text()
                    mrp = self.clean_price(price_text)
                    if mrp:
                        return mrp
            
            # Alternative: Look for strike-through price (usually MRP)
            strike_price = container.select_one('span.a-price.a-text-price')
            if strike_price:
                price_text = strike_price.get_text()
                mrp = self.clean_price(price_text)
                if mrp:
                    return mrp
        
        except Exception as e:
            logger.debug(f"Error extracting MRP: {e}")
        
        return None
