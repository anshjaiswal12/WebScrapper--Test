"""
Main orchestrator for the Price Comparison Tool.

This module coordinates the entire scraping workflow:
1. Configuration initialization
2. User input collection
3. Web scraping (Amazon & Flipkart)
4. Data processing and validation
5. Export generation (CSV, Excel)
6. Visualization creation
7. Summary reporting
"""
import sys
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.flipkart_scraper import FlipkartScraper
from src.utils.data_processor import DataProcessor
from src.utils.visualizer import Visualizer
from src.utils.comparison_engine import ComparisonEngine
from src.utils.comparison_visualizer import ComparisonVisualizer
from src.utils.logger import setup_logger
from config.settings import (
    SEARCH_QUERY, MAX_ITEMS_PER_SITE, SITES,
    CSV_OUTPUT_DIR, EXCEL_OUTPUT_DIR, IMAGES_OUTPUT_DIR,
    MIN_PRICE, MAX_PRICE, MIN_RATING
)

logger = setup_logger()

# ANSI color codes for colored console output
class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'
    CYAN = '\033[96m'


def print_colored(message: str, color: str = Colors.BLUE):
    """Print colored message to console."""
    print(f"{color}{message}{Colors.END}")


def print_header():
    """Display welcome message and project info."""
    print("\n" + "=" * 70)
    print_colored("Welcome to Laptop Price Comparison Tool", Colors.BOLD + Colors.CYAN)
    print("=" * 70)
    print_colored("This tool compares laptop prices across Amazon and Flipkart", Colors.BLUE)
    print_colored("Powered by Python Web Scraping", Colors.BLUE)
    print("=" * 70 + "\n")


def get_user_input(default_query: str = "HP Pavilion laptop") -> str:
    """
    Get user input for search query.
    
    Args:
        default_query: Default search query if user presses Enter
        
    Returns:
        Search query string
    """
    try:
        user_input = input(
            f"Enter laptop model to search (or press Enter for '{default_query}'): "
        ).strip()
        
        if not user_input:
            query = default_query
            print_colored(f"Using default query: {query}", Colors.YELLOW)
        else:
            query = user_input
            print_colored(f"Search query: {query}", Colors.GREEN)
        
        return query
        
    except (EOFError, KeyboardInterrupt):
        print_colored("\n\nOperation cancelled by user.", Colors.RED)
        sys.exit(0)
    except Exception as e:
        logger.warning(f"Error getting user input: {e}, using default")
        return default_query


def scrape_amazon(query: str, max_results: int = 10) -> Tuple[List[Dict], bool]:
    """
    Scrape products from Amazon.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        Tuple of (products list, success status)
    """
    print_colored("  📦 Scraping Amazon India...", Colors.BLUE)
    start_time = time.time()
    
    try:
        scraper = AmazonScraper(search_query=query, max_results=max_results)
        products = scraper.scrape()
        
        elapsed = time.time() - start_time
        if products:
            print_colored(
                f"  ✓ Amazon: Found {len(products)} products in {elapsed:.1f}s", 
                Colors.GREEN
            )
            logger.info(f"Amazon scraping completed: {len(products)} products in {elapsed:.1f}s")
            return products, True
        else:
            print_colored("  ⚠ Amazon: No products found", Colors.YELLOW)
            logger.warning("Amazon scraping returned no products")
            return [], True  # Success but empty
            
    except Exception as e:
        elapsed = time.time() - start_time
        print_colored(f"  ✗ Amazon: Error - {str(e)}", Colors.RED)
        logger.error(f"Amazon scraping failed after {elapsed:.1f}s: {e}", exc_info=True)
        return [], False


def scrape_flipkart(query: str, max_results: int = 10) -> Tuple[List[Dict], bool]:
    """
    Scrape products from Flipkart.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        Tuple of (products list, success status)
    """
    print_colored("  🛒 Scraping Flipkart...", Colors.BLUE)
    start_time = time.time()
    
    try:
        scraper = FlipkartScraper(search_query=query, max_results=max_results)
        products = scraper.scrape()
        
        elapsed = time.time() - start_time
        if products:
            print_colored(
                f"  ✓ Flipkart: Found {len(products)} products in {elapsed:.1f}s", 
                Colors.GREEN
            )
            logger.info(f"Flipkart scraping completed: {len(products)} products in {elapsed:.1f}s")
            return products, True
        else:
            print_colored("  ⚠ Flipkart: No products found", Colors.YELLOW)
            logger.warning("Flipkart scraping returned no products")
            return [], True  # Success but empty
            
    except Exception as e:
        elapsed = time.time() - start_time
        print_colored(f"  ✗ Flipkart: Error - {str(e)}", Colors.RED)
        logger.error(f"Flipkart scraping failed after {elapsed:.1f}s: {e}", exc_info=True)
        return [], False


def validate_scraped_data(amazon_data: List[Dict], flipkart_data: List[Dict]) -> bool:
    """
    Validate that we have at least some data to work with.
    
    Args:
        amazon_data: Amazon products list
        flipkart_data: Flipkart products list
        
    Returns:
        True if data is valid, False otherwise
    """
    total_products = len(amazon_data) + len(flipkart_data)
    
    if total_products == 0:
        print_colored("\n⚠ No products found from any source!", Colors.YELLOW)
        print_colored("Possible reasons:", Colors.YELLOW)
        print_colored("  - Search query returned no results", Colors.YELLOW)
        print_colored("  - Websites may have blocked the scraper", Colors.YELLOW)
        print_colored("  - Network connectivity issues", Colors.YELLOW)
        print_colored("  - Website structure may have changed", Colors.YELLOW)
        logger.warning("No products found from any source")
        return False
    
    # Check for required fields
    all_products = amazon_data + flipkart_data
    valid_products = [
        p for p in all_products
        if p.get('price') and (p.get('product_name') or p.get('title'))
    ]
    
    if not valid_products:
        print_colored("\n⚠ Products found but missing required fields (price/name)", Colors.YELLOW)
        logger.warning("Products found but missing required fields")
        return False
    
    return True


def process_data(amazon_data: List[Dict], flipkart_data: List[Dict]) -> Optional[pd.DataFrame]:
    """
    Process and combine scraped data.
    
    Args:
        amazon_data: Amazon products list
        flipkart_data: Flipkart products list
        
    Returns:
        Combined DataFrame or None if processing fails
    """
    print_colored("  🔄 Combining data from all sources...", Colors.BLUE)
    
    try:
        processor = DataProcessor()
        df = processor.combine_scraped_data(amazon_data, flipkart_data)
        
        if df.empty:
            print_colored("  ✗ Data processing failed: Empty DataFrame", Colors.RED)
            return None
        
        # Clean product names
        print_colored("  🧹 Cleaning and normalizing product names...", Colors.BLUE)
        df = processor.clean_product_names(df)
        
        # Apply filters
        if MIN_PRICE > 0 or MAX_PRICE < float('inf') or MIN_RATING > 0:
            print_colored("  🔍 Applying filters...", Colors.BLUE)
            processor.df = df
            df = processor.filter_data(MIN_PRICE, MAX_PRICE, MIN_RATING)
            processor.df = df
        
        # Sort by price
        df = processor.sort_data(by='price', ascending=True)
        
        print_colored(f"  ✓ Processed {len(df)} products", Colors.GREEN)
        logger.info(f"Data processing completed: {len(df)} products")
        
        return df
        
    except Exception as e:
        print_colored(f"  ✗ Data processing error: {str(e)}", Colors.RED)
        logger.error(f"Data processing failed: {e}", exc_info=True)
        return None


def export_data(df) -> Tuple[Optional[str], Optional[str]]:
    """
    Export data to CSV and Excel.
    
    Args:
        df: DataFrame to export
        
    Returns:
        Tuple of (csv_path, excel_path)
    """
    print_colored("  💾 Generating reports...", Colors.BLUE)
    
    try:
        processor = DataProcessor()
        processor.df = df
        
        # Generate filenames with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"price_comparison_{timestamp}.csv"
        excel_filename = f"price_comparison_{timestamp}.xlsx"
        
        # Export CSV
        csv_success, csv_msg = processor.export_to_csv(csv_filename, df)
        if csv_success:
            csv_path = os.path.join(CSV_OUTPUT_DIR, csv_filename)
            print_colored(f"  ✓ CSV exported: {csv_path}", Colors.GREEN)
        else:
            print_colored(f"  ✗ CSV export failed: {csv_msg}", Colors.RED)
            csv_path = None
        
        # Export Excel
        excel_success, excel_msg = processor.export_to_excel(excel_filename, df)
        if excel_success:
            excel_path = os.path.join(EXCEL_OUTPUT_DIR, excel_filename)
            print_colored(f"  ✓ Excel exported: {excel_path}", Colors.GREEN)
        else:
            print_colored(f"  ✗ Excel export failed: {excel_msg}", Colors.RED)
            excel_path = None
        
        return csv_path, excel_path
        
    except Exception as e:
        print_colored(f"  ✗ Export error: {str(e)}", Colors.RED)
        logger.error(f"Export failed: {e}", exc_info=True)
        return None, None


def create_charts(df) -> Dict[str, str]:
    """
    Create visualization charts.
    
    Args:
        df: DataFrame with product data
        
    Returns:
        Dictionary with chart paths
    """
    print_colored("  📈 Creating visualizations...", Colors.BLUE)
    
    try:
        visualizer = Visualizer(output_dir=IMAGES_OUTPUT_DIR)
        results = visualizer.create_all_charts(df)
        
        chart_paths = {}
        for chart_name, (success, msg) in results.items():
            if success:
                # Extract path from message
                if "saved to" in msg:
                    path = msg.split("saved to ")[1]
                    chart_paths[chart_name] = path
                    print_colored(f"  ✓ {chart_name.replace('_', ' ').title()}: Created", Colors.GREEN)
                else:
                    print_colored(f"  ✓ {chart_name.replace('_', ' ').title()}: {msg}", Colors.GREEN)
            else:
                print_colored(f"  ✗ {chart_name.replace('_', ' ').title()}: {msg}", Colors.RED)
        
        return chart_paths
        
    except Exception as e:
        print_colored(f"  ✗ Visualization error: {str(e)}", Colors.RED)
        logger.error(f"Visualization failed: {e}", exc_info=True)
        return {}


def print_summary(df) -> None:
    """
    Display summary report.
    
    Args:
        df: DataFrame with product data
    """
    try:
        processor = DataProcessor()
        processor.df = df
        
        # Generate summary report
        report = processor.generate_summary_report(df)
        
        print("\n" + "=" * 70)
        print_colored("SUMMARY REPORT", Colors.BOLD + Colors.CYAN)
        print("=" * 70)
        print(report)
        
        # Calculate statistics
        stats = processor.calculate_price_statistics(df)
        
        if stats.get('lowest_price'):
            print("\n" + "=" * 70)
            print_colored("🏆 BEST DEAL RECOMMENDATION", Colors.BOLD + Colors.GREEN)
            print("=" * 70)
            lowest = stats['lowest_price']
            print_colored(f"Product: {lowest['product_name']}", Colors.BOLD)
            print_colored(f"Price: ₹{lowest['price']:,.0f}", Colors.GREEN)
            print_colored(f"Source: {lowest['source']}", Colors.BLUE)
            if lowest.get('url'):
                print_colored(f"URL: {lowest['url']}", Colors.CYAN)
        
        if stats.get('best_rated'):
            print("\n" + "=" * 70)
            print_colored("⭐ BEST RATED PRODUCT", Colors.BOLD + Colors.YELLOW)
            print("=" * 70)
            best = stats['best_rated']
            print_colored(f"Product: {best['product_name']}", Colors.BOLD)
            print_colored(f"Rating: {best['rating']}/5.0", Colors.YELLOW)
            print_colored(f"Price: ₹{best['price']:,.0f}", Colors.GREEN)
            print_colored(f"Source: {best['source']}", Colors.BLUE)
        
        # Recommendations
        print("\n" + "=" * 70)
        print_colored("💡 RECOMMENDATIONS", Colors.BOLD + Colors.CYAN)
        print("=" * 70)
        
        if stats.get('percentage_savings', 0) > 10:
            print_colored(
                f"  • Price difference of {stats['percentage_savings']:.1f}% found - "
                "compare carefully!", 
                Colors.YELLOW
            )
        
        if stats.get('lowest_price') and stats.get('highest_price'):
            price_diff = stats['highest_price']['price'] - stats['lowest_price']['price']
            if price_diff > 10000:
                print_colored(
                    f"  • Significant price variation (₹{price_diff:,.0f}) - "
                    "check product specifications", 
                    Colors.YELLOW
                )
        
        print_colored("  • Always verify product specifications match before purchasing", Colors.BLUE)
        print_colored("  • Check seller ratings and return policies", Colors.BLUE)
        print_colored("  • Consider delivery time and shipping costs", Colors.BLUE)
        
    except Exception as e:
        print_colored(f"  ✗ Error generating summary: {str(e)}", Colors.RED)
        logger.error(f"Summary generation failed: {e}", exc_info=True)


def print_output_locations(csv_path: Optional[str], excel_path: Optional[str], 
                          chart_paths: Dict[str, str]) -> None:
    """
    Display output file locations.
    
    Args:
        csv_path: Path to CSV file
        excel_path: Path to Excel file
        chart_paths: Dictionary of chart paths
    """
    print("\n" + "=" * 70)
    print_colored("📁 OUTPUT FILES", Colors.BOLD + Colors.CYAN)
    print("=" * 70)
    
    if csv_path:
        print_colored(f"  CSV Report: {os.path.abspath(csv_path)}", Colors.GREEN)
    else:
        print_colored("  CSV Report: Not generated", Colors.RED)
    
    if excel_path:
        print_colored(f"  Excel Report: {os.path.abspath(excel_path)}", Colors.GREEN)
    else:
        print_colored("  Excel Report: Not generated", Colors.RED)
    
    if chart_paths:
        print_colored("\n  Visualizations:", Colors.BLUE)
        for chart_name, path in chart_paths.items():
            print_colored(f"    • {chart_name.replace('_', ' ').title()}: {os.path.abspath(path)}", 
                         Colors.CYAN)
    else:
        print_colored("  Visualizations: Not generated", Colors.RED)
    
    print("=" * 70 + "\n")


def main(query: Optional[str] = None, max_results: Optional[int] = None, 
         output_dir: Optional[str] = None, no_visualize: bool = False, quiet_mode: bool = False):
    """
    Main execution function orchestrating the entire workflow.
    
    Args:
        query: Optional search query (if None, will prompt user)
        max_results: Optional max results per site (default: from settings)
        output_dir: Optional custom output directory
        no_visualize: Skip visualization if True
        quiet_mode: Minimal output if True
    """
    overall_start_time = time.time()
    
    # Configure logging based on quiet mode
    if quiet_mode:
        # Disable console output for logger, keep file logging
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                logger.removeHandler(handler)
    
    try:
        # 1. Setup
        if not quiet_mode:
            print_header()
        
        # Get user input if not provided
        if query is None:
            query = get_user_input(SEARCH_QUERY)
        
        if max_results is None:
            max_results = MAX_ITEMS_PER_SITE
        
        # Update output directories if custom path provided
        if output_dir:
            import config.settings as settings
            base_dir = output_dir
            settings.CSV_OUTPUT_DIR = os.path.join(base_dir, 'csv')
            settings.EXCEL_OUTPUT_DIR = os.path.join(base_dir, 'excel')
            settings.IMAGES_OUTPUT_DIR = os.path.join(base_dir, 'images')
            # Create subdirectories
            os.makedirs(settings.CSV_OUTPUT_DIR, exist_ok=True)
            os.makedirs(settings.EXCEL_OUTPUT_DIR, exist_ok=True)
            os.makedirs(settings.IMAGES_OUTPUT_DIR, exist_ok=True)
        
        if not quiet_mode:
            print(f"\n{Colors.BOLD}Configuration:{Colors.END}")
            print_colored(f"  Search Query: {query}", Colors.BLUE)
            print_colored(f"  Max Results per Site: {max_results}", Colors.BLUE)
            print_colored(f"  Enabled Sites: {', '.join([s for s, config in SITES.items() if config.get('enabled')])}", 
                         Colors.BLUE)
            if no_visualize:
                print_colored("  Visualization: Skipped (--no-visualize)", Colors.YELLOW)
            print()
        
        # 2. Scraping phase
        if not quiet_mode:
            print_colored("🔍 Starting web scraping...", Colors.BOLD + Colors.CYAN)
            print()
        
        amazon_results, amazon_success = scrape_amazon(query, max_results)
        flipkart_results, flipkart_success = scrape_flipkart(query, max_results)
        
        scraping_time = time.time() - overall_start_time
        if not quiet_mode:
            print_colored(f"\n✓ Scraping completed in {scraping_time:.1f}s\n", Colors.GREEN)
        logger.info(f"Scraping completed in {scraping_time:.1f}s")
        
        # Validate data
        if not validate_scraped_data(amazon_results, flipkart_results):
            if not quiet_mode:
                print_colored("\n✗ Cannot proceed without valid data. Exiting.", Colors.RED)
            logger.error("No valid data to process")
            sys.exit(1)
        
        # 3. Data processing and comparison
        if not quiet_mode:
            print_colored("📊 Processing data and comparing prices...", Colors.BOLD + Colors.CYAN)
            print()
        
        # Combine all products
        all_products = amazon_results + flipkart_results
        
        if not all_products:
            if not quiet_mode:
                print_colored("\n✗ No products found. Exiting.", Colors.RED)
            logger.error("No products to process")
            sys.exit(1)
        
        # Use comparison engine to find same products
        comparison_engine = ComparisonEngine()
        comparisons = comparison_engine.compare_same_products(all_products)
        
        if not comparisons:
            if not quiet_mode:
                print_colored("⚠ No matching products found across sites.", Colors.YELLOW)
                print_colored("Showing all products instead...", Colors.YELLOW)
            # Fallback to regular processing
            combined_df = process_data(amazon_results, flipkart_results)
            if combined_df is None or combined_df.empty:
                if not quiet_mode:
                    print_colored("\n✗ Data processing failed. Exiting.", Colors.RED)
                logger.error("Data processing returned empty DataFrame")
                sys.exit(1)
        else:
            # Display focused comparison
            if not quiet_mode:
                print_colored("\n" + "=" * 80, Colors.BOLD + Colors.CYAN)
                print_colored("💰 PRICE COMPARISON RESULTS", Colors.BOLD + Colors.CYAN)
                print_colored("=" * 80, Colors.BOLD + Colors.CYAN)
            
            comparison_output = comparison_engine.format_comparison_output(comparisons)
            if not quiet_mode:
                print(comparison_output)
            else:
                # In quiet mode, just log the summary
                logger.info(f"Found {len(comparisons)} products available on multiple sites")
            
            # Convert comparisons to DataFrame for export
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
                        'product_name': product_name,
                        'model_number': comp.get('model_number', ''),
                        'source': source,
                        'price': price,
                        'rating': info.get('rating'),
                        'in_stock': info.get('in_stock', True),
                        'url': info.get('url', ''),
                        'is_best_price': is_best
                    })
            
            combined_df = pd.DataFrame(rows) if rows else pd.DataFrame()
        
        if not quiet_mode:
            print()
        
        # 4. Export phase
        if not quiet_mode:
            print_colored("💾 Generating reports...", Colors.BOLD + Colors.CYAN)
            print()
        
        csv_path, excel_path = export_data(combined_df)
        
        if not quiet_mode:
            print()
        
        # 5. Visualization
        chart_paths = {}
        if not no_visualize:
            if not quiet_mode:
                print_colored("📈 Creating visualizations...", Colors.BOLD + Colors.CYAN)
                print()
            
            # Create focused same-product comparison chart if we have comparisons
            if comparisons:
                comp_visualizer = ComparisonVisualizer()
                success, msg = comp_visualizer.create_same_product_comparison(comparisons)
                if success:
                    chart_paths['same_product_comparison'] = msg.split('saved to ')[1] if 'saved to ' in msg else ''
                    if not quiet_mode:
                        print_colored(f"  ✓ Same-product comparison chart created", Colors.GREEN)
            
            # Also create regular charts
            if not combined_df.empty:
                regular_charts = create_charts(combined_df)
                chart_paths.update(regular_charts)
            
            if not quiet_mode:
                print()
        else:
            if not quiet_mode:
                print_colored("⏭ Skipping visualization (--no-visualize flag)", Colors.YELLOW)
                print()
            logger.info("Visualization skipped due to --no-visualize flag")
        
        # 6. Summary (only if we have comparisons)
        if comparisons:
            if not quiet_mode:
                print_colored("📋 COMPARISON SUMMARY", Colors.BOLD + Colors.CYAN)
                print_colored("=" * 80, Colors.BOLD + Colors.CYAN)
                print_colored(f"Found {len(comparisons)} products available on multiple sites", Colors.GREEN)
                
                total_savings = sum(c.get('savings', {}).get('price_difference', 0) for c in comparisons if c.get('savings'))
                if total_savings > 0:
                    print_colored(f"Total potential savings: ₹{total_savings:,.0f}", Colors.GREEN)
                print()
            else:
                # In quiet mode, print only essential summary
                summary_report = DataProcessor().generate_summary_report(combined_df)
                print(f"\n{Colors.BOLD}{Colors.GREEN}Analysis Complete!{Colors.END}")
                print(summary_report)
        else:
            if not quiet_mode:
                print_summary(combined_df)
            else:
                # In quiet mode, print minimal summary
                print(f"\n{Colors.BOLD}{Colors.GREEN}Analysis Complete!{Colors.END}")
                print(f"Total products: {len(combined_df)}")
        
        # 7. Output locations
        print_output_locations(csv_path, excel_path, chart_paths)
        
        # Final timing
        total_time = time.time() - overall_start_time
        if not quiet_mode:
            print_colored(f"✨ Process completed successfully in {total_time:.1f} seconds!", 
                         Colors.BOLD + Colors.GREEN)
            print()
        else:
            # In quiet mode, just show essential info
            print_colored(f"✓ Completed: {len(combined_df)} products in {total_time:.1f}s", Colors.GREEN)
        
        logger.info(f"Main execution completed successfully in {total_time:.1f}s")
        
    except KeyboardInterrupt:
        if not quiet_mode:
            print_colored("\n\n⚠ Operation cancelled by user.", Colors.RED)
        logger.warning("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        if not quiet_mode:
            print_colored(f"\n\n✗ Fatal error: {str(e)}", Colors.RED)
            print_colored("Check logs/scraper.log for details.", Colors.YELLOW)
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
