# Packaging Guide for Submission

## Package Structure

Create a zip file with the following structure:

```
Ansh_Jaiswal_PriceComparison_Internship.zip
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── amazon_scraper.py
│   │   └── flipkart_scraper.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── helpers.py
│       ├── data_processor.py
│       └── visualizer.py
├── config/
│   ├── config.json
│   └── settings.py
├── data/
│   └── output/
│       ├── csv/
│       ├── excel/
│       └── images/
├── logs/
├── tests/
│   ├── __init__.py
│   └── test_helpers.py
├── run_scraper.py
├── test_scraper.py
├── requirements.txt
├── README.md
├── SUBMISSION_SUMMARY.md
├── FINAL_CHECKLIST.md
└── PACKAGING_GUIDE.md (this file)
```

## Files to Include

### Required Files
- ✅ All Python source files in `src/`
- ✅ Configuration files in `config/`
- ✅ `run_scraper.py` (main entry point)
- ✅ `test_scraper.py` (test script)
- ✅ `requirements.txt` (dependencies)
- ✅ `README.md` (documentation)
- ✅ `SUBMISSION_SUMMARY.md` (summary)
- ✅ `FINAL_CHECKLIST.md` (checklist)

### Optional Files
- Sample output files in `data/output/` (if available)
- Screenshots in `screenshots/` folder (if available)
- Additional documentation files

### Files to Exclude
- `__pycache__/` directories
- `.pyc` files
- Virtual environment (`venv/`)
- Log files (can be regenerated)
- `.git/` directory (if using git)

## Creating the Package

### Method 1: Using Command Line

```bash
# Navigate to parent directory
cd /home/arth-linux/Desktop/My\ Code/

# Create zip excluding unnecessary files
zip -r Ansh_Jaiswal_PriceComparison_Internship.zip Web_Scrapper/ \
  -x "Web_Scrapper/__pycache__/*" \
  -x "Web_Scrapper/**/__pycache__/*" \
  -x "Web_Scrapper/**/*.pyc" \
  -x "Web_Scrapper/venv/*" \
  -x "Web_Scrapper/.git/*" \
  -x "Web_Scrapper/logs/*.log"
```

### Method 2: Manual Selection

1. Create a new folder: `Ansh_Jaiswal_PriceComparison_Internship`
2. Copy the following:
   - `src/` folder (entire directory)
   - `config/` folder
   - `data/` folder (structure only, or with sample outputs)
   - `tests/` folder
   - `run_scraper.py`
   - `test_scraper.py`
   - `requirements.txt`
   - `README.md`
   - `SUBMISSION_SUMMARY.md`
   - `FINAL_CHECKLIST.md`
3. Exclude:
   - `__pycache__/` folders
   - `.pyc` files
   - `venv/` folder
   - Large log files
4. Zip the folder

## Verification Steps

Before submitting, verify:

1. **All files present**:
   ```bash
   unzip -l Ansh_Jaiswal_PriceComparison_Internship.zip | grep -E "(\.py|\.txt|\.md)$"
   ```

2. **Structure is correct**:
   ```bash
   unzip -l Ansh_Jaiswal_PriceComparison_Internship.zip | head -30
   ```

3. **No sensitive data**:
   - Check for API keys
   - Check for passwords
   - Check for personal information

4. **README is complete**:
   - All sections present
   - Author name correct
   - No placeholder text

## Sample Output Files

If including sample outputs:

1. Run the scraper once:
   ```bash
   python run_scraper.py --query "HP Pavilion laptop" --max-results 5
   ```

2. Copy sample files:
   - One CSV file
   - One Excel file
   - One chart image

3. Rename to indicate they are samples:
   - `sample_price_comparison.csv`
   - `sample_price_comparison.xlsx`
   - `sample_price_comparison_chart.png`

## Final Size Check

The package should be:
- **Size**: Typically 500KB - 2MB (without sample outputs)
- **Files**: 20-30 Python files
- **Structure**: Clean and organized

## Submission Checklist

Before final submission:

- [ ] Package name: `Ansh_Jaiswal_PriceComparison_Internship.zip`
- [ ] All source code included
- [ ] README.md is complete
- [ ] requirements.txt has all dependencies
- [ ] No __pycache__ folders
- [ ] No .pyc files
- [ ] No sensitive data
- [ ] Sample outputs included (optional)
- [ ] Package size is reasonable
- [ ] Can be extracted and run

## Testing the Package

After creating the package:

1. Extract to a new location
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run test: `python test_scraper.py`
5. Run main: `python run_scraper.py --help`

If all steps work, the package is ready for submission!

---

**Package Name**: `Ansh_Jaiswal_PriceComparison_Internship.zip`  
**Developer**: Ansh Jaiswal

