"""
Extractors for publication data from research institute websites.
"""
import re
from urllib.parse import urljoin


def extract_publications(session_manager, base_url, logger, limit=50):
    """
    Extract scientific publications using advanced techniques.
    
    Args:
        session_manager: SessionManager instance
        base_url: Base URL of the website
        logger: Logger instance
        limit: Maximum number of publications to extract
        
    Returns:
        List of dictionaries with publication information
    """
    logger.info("Extracting publications")
    publications_urls = [
        urljoin(base_url, "index.php/en/publications"),
        urljoin(base_url, "index.php/es/publicaciones"),
        urljoin(base_url, "publicaciones"),
        urljoin(base_url, "publications"),
        urljoin(base_url, "en/publications"),
    ]
    
    # Try different URLs until a valid one is found
    soup = None
    used_url = None
    
    for url in publications_urls:
        # Use Selenium for handling dynamic content
        soup = session_manager.get_soup(url, use_selenium=True)
        if soup:
            used_url = url
            logger.debug(f"Publications URL found: {url}")
            break
    
    if not soup:
        logger.error("Could not find the publications page")
        return []
    
    publications = []
    
    # Strategy 1: Look for structured publication elements
    pub_containers = soup.select('.publication, .paper, .article, li.publication-item')
    
    if pub_containers and len(pub_containers) > 3:
        logger.debug(f"Found {len(pub_containers)} publication containers")
        
        for container in pub_containers[:limit]:
            # Extract publication information
            pub_text = container.get_text().strip()
            
            # Look for common patterns in academic publications
            # 1. Authors followed by title in quotes
            authors_match = re.search(r'^((?:[A-Z][^"]+),(?:[A-Z][^"]+)(?:,\s*(?:and|y))?[^"]+)', pub_text)
            
            # 2. Title usually in quotes or after authors
            title_match = re.search(r'["\'](.*?)["\']', pub_text)
            if not title_match:
                title_match = re.search(r'(?:,|\.)\s+([^,.]+\.)(?=\s+[A-Z])', pub_text)
            
            # 3. Venue (journal/conference)
            venue_match = re.search(r'(?:["\'].*?["\'][\.,]\s*)(.*?)(?:,|\.|vol|volume)', pub_text, re.IGNORECASE)
            
            # 4. Year (usually 4 digits)
            year_match = re.search(r'(?:^|\s)(\d{4})(?:\)|\.|\s|$)', pub_text)
            
            # 5. DOI if available
            doi_match = re.search(r'doi[\s:]*([^\s,\.]+)', pub_text, re.IGNORECASE)
            
            # Create publication object with extracted information
            publication = {
                'authors': authors_match.group(1).strip() if authors_match else "",
                'title': title_match.group(1).strip() if title_match else "",
                'venue': venue_match.group(1).strip() if venue_match else "",
                'year': year_match.group(1) if year_match else "",
                'doi': doi_match.group(1) if doi_match else "",
                'url': used_url,
                'full_text': pub_text[:1000]  # Limit length of full text
            }
            
            # Only add if we have at least title or authors
            if publication['title'] or publication['authors']:
                publications.append(publication)
    
    # Strategy 2: If no structured publications found, look in full text
    if not publications:
        logger.debug("No structured publications found, searching in full text")
        
        # Get main content
        main_content = soup.select_one('.item-page, article, .content, #content, main')
        
        if main_content:
            text = main_content.get_text()
            
            # Common patterns for scientific publications
            patterns = [
                # Pattern 1: Authors. "Title". Venue, Year.
                r'([A-Z][^\.,"]+(?:(?:,| and | y )[A-Z][^\.,"]+)+)\.\s+"([^"]+)"\.\s+([^,]+),\s+(\d{4})',
                
                # Pattern 2: Authors. Title. Venue, Year.
                r'([A-Z][^\.]+(?:,\s*[A-Z][^\.]+)+)\.\s+([^\.]+)\.\s+([^,]+),\s+(\d{4})',
                
                # Pattern 3: Year. Authors. "Title". Venue.
                r'(\d{4})\.\s+([A-Z][^\.]+(?:,\s*[A-Z][^\.]+)+)\.\s+"([^"]+)"\.\s+([^,\.]+)'
            ]
            
            # Try different patterns until enough publications are found
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    logger.debug(f"Found {len(matches)} publications with pattern: {pattern}")
                    
                    for match in matches[:limit]:
                        if len(match) >= 4:
                            if pattern == patterns[0]:
                                # Pattern 1: Authors, Title, Venue, Year
                                publication = {
                                    'authors': match[0].strip(),
                                    'title': match[1].strip(),
                                    'venue': match[2].strip(),
                                    'year': match[3].strip(),
                                    'doi': "",
                                    'url': used_url,
                                    'full_text': match[0] + match[1] + match[2] + match[3]
                                }
                                publications.append(publication)
                            elif pattern == patterns[1]:
                                # Pattern 2: Authors, Title, Venue, Year
                                publication = {
                                    'authors': match[0].strip(),
                                    'title': match[1].strip(),
                                    'venue': match[2].strip(),
                                    'year': match[3].strip(),
                                    'doi': "",
                                    'url': used_url,
                                    'full_text': match[0] + match[1] + match[2] + match[3]
                                }
                                publications.append(publication)
                            elif pattern == patterns[2]:
                                # Pattern 3: Year, Authors, Title, Venue
                                publication = {
                                    'year': match[0].strip(),
                                    'authors': match[1].strip(),
                                    'title': match[2].strip(),
                                    'venue': match[3].strip(),
                                    'doi': "",
                                    'url': used_url,
                                    'full_text': match[0] + match[1] + match[2] + match[3]
                                }
                                publications.append(publication)
                    
                    # If we find enough publications, stop searching
                    if len(publications) >= limit // 2:
                        break
    
    # Strategy 3: Look for links to articles or PDFs that might be publications
    if len(publications) < limit // 2:
        logger.debug("Looking for links to publications")
        
        pdf_links = soup.select('a[href$=".pdf"]')
        for link in pdf_links[:limit - len(publications)]:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            if text and len(text) > 10:  # Only consider links with descriptive text
                # Try to extract information from the link text
                authors = ""
                title = text
                year = ""
                
                # Look for year in filename or text
                year_match = re.search(r'(?:^|\s|_)(\d{4})(?:\s|_|$)', href + " " + text)
                if year_match:
                    year = year_match.group(1)
                
                publications.append({
                    'authors': authors,
                    'title': title[:150],  # Limit title length
                    'venue': "",
                    'year': year,
                    'doi': "",
                    'url': urljoin(used_url, href),
                    'full_text': text
                })
    
    # Remove duplicates based on title
    unique_pubs = []
    seen_titles = set()
    
    for pub in publications:
        # Normalize title for comparison
        norm_title = re.sub(r'\W+', ' ', pub['title'].lower()).strip()
        
        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            unique_pubs.append(pub)
    
    logger.info(f"Extracted {len(unique_pubs)} unique publications")
    return unique_pubs