"""Core comparison workflow shared by CLI and Streamlit."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

from config.settings import (
    CSV_OUTPUT_DIR,
    EXCEL_OUTPUT_DIR,
    IMAGES_OUTPUT_DIR,
    MAX_ITEMS_PER_SITE,
    MIN_PRICE,
    MAX_PRICE,
    MIN_RATING,
    SITES,
)
from src.data.demo_products import get_demo_products
from src.scrapers.amazon_scraper import AmazonScraper
from src.scrapers.flipkart_scraper import FlipkartScraper
from src.utils.comparison_engine import ComparisonEngine
from src.utils.comparison_visualizer import ComparisonVisualizer
from src.utils.data_processor import DataProcessor
from src.utils.logger import setup_logger
from src.utils.visualizer import Visualizer

logger = setup_logger()


@dataclass
class ComparisonResult:
    """Structured output from a comparison run."""

    query: str
    dataframe: pd.DataFrame
    comparisons: List[Dict]
    stats: Dict
    csv_path: Optional[str] = None
    excel_path: Optional[str] = None
    chart_paths: Dict[str, str] = field(default_factory=dict)
    used_demo_data: bool = False
    messages: List[str] = field(default_factory=list)


def _ensure_output_dirs() -> None:
    for path in (CSV_OUTPUT_DIR, EXCEL_OUTPUT_DIR, IMAGES_OUTPUT_DIR):
        os.makedirs(path, exist_ok=True)


def _chrome_available() -> bool:
    """Check whether Chrome/Chromium is available for Selenium."""
    return any(
        shutil.which(binary)
        for binary in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser')
    )


def scrape_products(
    query: str,
    max_results: int,
    scrape_amazon: bool = True,
    scrape_flipkart: bool = True,
    use_demo: bool = False,
) -> Tuple[List[Dict], List[Dict], bool]:
    """
    Scrape or load demo products.

    Returns:
        Tuple of (amazon_products, flipkart_products, used_demo_data)
    """
    if use_demo:
        demo = get_demo_products(query)
        amazon = [p for p in demo if p['source'] == 'Amazon']
        flipkart = [p for p in demo if p['source'] == 'Flipkart']
        return amazon, flipkart, True

    amazon_products: List[Dict] = []
    flipkart_products: List[Dict] = []

    if scrape_amazon and SITES.get('amazon', {}).get('enabled', True):
        try:
            amazon_products = AmazonScraper(search_query=query, max_results=max_results).scrape()
        except Exception as exc:
            logger.error(f"Amazon scrape failed: {exc}")

    if scrape_flipkart and SITES.get('flipkart', {}).get('enabled', True):
        try:
            flipkart_products = FlipkartScraper(search_query=query, max_results=max_results).scrape()
        except Exception as exc:
            logger.error(f"Flipkart scrape failed: {exc}")

    if not amazon_products and not flipkart_products:
        demo = get_demo_products(query)
        amazon_products = [p for p in demo if p['source'] == 'Amazon']
        flipkart_products = [p for p in demo if p['source'] == 'Flipkart']
        return amazon_products, flipkart_products, True

    return amazon_products, flipkart_products, False


def _comparisons_to_dataframe(comparisons: List[Dict]) -> pd.DataFrame:
    rows = []
    for comp in comparisons:
        product_name = comp['product_name']
        prices = [
            info.get('price', float('inf'))
            for info in comp['sources'].values()
            if info.get('price')
        ]
        min_price = min(prices) if prices else float('inf')

        for source, info in comp['sources'].items():
            price = info.get('price', 0)
            is_best = price == min_price if price > 0 and min_price != float('inf') else False
            rows.append({
                'product_name': product_name,
                'model_number': comp.get('model_number', ''),
                'source': source,
                'price': price,
                'rating': info.get('rating'),
                'in_stock': info.get('in_stock', True),
                'url': info.get('url', ''),
                'is_best_price': is_best,
            })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def run_comparison(
    query: str,
    max_results: Optional[int] = None,
    scrape_amazon: bool = True,
    scrape_flipkart: bool = True,
    use_demo: Optional[bool] = None,
    create_charts: bool = True,
) -> ComparisonResult:
    """
    Execute the full comparison workflow.

    Args:
        query: Product search query.
        max_results: Max products per site.
        scrape_amazon: Whether to include Amazon.
        scrape_flipkart: Whether to include Flipkart.
        use_demo: Force demo data. Auto-detected when Chrome is unavailable if None.
        create_charts: Whether to generate chart images.
    """
    _ensure_output_dirs()
    messages: List[str] = []
    max_results = max_results or MAX_ITEMS_PER_SITE

    if use_demo is None:
        use_demo = os.getenv('DEMO_MODE', 'false').lower() in ('1', 'true', 'yes')
        if not use_demo and not _chrome_available():
            use_demo = True
            messages.append('Chrome not detected — using demo data.')

    amazon_data, flipkart_data, used_demo = scrape_products(
        query=query,
        max_results=max_results,
        scrape_amazon=scrape_amazon,
        scrape_flipkart=scrape_flipkart,
        use_demo=use_demo,
    )

    all_products = amazon_data + flipkart_data
    if not all_products:
        raise ValueError('No products found. Try a different search query or enable demo mode.')

    comparison_engine = ComparisonEngine()
    comparisons = comparison_engine.compare_same_products(all_products)

    processor = DataProcessor()
    if comparisons:
        dataframe = _comparisons_to_dataframe(comparisons)
        messages.append(f'Found {len(comparisons)} products on multiple sites.')
    else:
        dataframe = processor.combine_scraped_data(amazon_data, flipkart_data)
        dataframe = processor.clean_product_names(dataframe)
        processor.df = dataframe
        if MIN_PRICE > 0 or MAX_PRICE < float('inf') or MIN_RATING > 0:
            dataframe = processor.filter_data(MIN_PRICE, MAX_PRICE, MIN_RATING)
            processor.df = dataframe
        dataframe = processor.sort_data(by='price', ascending=True)
        processor.df = dataframe
        messages.append('No cross-site matches found — showing all scraped products.')

    stats = processor.calculate_price_statistics(dataframe)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    csv_filename = f'price_comparison_{timestamp}.csv'
    excel_filename = f'price_comparison_{timestamp}.xlsx'
    csv_success, csv_msg = processor.export_to_csv(csv_filename, dataframe)
    excel_success, excel_msg = processor.export_to_excel(excel_filename, dataframe)

    csv_path = os.path.join(CSV_OUTPUT_DIR, csv_filename) if csv_success else None
    excel_path = os.path.join(EXCEL_OUTPUT_DIR, excel_filename) if excel_success else None
    if not csv_success:
        messages.append(csv_msg)
    if not excel_success:
        messages.append(excel_msg)

    chart_paths: Dict[str, str] = {}
    if create_charts and not dataframe.empty:
        if comparisons:
            success, msg = ComparisonVisualizer().create_same_product_comparison(comparisons)
            if success and 'saved to ' in msg:
                chart_paths['same_product_comparison'] = msg.split('saved to ')[1]

        visualizer = Visualizer(output_dir=IMAGES_OUTPUT_DIR)
        for chart_name, (success, msg) in visualizer.create_all_charts(dataframe).items():
            if success and 'saved to ' in msg:
                chart_paths[chart_name] = msg.split('saved to ')[1]

    return ComparisonResult(
        query=query,
        dataframe=dataframe,
        comparisons=comparisons,
        stats=stats,
        csv_path=csv_path,
        excel_path=excel_path,
        chart_paths=chart_paths,
        used_demo_data=used_demo,
        messages=messages,
    )
