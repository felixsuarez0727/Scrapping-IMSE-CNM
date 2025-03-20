"""
Extractors for subpage content from research institute websites.
"""
import re
from urllib.parse import urljoin


def extract_subpage_content(session_manager, url, max_depth=1, current_depth=0, logger=None):
    """
    Extract content recursively from a subpage and its links.
    
    Args:
        session_manager: SessionManager instance
        url: URL of the page to extract
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
        logger: Logger instance
        
    Returns:
        Dictionary with extracted content
    """
    if current_depth > max_depth:
        return None
    
    if logger:
        logger.debug(f"Extracting content from subpage: {url} (depth {current_depth}/{max_depth})")
    else:
        print(f"Extracting content from subpage: {url} (depth {current_depth}/{max_depth})")
    
    # Decide whether to use Selenium based on depth
    use_selenium = (current_depth == 0)
    soup = session_manager.get_soup(url, use_selenium=use_selenium)
    
    if not soup:
        return None
    
    # Extract page title
    title = ""
    title_elem = soup.select_one('title')
    if title_elem:
        title = title_elem.text.strip()
    else:
        title_elem = soup.select_one('h1, .page-title')
        if title_elem:
            title = title_elem.text.strip()
    
    # Extract main content
    content = ""
    content_elems = soup.select('.item-page, .content, #content, main, article')
    if content_elems:
        # Extract text from first found content element
        content = content_elems[0].get_text().strip()
    else:
        # If no specific elements, take text from body
        body = soup.select_one('body')
        if body:
            content = body.get_text().strip()
    
    # Extract links to subpages
    subpages = []
    if current_depth < max_depth:
        content_links = soup.select('.item-page a, .content a, #content a, main a, article a, nav a')
        for link in content_links:
            href = link.get('href', '')
            
            # Ignore empty links, anchors, or external links
            if (not href or href.startswith('#') or href.startswith('javascript:') or 
                'mailto:' in href or '.pdf' in href):
                continue
            
            # Normalize URL
            link_url = urljoin(url, href)
            
            # Only include URLs from the same domain
            if url.split('/')[2] not in link_url:
                continue
            
            # Avoid URLs already visited
            if link_url in [sp['url'] for sp in subpages]:
                continue
            
            link_text = link.text.strip() or link.get('title', '')
            if not link_text:
                # If no text or title, try to use last segment of URL
                link_text = link_url.rstrip('/').split('/')[-1].replace('-', ' ').replace('_', ' ')
            
            subpages.append({
                'title': link_text,
                'url': link_url
            })
    
    return {
        'url': url,
        'title': title,
        'content': content,
        'subpages': subpages
    }