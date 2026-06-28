"""
Price Comparison Tool — Streamlit Web Application

Run locally:
    streamlit run app.py
"""
import os
import sys

import pandas as pd
import streamlit as st

# Project root on path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config.settings import DEMO_MODE, MAX_ITEMS_PER_SITE, SEARCH_QUERY
from src.services.comparison_service import run_comparison

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title='PriceCompare — Amazon vs Flipkart',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #2E86AB 0%, #FF6B35 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        color: #6c757d;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        border-left: 4px solid #2E86AB;
    }
    .best-price {
        color: #198754;
        font-weight: 600;
    }
    div[data-testid="stSidebar"] {
        background-color: #f0f4f8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('### ⚙️ Settings')
    search_query = st.text_input(
        'Search query',
        value=SEARCH_QUERY,
        placeholder='e.g. HP Pavilion laptop',
        help='Product name or model to compare across sites.',
    )
    max_results = st.slider(
        'Max results per site',
        min_value=3,
        max_value=20,
        value=MAX_ITEMS_PER_SITE,
    )
    st.markdown('**Sources**')
    scrape_amazon = st.checkbox('Amazon India', value=True)
    scrape_flipkart = st.checkbox('Flipkart', value=True)
    use_demo = st.checkbox(
        'Demo mode (sample data)',
        value=DEMO_MODE,
        help='Use built-in sample data. Recommended on cloud hosts without Chrome.',
    )
    create_charts = st.checkbox('Generate charts', value=True)

    st.divider()
    st.markdown(
        '**About**\n\n'
        'Compares prices across Amazon India and Flipkart, '
        'matches identical products, and highlights the best deal.'
    )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<p class="main-header">💰 PriceCompare</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Smart price comparison across Amazon India &amp; Flipkart</p>',
    unsafe_allow_html=True,
)

col_run, col_info = st.columns([1, 3])
with col_run:
    run_clicked = st.button('🔍 Compare Prices', type='primary', use_container_width=True)
with col_info:
    if use_demo:
        st.info('Demo mode is on — results use sample data.')

# ---------------------------------------------------------------------------
# Run comparison
# ---------------------------------------------------------------------------
if run_clicked:
    if not search_query.strip():
        st.error('Please enter a search query.')
    elif not scrape_amazon and not scrape_flipkart:
        st.error('Select at least one source.')
    else:
        with st.spinner('Searching and comparing prices…'):
            try:
                result = run_comparison(
                    query=search_query.strip(),
                    max_results=max_results,
                    scrape_amazon=scrape_amazon,
                    scrape_flipkart=scrape_flipkart,
                    use_demo=use_demo,
                    create_charts=create_charts,
                )
                st.session_state['result'] = result
            except Exception as exc:
                st.error(f'Comparison failed: {exc}')
                st.session_state.pop('result', None)

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
result = st.session_state.get('result')

if result is not None:
    for msg in result.messages:
        st.caption(msg)

    if result.used_demo_data:
        st.warning('Showing demo data. Install Chrome locally for live scraping.')

    stats = result.stats
    df = result.dataframe

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Products', len(df))
    m2.metric(
        'Lowest Price',
        f"₹{stats['lowest_price']['price']:,.0f}" if stats.get('lowest_price') else '—',
    )
    m3.metric(
        'Highest Price',
        f"₹{stats['highest_price']['price']:,.0f}" if stats.get('highest_price') else '—',
    )
    m4.metric(
        'Potential Savings',
        f"{stats.get('percentage_savings', 0):.1f}%",
    )

    # Best deal highlight
    if stats.get('lowest_price'):
        best = stats['lowest_price']
        st.success(
            f"**Best deal:** {best['product_name']} — "
            f"₹{best['price']:,.0f} on **{best['source']}**"
        )

    # Tabs
    tab_compare, tab_table, tab_charts, tab_download = st.tabs(
        ['Cross-site matches', 'All products', 'Charts', 'Downloads']
    )

    with tab_compare:
        if result.comparisons:
            for comp in result.comparisons:
                with st.expander(f"📦 {comp['product_name']}", expanded=True):
                    rows = []
                    prices = [
                        info.get('price', float('inf'))
                        for info in comp['sources'].values()
                        if info.get('price')
                    ]
                    min_price = min(prices) if prices else None

                    for source, info in sorted(
                        comp['sources'].items(),
                        key=lambda x: x[1].get('price', float('inf')),
                    ):
                        price = info.get('price', 0)
                        rows.append({
                            'Source': source,
                            'Price': f"₹{price:,.0f}",
                            'Rating': f"{info.get('rating', '—')}/5",
                            'In Stock': '✅' if info.get('in_stock', True) else '❌',
                            'Best Price': '🏆' if price == min_price else '',
                            'URL': info.get('url', ''),
                        })

                    st.dataframe(
                        pd.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                    savings = comp.get('savings')
                    if savings and savings.get('price_difference', 0) > 0:
                        st.markdown(
                            f"<span class='best-price'>Save ₹{savings['price_difference']:,.0f} "
                            f"({savings['percentage_savings']:.1f}%) by buying from "
                            f"{savings['best_deal_source']}</span>",
                            unsafe_allow_html=True,
                        )
        else:
            st.info('No cross-site product matches found for this query.')

    with tab_table:
        display_df = df.copy()
        if 'price' in display_df.columns:
            display_df['price'] = display_df['price'].apply(
                lambda x: f"₹{x:,.0f}" if pd.notna(x) else '—'
            )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with tab_charts:
        if result.chart_paths:
            for name, path in result.chart_paths.items():
                if os.path.exists(path):
                    st.markdown(f"**{name.replace('_', ' ').title()}**")
                    st.image(path, use_container_width=True)
        else:
            st.info('No charts generated. Enable "Generate charts" in the sidebar.')

    with tab_download:
        dl1, dl2 = st.columns(2)
        with dl1:
            if result.csv_path and os.path.exists(result.csv_path):
                with open(result.csv_path, 'rb') as f:
                    st.download_button(
                        '⬇️ Download CSV',
                        data=f,
                        file_name=os.path.basename(result.csv_path),
                        mime='text/csv',
                        use_container_width=True,
                    )
        with dl2:
            if result.excel_path and os.path.exists(result.excel_path):
                with open(result.excel_path, 'rb') as f:
                    st.download_button(
                        '⬇️ Download Excel',
                        data=f,
                        file_name=os.path.basename(result.excel_path),
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        use_container_width=True,
                    )

else:
    # Landing state
    st.markdown('---')
    st.markdown('### How it works')
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('**1. Search**\n\nEnter a product name or model number.')
    with c2:
        st.markdown('**2. Compare**\n\nWe scrape Amazon & Flipkart and match identical products.')
    with c3:
        st.markdown('**3. Save**\n\nSee the best deal, charts, and exportable reports.')

    st.markdown('---')
    st.markdown(
        '_Tip: Enable **Demo mode** to explore the app without live scraping — '
        'ideal for cloud deployment._'
    )
