"""
Helper utility functions for web scraping.
"""
import re
from typing import Optional


def clean_price(price_text: str) -> Optional[float]:
    """
    Extract and clean price from text.
    
    Args:
        price_text: Raw price text from website
        
    Returns:
        Cleaned price as float or None
    """
    if not price_text:
        return None
    
    # Remove currency symbols and extract numbers
    price_text = price_text.replace(',', '').replace('₹', '').strip()
    
    # Extract numeric value
    match = re.search(r'(\d+\.?\d*)', price_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    return ' '.join(text.split())


def extract_rating(rating_text: str) -> Optional[float]:
    """
    Extract rating from text.
    
    Args:
        rating_text: Raw rating text
        
    Returns:
        Rating as float or None
    """
    if not rating_text:
        return None
    
    match = re.search(r'(\d+\.?\d*)', rating_text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def extract_reviews_count(reviews_text: str) -> Optional[int]:
    """
    Extract number of reviews from text.
    
    Args:
        reviews_text: Raw reviews text
        
    Returns:
        Number of reviews as int or None
    """
    if not reviews_text:
        return None
    
    # Remove commas and extract number
    reviews_text = reviews_text.replace(',', '').replace('(', '').replace(')', '')
    match = re.search(r'(\d+)', reviews_text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None

