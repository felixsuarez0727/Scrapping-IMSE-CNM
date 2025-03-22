"""
Main scraper class for extracting data from research institute websites.
"""
import os
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

from imse_scraper.utils.browser import SessionManager
from imse_scraper.extractors.news import extract_news
from imse_scraper.extractors.publications import extract_publications
from imse_scraper.extractors.research import extract_research_groups
from imse_scraper.extractors.staff import extract_staff
from imse_scraper.extractors.contact import extract_contact_info
from imse_scraper.extractors.projects import extract_projects
from imse_scraper.extractors.subpages import extract_subpage_content
from imse_scraper.extractors.base import extract_main_sections
from imse_scraper.utils.io import save_to_csv, save_to_json


class IMSEScraperAdvanced:
    """
    Advanced scraper for research institute websites with multiple extraction strategies.
    
    This scraper can extract various types of information from institute websites,
    including news, publications, research groups, staff, contact info, and projects.
    It can handle both static and dynamic (JavaScript-rendered) content.
    """
    
    def __init__(self, base_url="http://www.imse-cnm.csic.es/", output_dir="data", 
                 log_level=logging.INFO, use_selenium=True):
        """
        Initialize the scraper with basic configuration.
        
        Args:
            base_url: Base URL of the website to scrape
            output_dir: Directory where CSV/JSON files will be saved
            log_level: Logging level (INFO, DEBUG, ERROR, etc.)
            use_selenium: If True, use Selenium for JavaScript-rendered pages
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.use_selenium = use_selenium
        self.extracted_data = {}
        
        # Set up logging
        self._setup_logging(log_level)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize session manager
        self.session_manager = SessionManager(use_selenium=use_selenium)
    
    def _setup_logging(self, log_level):
        """Configure the logging system."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(f"imse_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("IMSE-Scraper")
    
    def extract_main_sections(self):
        """
        Extract the main sections of the website.
        
        Returns:
            List of dictionaries with section information
        """
        self.logger.info("Extracting main sections")
        sections = extract_main_sections(
            self.session_manager, 
            self.base_url, 
            self.logger
        )
        self.extracted_data['sections'] = sections
        return sections
    
    def extract_news(self):
        """
        Extract recent news articles.
        
        Returns:
            List of dictionaries with news information
        """
        self.logger.info("Extracting news")
        news = extract_news(
            self.session_manager, 
            self.base_url, 
            self.logger
        )
        self.extracted_data['news'] = news
        return news
    
    def extract_research_groups(self):
        """
        Extract information about research groups.
        
        Returns:
            List of dictionaries with research group information
        """
        self.logger.info("Extracting research groups")
        groups = extract_research_groups(
            self.session_manager, 
            self.base_url, 
            self.logger,
            staff_data=self.extracted_data.get('staff'),
            sections=self.extracted_data.get('sections')
        )
        self.extracted_data['research_groups'] = groups
        return groups
    
    def extract_publications(self, limit=50):
        """
        Extract scientific publications using advanced techniques.
        
        Args:
            limit: Maximum number of publications to extract
            
        Returns:
            List of dictionaries with publication information
        """
        self.logger.info("Extracting publications")
        publications = extract_publications(
            self.session_manager, 
            self.base_url, 
            self.logger,
            limit=limit
        )
        self.extracted_data['publications'] = publications
        return publications
    
    def extract_staff(self, return_raw=False):
        """
        Extract staff information using advanced techniques.
        
        Args:
            return_raw: If True, return the list without storing in extracted_data
            
        Returns:
            List of dictionaries with staff information
        """
        self.logger.info("Extracting staff information")
        staff = extract_staff(
            self.session_manager, 
            self.base_url, 
            self.logger
        )
        
        # If return_raw is True, just return without storing
        if return_raw:
            return staff
            
        self.extracted_data['staff'] = staff
        return staff
    
    def extract_contact_info(self):
        """
        Extract institute contact information.
        
        Returns:
            Dictionary with contact information
        """
        self.logger.info("Extracting contact information")
        contact_info = extract_contact_info(
            self.session_manager, 
            self.base_url, 
            self.logger
        )
        self.extracted_data['contact_info'] = contact_info
        return contact_info
    
    def extract_projects(self):
        """
        Extract information about research projects.
        
        Returns:
            List of dictionaries with project information
        """
        self.logger.info("Extracting project information")
        projects = extract_projects(
            self.session_manager, 
            self.base_url, 
            self.logger
        )
        self.extracted_data['projects'] = projects
        return projects
    
    def extract_project_contents(self, projects=None):
        """
        Extract detailed content from individual project pages.
        
        Args:
            projects: List of projects to extract content from (if None, use previously extracted projects)
            
        Returns:
            Dictionary with project URLs as keys and content details as values
        """
        self.logger.info("Extracting detailed project contents")
        
        # If no projects provided, use previously extracted projects
        if projects is None:
            projects = self.extracted_data.get('projects', [])
        
        if not projects:
            self.logger.warning("No projects available to extract content from")
            return {}
        
        from imse_scraper.extractors.project_contents import extract_project_contents
        project_contents = extract_project_contents(
            self.session_manager,
            projects,
            self.logger
        )
    
        self.extracted_data['project_contents'] = project_contents
        return project_contents
    
    def extract_all_subpages(self, base_sections=None, max_depth=1):
        """
        Extract content from all main sections and their subpages.
        
        Args:
            base_sections: List of base sections to extract (if None, extract automatically)
            max_depth: Maximum recursion depth for subpages
            
        Returns:
            Dictionary with all extracted pages
        """
        self.logger.info(f"Extracting all subpages (max depth: {max_depth})")
        
        # If no base sections provided, extract them
        if base_sections is None:
            base_sections = self.extract_main_sections()
        
        all_pages = {}
        
        # Use ThreadPoolExecutor to parallelize extractions
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Create futures for each base section
            future_to_url = {
                executor.submit(extract_subpage_content, 
                                self.session_manager, 
                                section['url'], 
                                max_depth, 
                                0, 
                                self.logger): section['url']
                for section in base_sections
            }
            
            # Process results
            for future in future_to_url:
                url = future_to_url[future]
                try:
                    data = future.result()
                    if data:
                        all_pages[url] = data
                        
                        # If there are subpages and we're at the first depth,
                        # also extract second-level subpages
                        if max_depth > 1 and 'subpages' in data and data['subpages']:
                            for subpage in data['subpages']:
                                subpage_url = subpage['url']
                                
                                # Avoid duplicate URLs
                                if subpage_url not in all_pages:
                                    try:
                                        # Extract subpage content
                                        subpage_data = extract_subpage_content(
                                            self.session_manager,
                                            subpage_url, 
                                            max_depth, 
                                            1,
                                            self.logger
                                        )
                                        if subpage_data:
                                            all_pages[subpage_url] = subpage_data
                                    except Exception as e:
                                        self.logger.error(f"Error extracting subpage {subpage_url}: {e}")
                except Exception as e:
                    self.logger.error(f"Error extracting {url}: {e}")
        
        self.logger.info(f"Extracted {len(all_pages)} pages total")
        self.extracted_data['all_pages'] = all_pages
        return all_pages
    
    def clean_and_normalize_data(self):
        """
        Clean and normalize all extracted data.
        
        Returns:
            Dictionary with cleaned and normalized data
        """
        self.logger.info("Cleaning and normalizing data")
        
        from imse_scraper.utils.parsers import clean_data
        cleaned_data = clean_data(self.extracted_data, self.logger)
        
        self.logger.info("Data cleaned and normalized")
        return cleaned_data
    
    def run_full_scrape(self, include_subpages=False, subpage_depth=1, save_json=True, extract_content=True):
        """
        Run complete scraping of the website.
        
        Args:
            include_subpages: If True, also extract all subpages
            subpage_depth: Maximum depth for subpage extraction
            save_json: If True, also save JSON files (in addition to CSV)
            extract_content: If True, extract detailed content from project pages
            
        Returns:
            Dictionary with all extracted data
        """
        self.logger.info(f"Starting advanced scraping of {self.base_url}")
        start_time = time.time()
        
        # Extract main sections
        sections = self.extract_main_sections()
        save_to_csv(sections, 'sections', self.output_dir, self.logger)
        if save_json:
            save_to_json(sections, 'sections', self.output_dir, self.logger)
        
        # Extract news
        news = self.extract_news()
        save_to_csv(news, 'news', self.output_dir, self.logger)
        if save_json:
            save_to_json(news, 'news', self.output_dir, self.logger)
        
        # Extract research groups
        groups = self.extract_research_groups()
        save_to_csv(groups, 'research_groups', self.output_dir, self.logger)
        if save_json:
            save_to_json(groups, 'research_groups', self.output_dir, self.logger)
        
        # Extract publications
        publications = self.extract_publications()
        save_to_csv(publications, 'publications', self.output_dir, self.logger)
        if save_json:
            save_to_json(publications, 'publications', self.output_dir, self.logger)
        
        # Extract staff
        staff = self.extract_staff()
        save_to_csv(staff, 'staff', self.output_dir, self.logger)
        if save_json:
            save_to_json(staff, 'staff', self.output_dir, self.logger)
        
        # Extract contact information
        contact_info = self.extract_contact_info()
        save_to_csv([contact_info], 'contact_info', self.output_dir, self.logger)  # Save as list for CSV
        if save_json:
            save_to_json(contact_info, 'contact_info', self.output_dir, self.logger)
        
        # Extract projects
        projects = self.extract_projects()
        save_to_csv(projects, 'projects', self.output_dir, self.logger)
        if save_json:
            save_to_json(projects, 'projects', self.output_dir, self.logger)
        
        # Extract detailed project contents
        if extract_content and projects:
            project_contents = self.extract_project_contents(projects)
            if save_json:
                save_to_json(project_contents, 'project_contents', self.output_dir, self.logger)
        
        # Optionally extract all subpages
        if include_subpages:
            all_pages = self.extract_all_subpages(sections, max_depth=subpage_depth)
            if save_json:
                save_to_json(all_pages, 'all_pages', self.output_dir, self.logger)
        
        # Clean and normalize all data
        cleaned_data = self.clean_and_normalize_data()
        
        # Save all data to a single file
        if save_json:
            save_to_json(cleaned_data, 'all_data', self.output_dir, self.logger)
        
        # Close the Selenium browser if used
        if self.use_selenium:
            try:
                self.session_manager.close()
                self.logger.debug("Selenium browser closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing Selenium browser: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        self.logger.info(f"Scraping completed in {duration:.2f} seconds")
        
        return cleaned_data