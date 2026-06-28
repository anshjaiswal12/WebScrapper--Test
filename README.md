# Price Comparison Tool

A Python application that compares product prices across **Amazon India** and **Flipkart**. It scrapes listings, matches identical products, highlights the best deal, and exports CSV/Excel reports with charts.

## Features

- Multi-site scraping (Amazon India & Flipkart) via Selenium
- Intelligent product matching by model number and name similarity
- Cross-site price comparison with savings calculation
- CSV and Excel export with formatting
- Professional charts (price comparison, distribution, dashboard)
- **Streamlit web UI** for interactive use
- **Demo mode** for cloud deployment without Chrome

## Quick Start (Local)

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Streamlit app
streamlit run app.py
```

### CLI

```bash
# Interactive CLI (prompts for query)
python -m src.main

# Config-driven batch run
python main.py
```

## Demo Mode

Live scraping requires Chrome/Chromium. For testing or cloud hosts without a browser:

```bash
export DEMO_MODE=true
streamlit run app.py
```

Or enable **Demo mode** in the Streamlit sidebar.

## Deploy to Render

1. Push this repo to GitHub.
2. In [Render](https://render.com), create a **Web Service**.
3. Connect the repo — Render detects `render.yaml` automatically.
4. Deploy. The app starts with `DEMO_MODE=true` (configured in `render.yaml`).

**Manual setup** (without Blueprint):

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |
| Python Version | `3.11.9` |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `false` | Use sample data instead of live scraping |
| `HEADLESS` | `true` | Run Chrome in headless mode |
| `SEARCH_QUERY` | `HP Pavilion laptop` | Default search query |
| `MAX_ITEMS_PER_SITE` | `10` | Max products per site |
| `AMAZON_ENABLED` | `true` | Enable Amazon scraping |
| `FLIPKART_ENABLED` | `true` | Enable Flipkart scraping |
| `LOG_LEVEL` | `INFO` | Logging level |

See `.env.example` for a full template.

## Project Structure

```
├── app.py                  # Streamlit web application
├── main.py                 # Config-driven CLI entry point
├── config/
│   ├── config.json         # JSON configuration
│   └── settings.py         # Python settings (env-aware)
├── src/
│   ├── scrapers/           # Amazon & Flipkart scrapers
│   ├── services/           # Comparison workflow service
│   ├── data/               # Demo product data
│   └── utils/              # Data processing, matching, charts
├── tests/                  # Unit tests
├── requirements.txt
├── runtime.txt
└── render.yaml             # Render deployment blueprint
```

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Limitations

- Live scraping depends on Chrome/Chromium and may be blocked by target sites.
- Cloud hosts (Render free tier) do not include Chrome — use demo mode.
- Website HTML structure changes may require scraper selector updates.

## License

MIT
