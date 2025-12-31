"""
Example usage script demonstrating how to use individual components.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.flipkart_scraper import FlipkartScraper
from src.utils.data_processor import DataProcessor
from src.utils.visualizer import Visualizer
from src.utils.logger import setup_logger

logger = setup_logger()


def example_amazon_scraping():
    """Example: Scrape Amazon India."""
    logger.info("Example: Amazon Scraping")
    
    scraper = AmazonScraper(headless=True)
    try:
        products = scraper.search("HP Pavilion laptop", max_results=5)
        
        for product in products:
            print(f"\nTitle: {product.get('title', 'N/A')}")
            print(f"Price: ₹{product.get('price', 'N/A')}")
            print(f"Rating: {product.get('rating', 'N/A')}")
            print(f"URL: {product.get('url', 'N/A')}")
        
    finally:
        scraper.close()


def example_flipkart_scraping():
    """Example: Scrape Flipkart."""
    logger.info("Example: Flipkart Scraping")
    
    scraper = FlipkartScraper(headless=True)
    try:
        products = scraper.search("HP Pavilion laptop", max_results=5)
        
        for product in products:
            print(f"\nTitle: {product.get('title', 'N/A')}")
            print(f"Price: ₹{product.get('price', 'N/A')}")
            print(f"Rating: {product.get('rating', 'N/A')}")
            print(f"URL: {product.get('url', 'N/A')}")
        
    finally:
        scraper.close()


def example_data_processing():
    """Example: Process and export data."""
    logger.info("Example: Data Processing")
    
    # Sample data
    sample_products = [
        {
            'title': 'HP Pavilion 15',
            'price': 45999.0,
            'rating': 4.5,
            'source': 'Amazon India',
            'url': 'https://example.com'
        },
        {
            'title': 'HP Pavilion 14',
            'price': 42999.0,
            'rating': 4.3,
            'source': 'Flipkart',
            'url': 'https://example.com'
        }
    ]
    
    processor = DataProcessor()
    df = processor.combine_data([sample_products])
    
    # Filter and sort
    filtered_df = processor.filter_data(min_price=40000, max_price=50000)
    sorted_df = processor.sort_data(by='price', ascending=True)
    
    # Export
    processor.export_to_csv('data/output/csv/example.csv', sorted_df)
    processor.export_to_excel('data/output/excel/example.xlsx', sorted_df)
    
    # Print summary
    summary = processor.get_summary_stats()
    print(f"\nSummary: {summary}")


def example_visualization():
    """Example: Create visualizations."""
    logger.info("Example: Visualization")
    
    import pandas as pd
    
    # Sample data
    data = {
        'title': ['HP Pavilion 15', 'HP Pavilion 14', 'HP Pavilion 13'],
        'price': [45999, 42999, 49999],
        'rating': [4.5, 4.3, 4.7],
        'source': ['Amazon India', 'Flipkart', 'Amazon India']
    }
    df = pd.DataFrame(data)
    
    visualizer = Visualizer()
    visualizer.plot_price_comparison(df, 'example_price_comparison.png')
    visualizer.plot_price_distribution(df, 'example_price_distribution.png')


if __name__ == "__main__":
    print("=" * 60)
    print("Example Usage Scripts")
    print("=" * 60)
    print("\nUncomment the function you want to run:")
    print("# example_amazon_scraping()")
    print("# example_flipkart_scraping()")
    print("# example_data_processing()")
    print("# example_visualization()")
    print("\nNote: Make sure ChromeDriver is installed for scraping examples.")

