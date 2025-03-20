# IMSE-Scraper

An advanced web scraper for extracting structured data from the Institute of Microelectronics of Seville (IMSE-CNM) website.

## Features

- Extracts structured data from research institute websites, including:
  - News articles
  - Research groups
  - Scientific publications
  - Staff information
  - Contact details
  - Research projects
- Handles JavaScript-rendered content with Selenium
- Intelligent data extraction with multiple fallback strategies
- Multi-threaded for efficient scraping
- Exports data to both CSV and JSON formats
- Comprehensive logging system

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/imse-scraper.git
cd imse-scraper

# Install dependencies
pip install -r requirements.txt
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
python -m imse_scraper.cli

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
import logging

# Initialize scraper
scraper = IMSEScraperAdvanced(
    base_url="http://www.imse-cnm.csic.es/",
    output_dir="data_folder",
    log_level=logging.INFO,
    use_selenium=True
)

# Run full scrape
data = scraper.run_full_scrape(
    include_subpages=True,
    subpage_depth=2,
    save_json=True
)

# Or extract specific data types
news = scraper.extract_news()
staff = scraper.extract_staff()
publications = scraper.extract_publications()
```

## Output File Structure

The scraper generates the following files in the specified directory (default: `data/`):

### CSV Files

- `sections.csv`: Main website sections
- `news.csv`: News articles
- `research_groups.csv`: Research groups
- `publications.csv`: Academic publications
- `staff.csv`: Staff information
- `contact_info.csv`: Contact details
- `projects.csv`: Research projects

### JSON Files

- `sections.json`: Main website sections
- `news.json`: News articles
- `research_groups.json`: Research groups
- `publications.json`: Academic publications
- `staff.json`: Staff information
- `contact_info.json`: Contact details
- `projects.json`: Research projects
- `all_data.json`: Consolidated data from all categories
- `all_pages.json`: Content from all subpages (when `--subpages` is enabled)

### Log Files

- `imse_scraper_YYYYMMDD_HHMMSS.log`: Detailed execution log with timestamp

## File Contents

### sections.csv/json

Contains the main sections of the website:

| Field      | Description                                  |
|------------|----------------------------------------------|
| title      | Section title                                |
| url        | Full URL of the section                      |
| section_id | Unique identifier generated from the title   |

### news.csv/json

Contains news articles extracted from the site:

| Field     | Description                                  |
|-----------|----------------------------------------------|
| title     | News title                                   |
| date      | Publication date                             |
| content   | Textual content of the news article          |
| url       | Full URL of the article (if available)       |
| image_url | URL of the associated image (if available)   |

### research_groups.csv/json

Contains information about research groups:

| Field           | Description                                  |
|-----------------|----------------------------------------------|
| name            | Name of the research group                   |
| description     | Description of the group's activities        |
| researchers     | List of researchers (JSON format in CSV)     |
| researchers_text| List of researchers in text format           |

### publications.csv/json

Contains scientific publications:

| Field     | Description                                  |
|-----------|----------------------------------------------|
| authors   | Publication authors                          |
| title     | Publication title                            |
| venue     | Journal or conference                        |
| year      | Publication year                             |
| doi       | DOI (Digital Object Identifier) if available |
| url       | URL of the publication or source page        |
| full_text | Complete bibliographic citation text         |

### staff.csv/json

Contains information about institute personnel:

| Field      | Description                                  |
|------------|----------------------------------------------|
| name       | Full name of the person                      |
| position   | Role or position                             |
| email      | Email address                                |
| phone      | Phone number                                 |
| department | Department or area                           |
| source_url | URL of the source page                       |

### contact_info.csv/json

Contains general contact information:

| Field         | Description                                  |
|---------------|----------------------------------------------|
| institute_name| Full name of the institute                   |
| address       | Physical address                             |
| city          | City                                         |
| postal_code   | Postal code                                  |
| country       | Country                                      |
| phone         | General phone number                         |
| fax           | Fax number                                   |
| email         | General contact email                        |
| website       | Official website                             |
| social_media  | Social media links (JSON format in CSV)      |

### projects.csv/json

Contains information about research projects:

| Field       | Description                                  |
|-------------|----------------------------------------------|
| title       | Project title                                |
| description | Project description                          |
| period      | Duration period (e.g., "2023-2026")          |
| funding     | Funding information                          |
| url         | URL of the project page or source            |

### all_data.json

JSON file containing all the above data in a single hierarchically structured file:

```json
{
  "sections": [...],
  "news": [...],
  "research_groups": [...],
  "publications": [...],
  "staff": [...],
  "contact_info": {...},
  "projects": [...]
}
```

### all_pages.json

JSON file with the content of all subpages up to the specified depth:

```json
{
  "http://www.imse-cnm.csic.es/page1.php": {
    "url": "http://www.imse-cnm.csic.es/page1.php",
    "title": "Page title",
    "content": "Textual content of the page",
    "subpages": [
      {
        "title": "Subpage title",
        "url": "http://www.imse-cnm.csic.es/subpage.php"
      }
    ]
  },
  "http://www.imse-cnm.csic.es/page2.php": {
    // Similar structure
  }
}
```

## Performance Optimization

The scraper implements several techniques to optimize performance:

1. **Parallel processing**: Uses threads to extract multiple pages simultaneously.
2. **Selective extraction**: Uses Selenium only when necessary for dynamic content.
3. **Caching system**: Avoids downloading the same page multiple times.
4. **Fallback strategies**: If one extraction method fails, automatically tries alternative methods.

## Customization and Extension

### Selenium Configuration

By default, the scraper runs Chrome in headless mode. To customize:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--user-agent=Mozilla/5.0...")

# Pass these options when initializing the scraper
scraper = IMSEScraperAdvanced(
    # ... other parameters ...
    selenium_options=options
)
```

### Adding New Extractors

To add a new type of extraction:

1. Create a new file in the `extractors/` directory (e.g., `events.py`)
2. Implement the extraction function
3. Add the corresponding method in the `IMSEScraperAdvanced` class
4. Register the new extractor in `run_full_scrape()`

### Adapting to Other Websites

To adapt the scraper to other research institute websites:

1. Create a subclass of `IMSEScraperAdvanced` for the new site
2. Adjust CSS selectors and patterns as needed
3. Modify specific extraction methods to adapt to the structure of the new site

## Troubleshooting

### Common Issues

- **Error 'ChromeDriver executable needs to be in PATH'**: Make sure you have webdriver-manager installed (`pip install webdriver-manager`).
- **No JavaScript content extracted**: Verify that Selenium is enabled (`use_selenium=True`).
- **Empty or incomplete data**: Try enabling debug mode to see detailed messages (`--debug`).
- **Network errors or timeouts**: Increase the number of retries or add delays between requests.

### Debug Logs

To get detailed information during execution:

```bash
python -m imse_scraper.cli --debug
```

Logs are saved to the `imse_scraper_YYYYMMDD_HHMMSS.log` file and also displayed in the console.
