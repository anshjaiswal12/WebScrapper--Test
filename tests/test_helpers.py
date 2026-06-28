"""
Unit tests for helper functions.
"""
import unittest
from src.utils.helpers import clean_price, clean_text, extract_rating, extract_reviews_count


class TestHelpers(unittest.TestCase):
    """Test cases for helper functions."""
    
    def test_clean_price(self):
        """Test price cleaning function."""
        self.assertEqual(clean_price("₹45,999"), 45999.0)
        self.assertEqual(clean_price("45,999"), 45999.0)
        self.assertEqual(clean_price("₹45,999.50"), 45999.5)
        self.assertIsNone(clean_price(""))
        self.assertIsNone(clean_price("N/A"))
    
    def test_clean_text(self):
        """Test text cleaning function."""
        self.assertEqual(clean_text("  hello   world  "), "hello world")
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text("test\n\nstring"), "test string")
    
    def test_extract_rating(self):
        """Test rating extraction function."""
        self.assertEqual(extract_rating("4.5 out of 5"), 4.5)
        self.assertEqual(extract_rating("4.5"), 4.5)
        self.assertIsNone(extract_rating(""))
    
    def test_extract_reviews_count(self):
        """Test reviews count extraction function."""
        self.assertEqual(extract_reviews_count("(1,234)"), 1234)
        self.assertEqual(extract_reviews_count("1,234 reviews"), 1234)
        self.assertIsNone(extract_reviews_count(""))


if __name__ == '__main__':
    unittest.main()

