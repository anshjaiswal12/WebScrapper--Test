"""
Main entry point for the Price Comparison Web Scraper.
"""
import json
import os
import sys
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.flipkart_scraper import FlipkartScraper
from src.utils.data_processor import DataProcessor
from src.utils.visualizer import Visualizer
from src.utils.logger import setup_logger

logger = setup_logger()


def load_config(config_path: str = "config/config.json") -> Dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise


def scrape_products(config: Dict) -> List[List[Dict]]:
    """Scrape products from all enabled sites."""
    all_products = []
    search_query = config.get('search_query', 'HP Pavilion laptop')
    max_results = config.get('max_results', 20)

    if config.get('sites', {}).get('amazon', {}).get('enabled', False):
        try:
            logger.info("Starting Amazon scraper...")
            amazon_scraper = AmazonScraper(search_query=search_query, max_results=max_results)
            amazon_products = amazon_scraper.scrape()
            all_products.append(amazon_products)
            logger.info(f"Amazon: Found {len(amazon_products)} products")
        except Exception as e:
            logger.error(f"Error scraping Amazon: {e}")
            all_products.append([])

    if config.get('sites', {}).get('flipkart', {}).get('enabled', False):
        try:
            logger.info("Starting Flipkart scraper...")
            flipkart_scraper = FlipkartScraper(search_query=search_query, max_results=max_results)
            flipkart_products = flipkart_scraper.scrape()
            all_products.append(flipkart_products)
            logger.info(f"Flipkart: Found {len(flipkart_products)} products")
        except Exception as e:
            logger.error(f"Error scraping Flipkart: {e}")
            all_products.append([])

    return all_products


def main():
    """Main execution function."""
    try:
        logger.info("=" * 60)
        logger.info("Price Comparison Web Scraper - Starting")
        logger.info("=" * 60)
        
        # Load configuration
        config = load_config()
        
        # Scrape products
        products_list = scrape_products(config)
        
        # Process data
        processor = DataProcessor()
        df = processor.combine_data(products_list)
        
        if df.empty:
            logger.warning("No products found. Exiting.")
            return
        
        # Apply filters
        filters = config.get('filters', {})
        filtered_df = processor.filter_data(
            min_price=filters.get('min_price', 0),
            max_price=filters.get('max_price', 200000),
            min_rating=filters.get('min_rating', 0)
        )
        processor.df = filtered_df
        
        # Sort by price
        sorted_df = processor.sort_data(by='price', ascending=True)
        processor.df = sorted_df
        
        # Generate output filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_config = config.get('output', {})
        
        csv_filename = os.path.join(
            output_config.get('csv_path', 'output/csv'),
            f"price_comparison_{timestamp}.csv"
        )
        
        excel_filename = os.path.join(
            output_config.get('excel_path', 'output/excel'),
            f"price_comparison_{timestamp}.xlsx"
        )
        
        # Export data
        logger.info("Exporting data to CSV and Excel...")
        csv_success, csv_msg = processor.export_to_csv(csv_filename, sorted_df)
        excel_success, excel_msg = processor.export_to_excel(excel_filename, sorted_df)
        if not csv_success:
            logger.warning(csv_msg)
        if not excel_success:
            logger.warning(excel_msg)
        
        # Print summary
        summary = processor.get_summary_stats()
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total Products: {summary.get('total_products', 0)}")
        logger.info(f"Sources: {summary.get('sources', {})}")
        if 'price_stats' in summary:
            price_stats = summary['price_stats']
            logger.info(f"Price Range: ₹{price_stats.get('min', 0):,.0f} - ₹{price_stats.get('max', 0):,.0f}")
            logger.info(f"Average Price: ₹{price_stats.get('mean', 0):,.0f}")
        
        # Create visualizations
        logger.info("\nCreating visualizations...")
        visualizer = Visualizer(output_dir=output_config.get('images_path', 'data/output/images'))
        visualizer.create_all_charts(sorted_df)
        
        logger.info("\n" + "=" * 60)
        logger.info("Scraping completed successfully!")
        logger.info(f"CSV file: {csv_filename}")
        logger.info(f"Excel file: {excel_filename}")
        logger.info(f"Visualizations: {output_config.get('images_path', 'output/images')}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

