"""
Product matching module to identify the same product across different e-commerce sites.

This module implements intelligent product matching using:
- Model number extraction
- Normalized product names
- Price similarity
- Brand matching
"""
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger()


class ProductMatcher:
    """
    Matches products across different e-commerce sites to identify the same product.
    """
    
    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize product matcher.
        
        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider products as matches
        """
        self.similarity_threshold = similarity_threshold
        logger.info(f"ProductMatcher initialized with threshold: {similarity_threshold}")
    
    def extract_model_number(self, product_name: str) -> Optional[str]:
        """
        Extract model number from product name.
        
        Common patterns:
        - HP Pavilion 15-eg2007TU -> eg2007TU
        - iPhone 15 128GB -> 15
        - Sony WH-1000XM5 -> WH-1000XM5
        
        Args:
            product_name: Product name string
            
        Returns:
            Model number or None
        """
        if not product_name:
            return None
        
        # Pattern 1: Model numbers like "eg2007TU", "dv2000TU" (letters-numbers-letters)
        pattern1 = r'([a-z]{1,3}\d{3,6}[a-z]{0,3})'
        match = re.search(pattern1, product_name, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # Pattern 2: iPhone/iPad style "15", "14 Pro", "13 mini"
        pattern2 = r'(?:iPhone|iPad|MacBook)\s*(\d{1,2}(?:\s*(?:Pro|Max|Mini|Air|Plus))?)'
        match = re.search(pattern2, product_name, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 3: Sony/other brands "WH-1000XM5", "WF-1000XM4"
        pattern3 = r'([A-Z]{2,3}-\d{4}[A-Z]{0,3}\d?)'
        match = re.search(pattern3, product_name, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # Pattern 4: Generic model numbers
        pattern4 = r'(\d{4,6}[A-Z]{0,3})'
        match = re.search(pattern4, product_name, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def normalize_product_name(self, product_name: str) -> str:
        """
        Normalize product name for comparison.
        
        Args:
            product_name: Raw product name
            
        Returns:
            Normalized name
        """
        if not product_name:
            return ""
        
        # Convert to lowercase
        normalized = product_name.lower()
        
        # Remove special characters except spaces and hyphens
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common words that don't help matching
        stop_words = ['new', 'latest', 'best', 'buy', 'online', 'india']
        words = normalized.split()
        words = [w for w in words if w not in stop_words]
        normalized = ' '.join(words)
        
        return normalized
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two product names.
        
        Args:
            name1: First product name
            name2: Second product name
            
        Returns:
            Similarity score (0-1)
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize both names
        norm1 = self.normalize_product_name(name1)
        norm2 = self.normalize_product_name(name2)
        
        # Use SequenceMatcher for string similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        return similarity
    
    def match_products(self, products: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group products that are the same across different sites.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Dictionary mapping product group ID to list of matching products
        """
        if not products:
            return {}
        
        # Extract model numbers and normalize names
        for product in products:
            product_name = product.get('product_name') or product.get('title', '')
            product['model_number'] = self.extract_model_number(product_name)
            product['normalized_name'] = self.normalize_product_name(product_name)
        
        # Group by model number first (most reliable)
        groups = {}
        group_id = 0
        
        # Try to match by model number
        model_groups = {}
        for product in products:
            model = product.get('model_number')
            if model:
                if model not in model_groups:
                    model_groups[model] = []
                model_groups[model].append(product)
        
        # Assign group IDs to model-based groups
        for model, group_products in model_groups.items():
            if len(group_products) > 1:  # Multiple products with same model
                groups[f"group_{group_id}"] = group_products
                group_id += 1
        
        # For products without model numbers, try name similarity
        unmatched = [p for p in products if not p.get('model_number')]
        
        for product in unmatched:
            matched = False
            # Try to find similar product in existing groups
            for group_key, group_products in groups.items():
                for existing_product in group_products:
                    similarity = self.calculate_similarity(
                        product.get('product_name', ''),
                        existing_product.get('product_name', '')
                    )
                    if similarity >= self.similarity_threshold:
                        groups[group_key].append(product)
                        matched = True
                        break
                if matched:
                    break
            
            # If no match found, create new group
            if not matched:
                groups[f"group_{group_id}"] = [product]
                group_id += 1
        
        logger.info(f"Matched {len(products)} products into {len(groups)} groups")
        return groups
    
    def find_best_deal(self, matched_products: List[Dict]) -> Optional[Dict]:
        """
        Find the best deal (lowest price) from matched products.
        
        Args:
            matched_products: List of same products from different sites
            
        Returns:
            Product with lowest price or None
        """
        if not matched_products:
            return None
        
        valid_products = [p for p in matched_products if p.get('price') and p.get('price') > 0]
        
        if not valid_products:
            return None
        
        # Sort by price
        best_deal = min(valid_products, key=lambda x: x.get('price', float('inf')))
        
        return best_deal
    
    def calculate_savings(self, matched_products: List[Dict]) -> Optional[Dict]:
        """
        Calculate savings information for matched products.
        
        Args:
            matched_products: List of same products from different sites
            
        Returns:
            Dictionary with savings information
        """
        if not matched_products or len(matched_products) < 2:
            return None
        
        valid_products = [p for p in matched_products if p.get('price') and p.get('price') > 0]
        
        if len(valid_products) < 2:
            return None
        
        prices = [p['price'] for p in valid_products]
        min_price = min(prices)
        max_price = max(prices)
        
        savings = {
            'lowest_price': min_price,
            'highest_price': max_price,
            'price_difference': max_price - min_price,
            'percentage_savings': ((max_price - min_price) / max_price * 100) if max_price > 0 else 0,
            'best_deal_source': next(p['source'] for p in valid_products if p['price'] == min_price),
            'best_deal_url': next((p.get('url', '') for p in valid_products if p['price'] == min_price), '')
        }
        
        return savings

