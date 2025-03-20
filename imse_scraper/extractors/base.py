"""
Base extractors for common website elements.
"""
import re
from urllib.parse import urljoin


def extract_main_sections(session_manager, base_url, logger):
    """
    Extract the main sections of the website.
    
    Args:
        session_manager: SessionManager instance
        base_url: Base URL of the website
        logger: Logger instance
        
    Returns:
        List of dictionaries with section information
    """
    logger.info("Extracting main sections")
    soup = session_manager.get_soup(base_url)
    if not soup:
        logger.error("Could not get the main page")
        return []
    
    sections = []
    
    # Try to extract from main menu
    menu_selectors = ['ul.menu li a', 'nav ul li a', '.nav-menu a', '#main-menu a']
    menu_items = []
    
    for selector in menu_selectors:
        menu_items = soup.select(selector)
        if menu_items:
            logger.debug(f"Found {len(menu_items)} menu items with selector '{selector}'")
            break
    
    if not menu_items:
        logger.warning("No menu items found with predefined selectors")
        # Try to find any menu on the page
        menu_items = soup.find_all('a', href=True)
    
    for link in menu_items:
        href = link.get('href', '')
        
        # Ignore empty links, anchors, or external links
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        
        # Normalize URL
        full_url = urljoin(base_url, href)
        
        # Only include URLs from the same domain
        if base_url.split('/')[2] not in full_url:
            continue
        
        sections.append({
            'title': link.text.strip(),
            'url': full_url,
            'section_id': re.sub(r'\W+', '_', link.text.strip().lower())  # Unique ID based on title
        })
    
    logger.info(f"Extracted {len(sections)} main sections")
    return sections


def get_page_text(soup):
    """
    Extract text from a page, focusing on content areas.
    
    Args:
        soup: BeautifulSoup object for the page
        
    Returns:
        Extracted text content
    """
    # Try to find main content areas
    content_selectors = [
        '.item-page', '.content', '#content', 'main', 'article', 
        '.entry-content', '.post-content', '.page-content'
    ]
    
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            return content.get_text(separator=' ', strip=True)
    
    # Fallback to extracting from body
    body = soup.select_one('body')
    if body:
        return body.get_text(separator=' ', strip=True)
    
    # Last resort: all text
    return soup.get_text(separator=' ', strip=True)


def extract_links(soup, base_url, same_domain_only=True):
    """
    Extract links from a page.
    
    Args:
        soup: BeautifulSoup object for the page
        base_url: Base URL for normalizing relative links
        same_domain_only: If True, only return links from the same domain
        
    Returns:
        List of dictionaries with link information
    """
    links = []
    domain = base_url.split('/')[2]
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        
        # Skip empty links, anchors, JavaScript, and mailto
        if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        
        # Normalize URL
        full_url = urljoin(base_url, href)
        
        # Check if it's from the same domain if required
        if same_domain_only and domain not in full_url.split('/')[2]:
            continue
            
        # Get link text or title
        text = link.get_text().strip()
        title = link.get('title', '')
        
        links.append({
            'url': full_url,
            'text': text or title,
            'title': title
        })
    
    return links


def extract_images(soup, base_url):
    """
    Extract images from a page.
    
    Args:
        soup: BeautifulSoup object for the page
        base_url: Base URL for normalizing relative links
        
    Returns:
        List of dictionaries with image information
    """
    images = []
    
    for img in soup.find_all('img', src=True):
        src = img.get('src', '')
        
        # Skip empty sources or data URIs
        if not src or src.startswith('data:'):
            continue
        
        # Normalize URL
        full_url = urljoin(base_url, src)
        
        # Get alt text and title
        alt = img.get('alt', '')
        title = img.get('title', '')
        
        images.append({
            'url': full_url,
            'alt': alt,
            'title': title
        })
    
    return images