# IMSE-Scraper

An advanced web scraper for extracting structured data from research institute websites, with a focus on the Institute of Microelectronics of Seville (IMSE-CNM).

## Features

- Extracts structured data from research institute websites, including:
  - News articles
  - Research groups
  - Publications
  - Staff information
  - Contact details
  - Research projects
- Handles JavaScript-rendered content with Selenium
- Intelligent data extraction with multiple fallback strategies
- Multi-threaded for efficient scraping
- Exports data to both CSV and JSON formats
- Comprehensive logging

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/imse-scraper.git
cd imse-scraper

# Install the package
pip install -e .

# Or install with all dependencies
pip install -e ".[dev]"
```

## Requirements

- Python 3.7+
- BeautifulSoup4
- Requests
- Selenium
- ChromeDriver (installed automatically with webdriver-manager)

## Usage

### Command Line Interface

```bash
# Basic usage with default settings
python -m imse_scraper.cli --url http://www.imse-cnm.csic.es/

# Advanced usage with all options
python -m imse_scraper.cli --url http://www.imse-cnm.csic.es/ --output data_folder --subpages --depth 2 --debug
```

### Options

- `--url`: Base URL of the website to scrape (default: http://www.imse-cnm.csic.es/)
- `--output`: Output directory for scraped data (default: data)
- `--subpages`: Extract subpages in addition to main sections
- `--depth`: Maximum depth for subpage extraction (default: 1)
- `--no-json`: Disable JSON output (CSV only)
- `--no-selenium`: Disable Selenium (affects dynamic content extraction)
- `--debug`: Enable debug mode (more verbose logging)

### Python API

```python
from imse_scraper import IMSEScraperAdvanced

# Initialize scraper
scraper = IMSEScraperAdvanced(
    base_url="http://www.imse-cnm.csic.es/",
    output_dir="data",
    log_level=logging.INFO,
    use_selenium=True
)

# Run full scrape
data = scraper.run_full_scrape(
    include_subpages=True,
    subpage_depth=2,
    save_json=True
)

# Or extract specific data
news = scraper.extract_news()
staff = scraper.extract_staff()
publications = scraper.extract_publications()
```

## Output Format

The scraper generates both CSV and JSON files (unless `--no-json` is specified):

- `sections.csv/json`: Main website sections
- `news.csv/json`: News articles
- `research_groups.csv/json`: Research groups
- `publications.csv/json`: Academic publications
- `staff.csv/json`: Staff information
- `contact_info.csv/json`: Contact details
- `projects.csv/json`: Research projects
- `all_data.json`: Consolidated data (JSON only)
- `all_pages.json`: Website content (when `--subpages` is enabled, JSON only)

## Extending the Scraper

The modular design allows easy extension for additional websites or data types:

1. Create a new extractor in the `extractors` directory
2. Add your extraction logic
3. Register the extractor in `scraper.py`

## License

MIT

## Acknowledgements

This project was developed for educational purposes to demonstrate advanced web scraping techniques with Python.