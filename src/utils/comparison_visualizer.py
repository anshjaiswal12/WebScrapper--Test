"""
Focused visualization for same-product price comparisons.

Shows where the same product is available at different prices across sites.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Dict, Optional
import os
from datetime import datetime

from src.utils.logger import setup_logger
from config.settings import IMAGES_OUTPUT_DIR

logger = setup_logger()

# Professional color scheme
COLOR_SCHEME = {
    'Amazon': '#2E86AB',
    'Flipkart': '#FF6B35',
    'Amazon India': '#2E86AB',
    'best': '#2ecc71'  # Green for best price
}

plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


class ComparisonVisualizer:
    """Create focused visualizations for same-product price comparisons."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = output_dir or IMAGES_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_same_product_comparison(self, comparisons: List[Dict], output_path: Optional[str] = None) -> tuple:
        """
        Create bar chart showing same product prices across sites.
        
        Args:
            comparisons: List of comparison dictionaries
            output_path: Output file path
            
        Returns:
            Tuple of (success, message)
        """
        if not comparisons:
            msg = "✗ No comparisons to visualize"
            logger.warning(msg)
            return False, msg
        
        try:
            # Create figure with subplots for each product
            n_products = len(comparisons)
            fig, axes = plt.subplots(n_products, 1, figsize=(12, 4 * n_products))
            
            if n_products == 1:
                axes = [axes]
            
            for idx, comp in enumerate(comparisons):
                ax = axes[idx] if n_products > 1 else axes[0]
                
                product_name = comp['product_name']
                sources = comp['sources']
                
                # Sort by price
                sorted_sources = sorted(sources.items(), key=lambda x: x[1].get('price', float('inf')))
                
                site_names = [s[0] for s in sorted_sources]
                prices = [s[1].get('price', 0) for s in sorted_sources]
                
                # Get best price
                best_price = min(prices) if prices else 0
                
                # Create bars with colors
                colors = [COLOR_SCHEME.get(site, '#95a5a6') for site in site_names]
                # Highlight best price
                for i, price in enumerate(prices):
                    if price == best_price:
                        colors[i] = COLOR_SCHEME['best']
                
                bars = ax.barh(site_names, prices, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
                
                # Add price labels
                for bar, price in zip(bars, prices):
                    width = bar.get_width()
                    ax.text(width, bar.get_y() + bar.get_height()/2,
                           f'₹{price:,.0f}',
                           ha='left', va='center', fontsize=10, fontweight='bold')
                
                # Add best price indicator
                if best_price > 0:
                    best_idx = prices.index(best_price)
                    ax.text(best_price, best_idx, ' 🏆 BEST',
                           ha='left', va='center', fontsize=9, fontweight='bold', color='green')
                
                ax.set_xlabel('Price (₹)', fontweight='bold', fontsize=11)
                ax.set_title(f"{product_name[:60]}...", fontweight='bold', fontsize=12, pad=10)
                ax.grid(axis='x', alpha=0.3)
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            
            plt.tight_layout()
            
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(self.output_dir, f"same_product_comparison_{timestamp}.png")
            elif not os.path.isabs(output_path):
                output_path = os.path.join(self.output_dir, output_path)
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            msg = f"✓ Same-product comparison chart saved to {output_path}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            msg = f"✗ Visualization failed: {str(e)}"
            logger.error(msg, exc_info=True)
            plt.close()
            return False, msg

