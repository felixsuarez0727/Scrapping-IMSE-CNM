"""
Extractors for news content from research institute websites.
"""
import re
from urllib.parse import urljoin
from imse_scraper.utils.parsers import extract_date_from_text


def extract_news(session_manager, base_url, logger):
    """
    Extract recent news articles.
    
    Args:
        session_manager: SessionManager instance
        base_url: Base URL of the website
        logger: Logger instance
        
    Returns:
        List of dictionaries with news information
    """
    logger.info("Extracting news")
    news_urls = [
        urljoin(base_url, "index.php/en/news"),
        urljoin(base_url, "index.php/es/es-es/noticias"),
        urljoin(base_url, "index.php/es/noticias"),
        urljoin(base_url, "noticias"),
        urljoin(base_url, "news"),
        urljoin(base_url, "en/news"),
    ]
    
    # Try different URLs until a valid one is found
    soup = None
    used_url = None
    
    for url in news_urls:
        soup = session_manager.get_soup(url, use_selenium=True)  # Use Selenium for news
        if soup:
            used_url = url
            logger.debug(f"News URL found: {url}")
            break
    
    if not soup:
        logger.error("Could not find the news page")
        return []
    
    news_items = []
    
    # Try to extract each individual news item
    news_container = soup.select_one('.blog, .news-container, #content, .item-page')
    
    if news_container:
        # Look for elements that look like news (articles, divs with specific classes)
        news_elements = news_container.select('article, .item, div[class*="item"], div[class*="blog-item"], div[class*="news"]')
        
        if not news_elements:
            # If we don't find specific articles, look for elements containing titles
            news_elements = news_container.select('div:has(h2), div:has(h3), div:has(.item-title)')
        
        if not news_elements:
            # Last resort: split by dates
            all_content = news_container.get_text()
            news_sections = re.split(r'\d{1,2}\s+[A-Z][a-z]+\s+\d{4}', all_content)
            
            for section in news_sections:
                if len(section.strip()) > 100:  # Only consider sections with enough content
                    # Extract title (assuming it's at the beginning)
                    title_match = re.search(r'^([^\n.]+)', section.strip())
                    title = title_match.group(1).strip() if title_match else "Untitled News"
                    
                    # Extract date if it exists
                    date_match = re.search(r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})', section)
                    date = date_match.group(1) if date_match else "No date"
                    
                    # Add the news item
                    news_items.append({
                        'title': title,
                        'date': date,
                        'content': section.strip(),
                        'url': used_url,
                        'image_url': ""
                    })
        else:
            # Process each news element
            for item in news_elements:
                # Extract title
                title_elem = item.select_one('h2, h3, .title, .item-title')
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                
                # Extract date
                date_elem = item.select_one('.date, .datetime, time, .item-date')
                date = date_elem.get_text().strip() if date_elem else "No date"
                
                # If no date element found, try to extract date from text
                if date == "No date":
                    content_text = item.get_text()
                    extracted_date = extract_date_from_text(content_text)
                    if extracted_date:
                        date = extracted_date
                
                # Extract content
                content_elem = item.select_one('.content, .item-content, .text, p')
                content = content_elem.get_text().strip() if content_elem else ""
                
                # If no specific content, use all text of the element
                if not content:
                    content = item.get_text().strip()
                    # Remove the title from content to avoid duplication
                    content = content.replace(title, "", 1).strip()
                
                # Extract URL
                link = ""
                link_elem = item.select_one('a[href]')
                if link_elem:
                    link = urljoin(used_url, link_elem['href'])
                
                # Extract image
                image_url = ""
                img_elem = item.select_one('img[src]')
                if img_elem:
                    image_url = urljoin(used_url, img_elem['src'])
                
                news_items.append({
                    'title': title,
                    'date': date,
                    'content': content,
                    'url': link or used_url,
                    'image_url': image_url
                })
    
    # If no news items found with the main approach, try to extract from global content
    if not news_items:
        logger.warning("No structured news elements found, extracting from global text")
        
        # Extract full text of the page
        text = soup.get_text()
        
        # Look for patterns that look like news (title followed by date and content)
        news_patterns = re.findall(r'([A-Z][^\.]{10,100})\.?\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})?\s+([^A-Z][^\.]{50,})', text)
        
        for match in news_patterns:
            if len(match) >= 3:
                news_items.append({
                    'title': match[0].strip(),
                    'date': match[1].strip() if match[1] else "No date",
                    'content': match[2].strip(),
                    'url': used_url,
                    'image_url': ""
                })
    
    logger.info(f"Extracted {len(news_items)} news items")
    return news_items