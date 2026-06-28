"""
Visualization module for generating professional price comparison charts.
"""
import matplotlib
matplotlib.use('Agg')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from typing import Optional, Dict, Tuple
import os
import numpy as np
from datetime import datetime
import warnings

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning)

from src.utils.logger import setup_logger
from config.settings import IMAGES_OUTPUT_DIR

logger = setup_logger()

# Professional color scheme (blues/greens)
COLOR_SCHEME = {
    'Amazon': '#2E86AB',      # Blue
    'Flipkart': '#FF6B35',   # Orange
    'Amazon India': '#2E86AB',
    'default': '#3498db'
}

# Set professional style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 14


class Visualizer:
    """
    Create professional visualizations for price comparison data.
    
    Provides methods for generating charts with consistent styling,
    high resolution, and publication-quality formatting.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory to save plots (default: data/output/images)
        """
        self.output_dir = output_dir or IMAGES_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Visualizer initialized with output directory: {self.output_dir}")
    
    def _truncate_name(self, name: str, max_length: int = 40) -> str:
        """
        Truncate product name if too long.
        
        Args:
            name: Product name
            max_length: Maximum length
            
        Returns:
            Truncated name with ellipsis
        """
        if not name or pd.isna(name):
            return "Unknown Product"
        
        name_str = str(name)
        if len(name_str) > max_length:
            return name_str[:max_length-3] + "..."
        return name_str
    
    def _get_source_color(self, source: str) -> str:
        """
        Get color for source.
        
        Args:
            source: Source name
            
        Returns:
            Color code
        """
        return COLOR_SCHEME.get(source, COLOR_SCHEME['default'])
    
    def _check_data_validity(self, df: pd.DataFrame, required_columns: list) -> Tuple[bool, str]:
        """
        Check if DataFrame has required columns and data.
        
        Args:
            df: DataFrame to check
            required_columns: List of required column names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if df is None or df.empty:
            return False, "DataFrame is empty or None"
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {missing_columns}"
        
        return True, ""
    
    def create_price_comparison_chart(self, df: pd.DataFrame, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create horizontal bar chart showing prices across sources for each product.
        
        Features:
        - X-axis: Price (₹)
        - Y-axis: Product names (truncated if too long)
        - Different color per source (Amazon=blue, Flipkart=orange)
        - Show exact price on bars
        - Title: "Laptop Price Comparison - {date}"
        - Save as PNG in data/output/
        
        Args:
            df: DataFrame with product data (must have 'product_name' or 'title', 'price', 'source')
            output_path: Output file path (optional, will generate if not provided)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check data validity
        name_col = 'product_name' if 'product_name' in df.columns else 'title'
        is_valid, error_msg = self._check_data_validity(df, [name_col, 'price', 'source'])
        if not is_valid:
            msg = f"✗ Price comparison chart failed: {error_msg}"
            logger.warning(msg)
            return False, msg
        
        try:
            # Filter valid data
            valid_df = df[df['price'].notna() & (df['price'] > 0)].copy()
            
            if valid_df.empty:
                msg = "✗ Price comparison chart failed: No valid price data"
                logger.warning(msg)
                return False, msg
            
            # Truncate product names
            valid_df['display_name'] = valid_df[name_col].apply(self._truncate_name)
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Get unique products and sources
            products = valid_df['display_name'].unique()
            sources = valid_df['source'].unique()
            
            # Prepare data for grouped bars
            y_pos = np.arange(len(products))
            bar_width = 0.35
            
            # Create bars for each source
            for idx, source in enumerate(sources):
                source_data = valid_df[valid_df['source'] == source]
                source_prices = []
                source_positions = []
                
                for product in products:
                    product_data = source_data[source_data['display_name'] == product]
                    if not product_data.empty:
                        source_prices.append(product_data['price'].iloc[0])
                        source_positions.append(np.where(products == product)[0][0])
                    else:
                        source_prices.append(0)
                        source_positions.append(np.where(products == product)[0][0])
                
                # Calculate bar positions
                if len(sources) == 1:
                    bar_positions = y_pos
                else:
                    offset = (idx - len(sources)/2 + 0.5) * bar_width
                    bar_positions = y_pos + offset
                
                # Create bars
                bars = ax.barh(bar_positions, source_prices, bar_width, 
                              label=source, color=self._get_source_color(source),
                              alpha=0.8, edgecolor='black', linewidth=0.5)
                
                # Add price labels on bars
                for bar, price in zip(bars, source_prices):
                    if price > 0:
                        width = bar.get_width()
                        ax.text(width, bar.get_y() + bar.get_height()/2,
                               f'₹{price:,.0f}',
                               ha='left', va='center', fontsize=8, fontweight='bold')
            
            # Customize axes
            ax.set_yticks(y_pos)
            ax.set_yticklabels(products)
            ax.set_xlabel('Price (₹)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Product', fontsize=11, fontweight='bold')
            
            # Title with date
            date_str = datetime.now().strftime('%B %d, %Y')
            ax.set_title(f'Laptop Price Comparison - {date_str}', 
                         fontsize=13, fontweight='bold', pad=15)
            
            # Add grid
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
            
            # Add legend
            ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True)
            
            # Invert y-axis to show highest price at top
            ax.invert_yaxis()
            
            # Format x-axis with currency
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            
            plt.tight_layout()
            
            # Generate filename if not provided
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(self.output_dir, f"price_comparison_{timestamp}.png")
            elif not os.path.isabs(output_path):
                output_path = os.path.join(self.output_dir, output_path)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save with high DPI
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            msg = f"✓ Price comparison chart saved to {output_path}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            msg = f"✗ Price comparison chart failed: {str(e)}"
            logger.error(msg, exc_info=True)
            plt.close()
            return False, msg
    
    def create_price_distribution_chart(self, df: pd.DataFrame, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create box plot showing price distribution by source.
        
        Features:
        - Compare price ranges between sites
        - Show outliers
        - Median price line
        - Professional styling
        
        Args:
            df: DataFrame with product data (must have 'price', 'source')
            output_path: Output file path (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        is_valid, error_msg = self._check_data_validity(df, ['price', 'source'])
        if not is_valid:
            msg = f"✗ Price distribution chart failed: {error_msg}"
            logger.warning(msg)
            return False, msg
        
        try:
            # Filter valid data
            valid_df = df[df['price'].notna() & (df['price'] > 0)].copy()
            
            if valid_df.empty:
                msg = "✗ Price distribution chart failed: No valid price data"
                logger.warning(msg)
                return False, msg
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create box plot
            sources = valid_df['source'].unique()
            data_to_plot = [valid_df[valid_df['source'] == source]['price'].values 
                           for source in sources]
            
            # Create box plot with custom colors
            bp = ax.boxplot(
                data_to_plot,
                tick_labels=sources,
                patch_artist=True,
                showmeans=True,
                meanline=True,
                boxprops=dict(linewidth=1.5),
                medianprops=dict(linewidth=2, color='red'),
                meanprops=dict(linewidth=1.5, linestyle='--', color='blue'),
            )
            
            # Color boxes by source
            for patch, source in zip(bp['boxes'], sources):
                patch.set_facecolor(self._get_source_color(source))
                patch.set_alpha(0.7)
            
            # Customize axes
            ax.set_ylabel('Price (₹)', fontsize=11, fontweight='bold')
            ax.set_xlabel('E-commerce Site', fontsize=11, fontweight='bold')
            
            # Title
            date_str = datetime.now().strftime('%B %d, %Y')
            ax.set_title(f'Price Distribution by Source - {date_str}',
                        fontsize=13, fontweight='bold', pad=15)
            
            # Format y-axis with currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            
            # Add grid
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
            
            # Add legend for median and mean
            median_line = mpatches.Patch(color='red', label='Median')
            mean_line = mpatches.Patch(color='blue', label='Mean', linestyle='--')
            ax.legend(handles=[median_line, mean_line], loc='upper right')
            
            plt.tight_layout()
            
            # Generate filename if not provided
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(self.output_dir, f"price_distribution_{timestamp}.png")
            elif not os.path.isabs(output_path):
                output_path = os.path.join(self.output_dir, output_path)
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save with high DPI
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            msg = f"✓ Price distribution chart saved to {output_path}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            msg = f"✗ Price distribution chart failed: {str(e)}"
            logger.error(msg, exc_info=True)
            plt.close()
            return False, msg
    
    def create_summary_dashboard(self, df: pd.DataFrame, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create multi-panel figure with comprehensive summary.
        
        Panels:
        - Subplot 1: Price comparison bars
        - Subplot 2: Average rating by source
        - Subplot 3: Number of products by source
        - Subplot 4: Price statistics table
        
        Args:
            df: DataFrame with product data
            output_path: Output file path (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        is_valid, error_msg = self._check_data_validity(df, ['price', 'source'])
        if not is_valid:
            msg = f"✗ Summary dashboard failed: {error_msg}"
            logger.warning(msg)
            return False, msg
        
        try:
            # Filter valid data
            valid_df = df[df['price'].notna() & (df['price'] > 0)].copy()
            
            if valid_df.empty:
                msg = "✗ Summary dashboard failed: No valid price data"
                logger.warning(msg)
                return False, msg
            
            # Create figure with subplots
            fig = plt.figure(figsize=(14, 10))
            gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
            
            # Subplot 1: Price comparison bars (by source)
            ax1 = fig.add_subplot(gs[0, 0])
            source_stats = valid_df.groupby('source')['price'].agg(['mean', 'min', 'max']).reset_index()
            x_pos = np.arange(len(source_stats))
            width = 0.25
            
            ax1.bar(x_pos - width, source_stats['min'], width, label='Min', 
                   color='#2ecc71', alpha=0.8, edgecolor='black')
            ax1.bar(x_pos, source_stats['mean'], width, label='Mean', 
                   color='#3498db', alpha=0.8, edgecolor='black')
            ax1.bar(x_pos + width, source_stats['max'], width, label='Max', 
                   color='#e74c3c', alpha=0.8, edgecolor='black')
            
            ax1.set_xlabel('E-commerce Site', fontweight='bold')
            ax1.set_ylabel('Price (₹)', fontweight='bold')
            ax1.set_title('Price Comparison by Source', fontweight='bold')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(source_stats['source'])
            ax1.legend()
            ax1.grid(axis='y', alpha=0.3)
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            
            # Subplot 2: Average rating by source
            ax2 = fig.add_subplot(gs[0, 1])
            if 'rating' in valid_df.columns:
                rating_stats = valid_df.groupby('source')['rating'].mean().reset_index()
                bars = ax2.bar(rating_stats['source'], rating_stats['rating'],
                              color=[self._get_source_color(s) for s in rating_stats['source']],
                              alpha=0.8, edgecolor='black')
                ax2.set_ylabel('Average Rating', fontweight='bold')
                ax2.set_xlabel('E-commerce Site', fontweight='bold')
                ax2.set_title('Average Rating by Source', fontweight='bold')
                ax2.set_ylim(0, 5)
                ax2.grid(axis='y', alpha=0.3)
                
                # Add value labels
                for bar, value in zip(bars, rating_stats['rating']):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                            f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
            else:
                ax2.text(0.5, 0.5, 'No rating data available', 
                        ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Average Rating by Source', fontweight='bold')
            
            # Subplot 3: Number of products by source
            ax3 = fig.add_subplot(gs[1, 0])
            product_counts = valid_df['source'].value_counts()
            bars = ax3.bar(product_counts.index, product_counts.values,
                          color=[self._get_source_color(s) for s in product_counts.index],
                          alpha=0.8, edgecolor='black')
            ax3.set_ylabel('Number of Products', fontweight='bold')
            ax3.set_xlabel('E-commerce Site', fontweight='bold')
            ax3.set_title('Product Count by Source', fontweight='bold')
            ax3.grid(axis='y', alpha=0.3)
            
            # Add value labels
            for bar, value in zip(bars, product_counts.values):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        str(value), ha='center', va='bottom', fontweight='bold')
            
            # Subplot 4: Price statistics table
            ax4 = fig.add_subplot(gs[1, 1])
            ax4.axis('off')
            
            # Calculate statistics
            stats_data = [
                ['Metric', 'Value'],
                ['Total Products', str(len(valid_df))],
                ['Lowest Price', f"₹{valid_df['price'].min():,.0f}"],
                ['Highest Price', f"₹{valid_df['price'].max():,.0f}"],
                ['Average Price', f"₹{valid_df['price'].mean():,.0f}"],
                ['Median Price', f"₹{valid_df['price'].median():,.0f}"],
                ['Price Range', f"₹{valid_df['price'].max() - valid_df['price'].min():,.0f}"]
            ]
            
            if 'rating' in valid_df.columns and valid_df['rating'].notna().any():
                stats_data.append(['Avg Rating', f"{valid_df['rating'].mean():.2f}/5.0"])
            
            table = ax4.table(cellText=stats_data[1:], colLabels=stats_data[0],
                            cellLoc='left', loc='center',
                            colWidths=[0.5, 0.5])
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            
            # Style table header
            for i in range(len(stats_data[0])):
                table[(0, i)].set_facecolor('#366092')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            ax4.set_title('Price Statistics Summary', fontweight='bold', pad=10)
            
            # Overall title
            date_str = datetime.now().strftime('%B %d, %Y')
            fig.suptitle(f'Price Comparison Dashboard - {date_str}',
                         fontsize=14, fontweight='bold', y=0.98)
            
            # Generate filename if not provided
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(self.output_dir, f"summary_dashboard_{timestamp}.png")
            elif not os.path.isabs(output_path):
                output_path = os.path.join(self.output_dir, output_path)
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save with high DPI
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            msg = f"✓ Summary dashboard saved to {output_path}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            msg = f"✗ Summary dashboard failed: {str(e)}"
            logger.error(msg, exc_info=True)
            plt.close()
            return False, msg
    
    def create_rating_vs_price_scatter(self, df: pd.DataFrame, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create scatter plot showing relationship between rating and price (optional).
        
        Args:
            df: DataFrame with product data
            output_path: Output file path (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        required_cols = ['price', 'rating', 'source']
        is_valid, error_msg = self._check_data_validity(df, required_cols)
        if not is_valid:
            msg = f"✗ Rating vs price scatter plot failed: {error_msg}"
            logger.warning(msg)
            return False, msg
        
        try:
            # Filter valid data
            valid_df = df[
                df['price'].notna() & (df['price'] > 0) &
                df['rating'].notna() & (df['rating'] > 0)
            ].copy()
            
            if valid_df.empty:
                msg = "✗ Rating vs price scatter plot failed: No valid rating/price data"
                logger.warning(msg)
                return False, msg
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot by source
            for source in valid_df['source'].unique():
                source_data = valid_df[valid_df['source'] == source]
                ax.scatter(source_data['price'], source_data['rating'],
                          label=source, color=self._get_source_color(source),
                          alpha=0.6, s=100, edgecolors='black', linewidth=0.5)
            
            ax.set_xlabel('Price (₹)', fontsize=11, fontweight='bold')
            ax.set_ylabel('Rating', fontsize=11, fontweight='bold')
            ax.set_title('Rating vs Price Comparison', fontsize=13, fontweight='bold', pad=15)
            ax.legend()
            ax.grid(alpha=0.3)
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
            
            plt.tight_layout()
            
            # Generate filename if not provided
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(self.output_dir, f"rating_vs_price_{timestamp}.png")
            elif not os.path.isabs(output_path):
                output_path = os.path.join(self.output_dir, output_path)
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            msg = f"✓ Rating vs price scatter plot saved to {output_path}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            msg = f"✗ Rating vs price scatter plot failed: {str(e)}"
            logger.error(msg, exc_info=True)
            plt.close()
            return False, msg
    
    def create_all_charts(self, df: pd.DataFrame) -> Dict[str, Tuple[bool, str]]:
        """
        Create all available charts.
        
        Args:
            df: DataFrame with product data
            
        Returns:
            Dictionary with chart names and (success, message) tuples
        """
        results = {}
        
        logger.info("Creating all visualization charts...")
        
        results['price_comparison'] = self.create_price_comparison_chart(df)
        results['price_distribution'] = self.create_price_distribution_chart(df)
        results['summary_dashboard'] = self.create_summary_dashboard(df)
        
        # Optional: rating vs price scatter
        if 'rating' in df.columns:
            results['rating_vs_price'] = self.create_rating_vs_price_scatter(df)
        
        logger.info("All charts created")
        return results
    
    # Backward compatibility methods
    def plot_price_comparison(self, df: pd.DataFrame, filename: Optional[str] = None):
        """Backward compatibility wrapper."""
        output_path = None
        if filename:
            output_path = os.path.join(self.output_dir, filename)
        success, msg = self.create_price_comparison_chart(df, output_path)
        if not success:
            logger.warning(msg)
    
    def plot_price_distribution(self, df: pd.DataFrame, filename: Optional[str] = None):
        """Backward compatibility wrapper."""
        output_path = None
        if filename:
            output_path = os.path.join(self.output_dir, filename)
        success, msg = self.create_price_distribution_chart(df, output_path)
        if not success:
            logger.warning(msg)
    
    def create_all_plots(self, df: pd.DataFrame):
        """Backward compatibility wrapper."""
        self.create_all_charts(df)
