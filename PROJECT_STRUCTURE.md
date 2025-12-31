# Project Structure

```
Web_Scrapper/
│
├── config/
│   └── config.json              # Configuration file for search queries, sites, filters
│
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py      # Base scraper class with common functionality
│   │   ├── amazon_scraper.py    # Amazon India scraper implementation
│   │   └── flipkart_scraper.py  # Flipkart scraper implementation
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # Logging utility setup
│   │   └── helpers.py           # Helper functions (price cleaning, text normalization)
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── processor.py         # Data processing, filtering, export (CSV/Excel)
│   │
│   └── visualizations/
│       ├── __init__.py
│       └── plotter.py           # Visualization functions (charts, graphs)
│
├── output/
│   ├── csv/                     # CSV output files
│   ├── excel/                   # Excel output files
│   └── images/                  # Visualization images (PNG)
│
├── logs/                        # Log files (auto-generated)
│
├── tests/
│   ├── __init__.py
│   └── test_helpers.py          # Unit tests for helper functions
│
├── main.py                      # Main entry point
├── example_usage.py             # Example usage scripts
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── .gitignore                   # Git ignore rules
└── PROJECT_STRUCTURE.md         # This file
```

## Key Components

### Scrapers (`src/scrapers/`)
- **BaseScraper**: Abstract base class providing common scraping functionality
  - WebDriver setup and management
  - Page fetching with Selenium
  - HTML parsing with BeautifulSoup
  
- **AmazonScraper**: Implements Amazon India product scraping
  - Search functionality
  - Product information extraction (title, price, rating, reviews, URL)
  
- **FlipkartScraper**: Implements Flipkart product scraping
  - Search functionality
  - Product information extraction

### Data Processing (`src/data/`)
- **DataProcessor**: Handles data operations
  - Combining data from multiple sources
  - Filtering by price and rating
  - Sorting
  - Export to CSV and Excel
  - Summary statistics

### Visualizations (`src/visualizations/`)
- **Plotter**: Creates various charts
  - Price comparison by source
  - Price distribution histograms
  - Rating comparisons
  - Top products charts

### Utilities (`src/utils/`)
- **Logger**: Centralized logging setup
- **Helpers**: Utility functions for data cleaning and extraction

## Workflow

1. **Configuration**: Load settings from `config/config.json`
2. **Scraping**: Run scrapers for enabled sites (Amazon, Flipkart)
3. **Processing**: Combine, filter, and sort scraped data
4. **Export**: Save to CSV and Excel formats
5. **Visualization**: Generate comparison charts
6. **Logging**: Record all operations in log files

## File Naming Conventions

- Output files include timestamps: `price_comparison_YYYYMMDD_HHMMSS.csv`
- Log files: `scraper_YYYYMMDD.log`
- Visualization files: `{chart_type}_YYYYMMDD_HHMMSS.png`

