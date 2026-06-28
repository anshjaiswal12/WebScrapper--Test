"""Unit tests for the comparison service."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.comparison_service import run_comparison


class TestComparisonService(unittest.TestCase):
    """Tests for the comparison workflow."""

    def test_demo_comparison(self):
        result = run_comparison(
            query='HP Pavilion laptop',
            max_results=5,
            use_demo=True,
            create_charts=True,
        )
        self.assertFalse(result.dataframe.empty)
        self.assertTrue(result.used_demo_data)
        self.assertGreater(len(result.comparisons), 0)
        self.assertIsNotNone(result.csv_path)
        self.assertTrue(os.path.exists(result.csv_path))

    def test_demo_query_filter(self):
        result = run_comparison(
            query='iPhone 15',
            max_results=5,
            use_demo=True,
            create_charts=False,
        )
        names = ' '.join(result.dataframe['product_name'].astype(str).tolist()).lower()
        self.assertIn('iphone', names)


if __name__ == '__main__':
    unittest.main()
