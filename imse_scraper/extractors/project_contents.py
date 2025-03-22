"""
Extractors for detailed project content from individual project pages.
"""
import re
from urllib.parse import urljoin


def extract_project_contents(session_manager, projects, logger):
    """
    Extract detailed content from individual project pages.
    
    Args:
        session_manager: SessionManager instance
        projects: List of projects with URLs to fetch content from
        logger: Logger instance
        
    Returns:
        Dictionary with project URLs as keys and content details as values
    """
    logger.info("Extracting detailed content from project pages")
    project_contents = {}
    
    if not projects:
        logger.warning("No projects provided to extract content from")
        return project_contents
    
    for project in projects:
        # Skip projects without URLs
        if not project.get('url'):
            continue
        
        project_url = project['url']
        
        # Skip already processed URLs
        if project_url in project_contents:
            continue
        
        logger.debug(f"Extracting content from project page: {project_url}")
        
        # Get the project page content
        soup = session_manager.get_soup(project_url, use_selenium=True)
        if not soup:
            logger.warning(f"Could not load project page: {project_url}")
            continue
        
        # Extract content
        content = {}
        
        # Project title - usually in a heading
        title_elem = soup.select_one('h1, h2, h3, .title, .page-title, .article-title')
        if title_elem:
            content['title'] = title_elem.text.strip()
        else:
            # Use the project title from the projects list
            content['title'] = project.get('title', '')
        
        # Main content
        main_content_elem = soup.select_one('.item-page, .content, #content, main, article')
        if main_content_elem:
            content['full_content'] = main_content_elem.get_text(separator='\n', strip=True)
        else:
            # Fallback to body content
            content['full_content'] = soup.get_text(separator='\n', strip=True)
        
        # Try to extract specific sections
        content['sections'] = extract_content_sections(main_content_elem or soup)
        
        # Extract images
        content['images'] = []
        for img in soup.select('img[src]'):
            src = img.get('src', '')
            if src and not src.startswith('data:'):
                content['images'].append({
                    'url': urljoin(project_url, src),
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        
        # Extract funding/grant information
        funding = extract_funding_info(content['full_content'])
        if funding:
            content['funding_info'] = funding
        
        # Extract timeline/period
        period = extract_period_info(content['full_content'])
        if period:
            content['period_info'] = period
        
        # Extract team members/investigators
        team = extract_team_info(soup, content['full_content'])
        if team:
            content['team_members'] = team
        
        # Store the full HTML for reference (optional)
        # content['html'] = str(soup)
        
        # Add to project contents
        project_contents[project_url] = content
    
    logger.info(f"Extracted content from {len(project_contents)} project pages")
    return project_contents


def extract_content_sections(soup):
    """
    Extract content divided into sections based on headings.
    
    Args:
        soup: BeautifulSoup object for the content
        
    Returns:
        List of section dictionaries with title and content
    """
    sections = []
    headings = soup.select('h1, h2, h3, h4, h5, h6')
    
    for i, heading in enumerate(headings):
        title = heading.get_text(strip=True)
        
        # Get all content until the next heading
        content = []
        current = heading.next_sibling
        
        while current and (i == len(headings) - 1 or current != headings[i + 1]):
            if hasattr(current, 'get_text'):
                text = current.get_text(strip=True)
                if text:
                    content.append(text)
            current = getattr(current, 'next_sibling', None)
        
        sections.append({
            'title': title,
            'content': '\n'.join(content)
        })
    
    return sections


def extract_funding_info(text):
    """
    Extract funding/grant information from text.
    
    Args:
        text: Text content to search in
        
    Returns:
        Dictionary with extracted funding information or empty dict if none found
    """
    funding_info = {}
    
    # Look for project reference codes
    ref_matches = re.findall(r'(?:RTI|TEC|BES|FPI|FPU|ERC|H2020|PID)[A-Z0-9-]+[-/]\d+', text)
    if ref_matches:
        funding_info['reference_codes'] = list(set(ref_matches))
    
    # Look for funding amount
    amount_matches = re.findall(r'(\d+(?:[,.]\d+)?)\s*(?:€|EUR|euros?|k€)', text, re.IGNORECASE)
    if amount_matches:
        funding_info['amounts'] = list(set(amount_matches))
    
    # Look for funding agencies
    agencies = [
        'Ministerio', 'MINECO', 'MICINN', 'European Commission', 'EU', 
        'European Union', 'H2020', 'Horizon', 'CDTI', 'Junta', 'Andalucía',
        'National', 'Regional', 'Internacional'
    ]
    
    agency_matches = []
    for agency in agencies:
        if re.search(r'\b' + re.escape(agency) + r'\b', text, re.IGNORECASE):
            agency_matches.append(agency)
    
    if agency_matches:
        funding_info['agencies'] = agency_matches
    
    return funding_info


def extract_period_info(text):
    """
    Extract project timeline/period information from text.
    
    Args:
        text: Text content to search in
        
    Returns:
        Dictionary with period information or empty dict if none found
    """
    period_info = {}
    
    # Look for start and end dates
    period_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|\w+)', text)
    if period_match:
        period_info['full_period'] = period_match.group(0)
        period_info['start_year'] = period_match.group(1)
        period_info['end_year'] = period_match.group(2)
    
    # Look for duration
    duration_match = re.search(r'(?:duración|duration)[:\s]+(\d+)(?:\s*(?:años|years|meses|months))?', text, re.IGNORECASE)
    if duration_match:
        period_info['duration'] = duration_match.group(1)
    
    return period_info


def extract_team_info(soup, text):
    """
    Extract information about team members and investigators.
    
    Args:
        soup: BeautifulSoup object for the content
        text: Text content to search in
        
    Returns:
        List of team members or empty list if none found
    """
    team_members = []
    
    # First try to find a list of team members
    member_lists = soup.select('ul, ol')
    for member_list in member_lists:
        list_text = member_list.get_text().lower()
        if ('equipo' in list_text or 'team' in list_text or 
            'investigador' in list_text or 'researcher' in list_text or
            'miembro' in list_text or 'member' in list_text):
            
            for item in member_list.select('li'):
                member_text = item.get_text(strip=True)
                if member_text and len(member_text) > 3:
                    team_members.append(member_text)
    
    # If no list found, try to extract from text
    if not team_members:
        # Look for principal investigator
        pi_match = re.search(r'(?:IP|investigador principal|principal investigator)[:\s]+([^\.;]+)', text, re.IGNORECASE)
        if pi_match:
            pi = pi_match.group(1).strip()
            if pi:
                team_members.append(f"Principal Investigator: {pi}")
        
        # Look for other team members
        team_section_match = re.search(r'(?:equipo|team|miembros|members)[^\n\.]*:\s*([^\n]+)', text, re.IGNORECASE)
        if team_section_match:
            team_section = team_section_match.group(1)
            members = re.split(r',|;|y|\band\b', team_section)
            for member in members:
                member_text = member.strip()
                if member_text and len(member_text) > 3:
                    team_members.append(member_text)
    
    return team_members