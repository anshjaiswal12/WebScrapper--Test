"""
Price comparison engine for same products across multiple sites.

This module provides the core comparison logic to show where the same product
is cheapest across different e-commerce platforms.
"""
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from src.utils.product_matcher import ProductMatcher
from src.utils.logger import setup_logger

logger = setup_logger()


class ComparisonEngine:
    """
    Engine for comparing prices of the same product across different sites.
    """
    
    def __init__(self):
        """Initialize comparison engine."""
        self.matcher = ProductMatcher(similarity_threshold=0.75)
        logger.info("ComparisonEngine initialized")
    
    def compare_same_products(self, products: List[Dict]) -> List[Dict]:
        """
        Compare same products across different sites.
        
        Args:
            products: List of all products from all sites
            
        Returns:
            List of comparison results showing same products with prices from each site
        """
        if not products:
            logger.warning("No products to compare")
            return []
        
        # Match products
        matched_groups = self.matcher.match_products(products)
        
        comparisons = []
        
        for group_id, group_products in matched_groups.items():
            # Only process groups with products from multiple sources
            sources = set(p.get('source', '') for p in group_products)
            if len(sources) < 2:
                continue  # Skip if only one source
            
            # Get product name (use first product's name)
            product_name = group_products[0].get('product_name') or group_products[0].get('title', 'Unknown')
            
            # Find best deal
            best_deal = self.matcher.find_best_deal(group_products)
            savings = self.matcher.calculate_savings(group_products)
            
            # Create comparison entry
            comparison = {
                'product_name': product_name,
                'model_number': group_products[0].get('model_number'),
                'sources': {},
                'best_deal': best_deal,
                'savings': savings,
                'total_listings': len(group_products)
            }
            
            # Add price info from each source
            for product in group_products:
                source = product.get('source', 'Unknown')
                comparison['sources'][source] = {
                    'price': product.get('price'),
                    'rating': product.get('rating'),
                    'url': product.get('url'),
                    'in_stock': product.get('in_stock', True)  # Default to True if not specified
                }
            
            comparisons.append(comparison)
        
        logger.info(f"Created {len(comparisons)} product comparisons")
        return comparisons
    
    def format_comparison_output(self, comparisons: List[Dict]) -> str:
        """
        Format comparison results for display.
        
        Args:
            comparisons: List of comparison dictionaries
            
        Returns:
            Formatted string output
        """
        if not comparisons:
            return "No matching products found across sites."
        
        output_lines = []
        output_lines.append("\n" + "=" * 80)
        output_lines.append("PRICE COMPARISON - SAME PRODUCTS ACROSS SITES")
        output_lines.append("=" * 80)
        output_lines.append("")
        
        for comp in comparisons:
            product_name = comp['product_name']
            output_lines.append(f"Product: {product_name}")
            output_lines.append("━" * 80)
            
            # Sort sources by price
            sources_sorted = sorted(
                comp['sources'].items(),
                key=lambda x: x[1].get('price', float('inf'))
            )
            
            best_price = sources_sorted[0][1].get('price') if sources_sorted else None
            
            for source, info in sources_sorted:
                price = info.get('price', 0)
                rating = info.get('rating')
                in_stock = info.get('in_stock', True)
                
                # Format price
                price_str = f"₹{price:,.0f}" if price else "N/A"
                
                # Format rating
                rating_str = f"⭐ {rating}/5" if rating else "⭐ N/A"
                
                # Stock status
                stock_str = "✓ In Stock" if in_stock else "✗ Out of Stock"
                
                # Best price indicator
                best_indicator = " 🏆 BEST PRICE" if price == best_price and price else ""
                
                output_lines.append(
                    f"{source:<20} {price_str:<15} {rating_str:<10} {stock_str:<15}{best_indicator}"
                )
            
            # Show savings if available
            if comp.get('savings'):
                savings = comp['savings']
                if savings['price_difference'] > 0:
                    output_lines.append("")
                    output_lines.append(
                        f"💰 BEST DEAL: Buy from {savings['best_deal_source']} and "
                        f"SAVE ₹{savings['price_difference']:,.0f} "
                        f"({savings['percentage_savings']:.1f}%)!"
                    )
                    if savings.get('best_deal_url'):
                        output_lines.append(f"   Link: {savings['best_deal_url']}")
            
            output_lines.append("")
            output_lines.append("=" * 80)
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    def export_comparison_csv(self, comparisons: List[Dict], filename: str) -> Tuple[bool, str]:
        """
        Export comparison results to CSV.
        
        Args:
            comparisons: List of comparison dictionaries
            filename: Output filename
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Flatten comparison data for CSV
            rows = []
            for comp in comparisons:
                product_name = comp['product_name']
                sources = comp['sources']
                
                # Get minimum price for this product
                prices = [v.get('price', float('inf')) for v in sources.values() if v.get('price')]
                min_price = min(prices) if prices else float('inf')
                
                for source, info in sources.items():
                    price = info.get('price', 0)
                    is_best = (price == min_price) if price > 0 and min_price != float('inf') else False
                    
                    rows.append({
                        'Product Name': product_name,
                        'Model Number': comp.get('model_number', ''),
                        'Source': source,
                        'Price': price,
                        'Rating': info.get('rating', ''),
                        'In Stock': info.get('in_stock', True),
                        'URL': info.get('url', ''),
                        'Is Best Price': is_best
                    })
            
            df = pd.DataFrame(rows)
            
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_csv(filename, index=False, encoding='utf-8')
            
            msg = f"✓ Comparison exported to {filename}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            msg = f"✗ Export failed: {str(e)}"
            logger.error(msg, exc_info=True)
            return False, msg

