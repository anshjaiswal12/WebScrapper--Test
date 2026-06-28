"""
Example usage script demonstrating how to use individual components.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.comparison_service import run_comparison
from src.utils.logger import setup_logger

logger = setup_logger()


def example_demo_comparison():
    """Run a full comparison using demo data."""
    logger.info("Example: Demo comparison")
    result = run_comparison(
        query='HP Pavilion laptop',
        max_results=5,
        use_demo=True,
        create_charts=True,
    )
    print(f"Products: {len(result.dataframe)}")
    print(f"Cross-site matches: {len(result.comparisons)}")
    print(f"CSV: {result.csv_path}")
    print(f"Excel: {result.excel_path}")


if __name__ == '__main__':
    print('=' * 60)
    print('Example Usage')
    print('=' * 60)
    example_demo_comparison()
