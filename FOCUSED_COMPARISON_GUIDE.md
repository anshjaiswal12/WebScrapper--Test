# 🎯 Focused Price Comparison Tool - User Guide

## What Changed?

The tool has been **completely rebuilt** to focus on the **core purpose**: comparing **THE SAME PRODUCT** across different sites to find where it's cheapest.

## How It Works Now

### Before (Old Approach)
- Showed all products from all sites
- Hard to compare different products
- No clear "best deal" recommendation

### After (New Approach) ✅
- **Matches same products** across sites using model numbers and similarity
- **Shows focused comparison** of the same product
- **Highlights best price** with savings amount
- **Clear recommendation** on where to buy

## Example Output

```
Product: Apple iPhone 15 (128GB, Blue)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amazon India:         ₹69,999 ⭐ 4.5/5  ✓ In Stock
Flipkart:            ₹68,490 ⭐ 4.4/5  ✓ In Stock  🏆 BEST PRICE

💰 BEST DEAL: Buy from Flipkart and SAVE ₹1,509 (2.2%)!
   Link: https://flipkart.com/...
```

## Key Features

### 1. Intelligent Product Matching
- Extracts model numbers (e.g., "eg2007TU", "WH-1000XM5")
- Normalizes product names
- Calculates similarity scores
- Groups same products across sites

### 2. Focused Comparison
- Only shows products available on **multiple sites**
- Sorts by price (cheapest first)
- Highlights best price with 🏆
- Shows stock status

### 3. Savings Calculation
- Price difference (₹)
- Percentage savings (%)
- Best deal source
- Direct link to buy

### 4. Professional Output
- Clean, formatted display
- Color-coded results
- Easy to read comparison table
- Actionable recommendations

## Usage

### Basic Usage
```bash
python start_scrapping.py
# or
python run_scraper.py
```

### With Custom Query
```bash
python run_scraper.py --query "iPhone 15 128GB"
```

### With More Results
```bash
python run_scraper.py --query "HP Pavilion 15" --max-results 20
```

## Output Files

1. **CSV Report**: Same-product comparisons with best price indicators
2. **Excel Report**: Formatted with multiple sheets
3. **Comparison Chart**: Visual bar chart showing same product prices
4. **Console Output**: Formatted comparison table

## Technical Details

### Product Matching Algorithm

1. **Model Number Extraction**
   - Pattern: `[letters][numbers][letters]` (e.g., "eg2007TU")
   - Pattern: `iPhone/iPad [number]` (e.g., "iPhone 15")
   - Pattern: `[BRAND]-[MODEL]` (e.g., "WH-1000XM5")

2. **Name Normalization**
   - Lowercase conversion
   - Remove special characters
   - Remove stop words ("new", "latest", "best")
   - Standardize whitespace

3. **Similarity Calculation**
   - Uses `SequenceMatcher` for string similarity
   - Threshold: 75% similarity to match
   - Considers model numbers as primary match

4. **Grouping Logic**
   - First: Group by model number
   - Then: Group by name similarity
   - Only groups with 2+ sources are shown

### Comparison Engine

- **Input**: List of all products from all sites
- **Process**: Match products → Group same products → Find best deals
- **Output**: List of comparisons with prices from each site

## Benefits

✅ **Focused**: Only shows same products, not random products  
✅ **Actionable**: Tells you exactly where to buy to save money  
✅ **Clear**: Easy to understand format  
✅ **Accurate**: Uses model numbers and similarity matching  
✅ **Time-saving**: No need to manually compare products  

## Testing

Run the test script to verify:
```bash
python test_comparison.py
```

This will test:
- Model number extraction
- Product matching
- Comparison engine
- Output formatting

## Troubleshooting

### "No matching products found"
- Products might have different names across sites
- Try a more specific search query
- Check if model numbers are being extracted correctly

### "Products not matching correctly"
- Adjust similarity threshold in `product_matcher.py`
- Check model number extraction patterns
- Verify product names are being normalized correctly

## Next Steps

1. **Run the tool**: `python start_scrapping.py`
2. **Enter your search query**: e.g., "HP Pavilion 15" or "iPhone 15"
3. **Review the comparison**: See where the same product is cheapest
4. **Save money**: Buy from the recommended site!

---

**Remember**: This tool compares **THE SAME PRODUCT** across sites. It's not for comparing different products - it's for finding where to buy the product you want at the best price!

