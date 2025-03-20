"""
Browser and session management utilities for web scraping.
"""
import random
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class SessionManager:
    """
    Manages HTTP sessions and Selenium browser instances for web scraping.
    
    Provides a unified interface for fetching web pages with both requests and Selenium,
    with built-in retry logic, error handling, and human-like behavior.
    """
    
    def __init__(self, use_selenium=True):
        """
        Initialize the session manager.
        
        Args:
            use_selenium: If True, initialize Selenium for JavaScript-rendered content
        """
        self.use_selenium = use_selenium
        self.headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5,es;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.session = requests.Session()
        
        # Initialize Selenium if enabled
        self.driver = None
        if self.use_selenium:
            self._setup_selenium()
    
    def _get_random_user_agent(self):
        """Return a random User-Agent to avoid blocking."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        return random.choice(user_agents)
    
    def _setup_selenium(self):
        """Configure Selenium browser for dynamic content."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={self._get_random_user_agent()}")
            
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
        except Exception as e:
            print(f"Error initializing Selenium: {e}")
            self.use_selenium = False
            print("Continuing without JavaScript support")
    
    def get_soup(self, url, retries=3, delay=1, use_selenium=False, logger=None):
        """
        Get a BeautifulSoup object from a URL with retries.
        
        Args:
            url: URL to scrape
            retries: Number of retries in case of failure
            delay: Time between retries (seconds)
            use_selenium: If True, use Selenium for JavaScript
            logger: Logger instance for logging
            
        Returns:
            BeautifulSoup object or None in case of error
        """
        # Use Selenium if enabled and requested for this URL
        if self.use_selenium and use_selenium:
            return self.get_selenium_soup(url, logger=logger)
        
        for attempt in range(retries):
            try:
                if logger:
                    logger.debug(f"Downloading {url} (attempt {attempt+1}/{retries})")
                else:
                    print(f"Downloading {url} (attempt {attempt+1}/{retries})")
                
                # Add random delay for more human-like behavior
                if attempt > 0:
                    sleep_time = delay * (1 + random.random())
                    time.sleep(sleep_time)
                
                response = self.session.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                # Detect encoding
                if 'charset' in response.headers.get('content-type', '').lower():
                    response.encoding = response.apparent_encoding
                
                if logger:
                    logger.debug(f"Download successful: {url}")
                else:
                    print(f"Download successful: {url}")
                    
                return BeautifulSoup(response.text, 'html.parser')
            
            except requests.exceptions.RequestException as e:
                if logger:
                    logger.warning(f"Error downloading {url} (attempt {attempt+1}): {e}")
                else:
                    print(f"Error downloading {url} (attempt {attempt+1}): {e}")
                    
                if attempt == retries - 1:
                    if logger:
                        logger.error(f"Could not download {url} after {retries} attempts")
                    else:
                        print(f"Could not download {url} after {retries} attempts")
                    return None
    
    def get_selenium_soup(self, url, wait_time=10, logger=None):
        """
        Get rendered HTML from a page using Selenium.
        
        Args:
            url: URL to scrape
            wait_time: Maximum wait time for page load
            logger: Logger instance for logging
            
        Returns:
            BeautifulSoup object or None in case of error
        """
        if not self.use_selenium:
            if logger:
                logger.warning("Selenium not available, using requests")
            else:
                print("Selenium not available, using requests")
            return self.get_soup(url, logger=logger)
        
        try:
            if logger:
                logger.debug(f"Loading {url} with Selenium")
            else:
                print(f"Loading {url} with Selenium")
                
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more to ensure JS executes
            time.sleep(2)
            
            # Get rendered HTML
            html = self.driver.page_source
            
            if logger:
                logger.debug(f"Selenium loaded successfully: {url}")
            else:
                print(f"Selenium loaded successfully: {url}")
                
            return BeautifulSoup(html, 'html.parser')
            
        except Exception as e:
            if logger:
                logger.error(f"Error loading {url} with Selenium: {e}")
                logger.debug(f"Trying fallback with requests for {url}")
            else:
                print(f"Error loading {url} with Selenium: {e}")
                print(f"Trying fallback with requests for {url}")
                
            # Try with requests as fallback
            return self.get_soup(url, logger=logger)
    
    def close(self):
        """Close the Selenium browser if it exists."""
        if self.driver:
            self.driver.quit()
            self.driver = None