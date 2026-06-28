"""Sample product data for demo mode and offline testing."""
from typing import List, Dict


def get_demo_products(query: str = "") -> List[Dict]:
    """
    Return realistic sample products for demonstration.

    Args:
        query: Optional search query used to lightly filter demo results.
    """
    products = [
        {
            'source': 'Amazon',
            'product_name': 'HP Pavilion 15-eg2007TU Laptop Intel Core i5 12th Gen',
            'price': 45990.0,
            'rating': 4.2,
            'url': 'https://www.amazon.in/dp/B08XYZ123',
            'in_stock': True,
            'sponsored': False,
        },
        {
            'source': 'Flipkart',
            'product_name': 'HP Pavilion 15-eg2007TU Intel Core i5 12th Gen Laptop',
            'price': 44990.0,
            'rating': 4.3,
            'url': 'https://www.flipkart.com/hp-pavilion-15',
            'in_stock': True,
            'sponsored': False,
        },
        {
            'source': 'Amazon',
            'product_name': 'Apple iPhone 15 128GB Blue',
            'price': 69999.0,
            'rating': 4.5,
            'url': 'https://www.amazon.in/dp/B0ABC123',
            'in_stock': True,
            'sponsored': False,
        },
        {
            'source': 'Flipkart',
            'product_name': 'Apple iPhone 15 128GB Blue',
            'price': 68490.0,
            'rating': 4.4,
            'url': 'https://www.flipkart.com/apple-iphone-15',
            'in_stock': True,
            'sponsored': False,
        },
        {
            'source': 'Amazon',
            'product_name': 'Sony WH-1000XM5 Wireless Noise Cancelling Headphones',
            'price': 24990.0,
            'rating': 4.6,
            'url': 'https://www.amazon.in/dp/B0XYZ789',
            'in_stock': True,
            'sponsored': False,
        },
        {
            'source': 'Flipkart',
            'product_name': 'Sony WH-1000XM5 Noise Cancelling Headphones',
            'price': 23990.0,
            'rating': 4.5,
            'url': 'https://www.flipkart.com/sony-wh-1000xm5',
            'in_stock': True,
            'sponsored': False,
        },
        {
            'source': 'Amazon',
            'product_name': 'Dell Inspiron 15 3000 Laptop Intel Core i3',
            'price': 38990.0,
            'rating': 4.0,
            'url': 'https://www.amazon.in/dp/DEL123',
            'in_stock': True,
            'sponsored': False,
        },
        {
            'source': 'Flipkart',
            'product_name': 'Lenovo IdeaPad 3 Laptop AMD Ryzen 5',
            'price': 34990.0,
            'rating': 3.9,
            'url': 'https://www.flipkart.com/lenovo-ideapad-3',
            'in_stock': True,
            'sponsored': False,
        },
    ]

    if not query:
        return products

    query_lower = query.lower()
    filtered = [
        p for p in products
        if any(token in p['product_name'].lower() for token in query_lower.split())
    ]
    return filtered or products
