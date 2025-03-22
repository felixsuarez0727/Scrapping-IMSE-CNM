"""
Command-line interface for the IMSE-Scraper.
"""
import argparse
import logging
from imse_scraper.scraper import IMSEScraperAdvanced


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Advanced Web Scraper for Research Institute Websites')
    parser.add_argument('--url', default='http://www.imse-cnm.csic.es/', 
                        help='Base URL of the website to scrape')
    parser.add_argument('--output', default='data', 
                        help='Output directory for scraped data')
    parser.add_argument('--subpages', action='store_true', 
                        help='Also extract subpages')
    parser.add_argument('--depth', type=int, default=1, 
                        help='Maximum depth for subpage extraction')
    parser.add_argument('--no-json', action='store_true', 
                        help='Do not save JSON files')
    parser.add_argument('--no-selenium', action='store_true', 
                        help='Do not use Selenium (may affect dynamic content extraction)')
    parser.add_argument('--no-project-content', action='store_true',
                        help='Do not extract detailed content from project pages')
    parser.add_argument('--debug', action='store_true', 
                        help='Enable debug mode (more verbose logging)')
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    log_level = logging.DEBUG if args.debug else logging.INFO
    
    # Initialize and run scraper
    scraper = IMSEScraperAdvanced(
        base_url=args.url, 
        output_dir=args.output, 
        log_level=log_level,
        use_selenium=not args.no_selenium
    )
    
    scraper.run_full_scrape(
        include_subpages=args.subpages, 
        subpage_depth=args.depth, 
        save_json=not args.no_json,
        extract_content=not args.no_project_content
    )
    
    print(f"Scraping completed. Results saved to '{args.output}' directory.")


if __name__ == "__main__":
    main()