"""
Extractors for project information from research institute websites.
"""
import re
from urllib.parse import urljoin


def extract_projects(session_manager, base_url, logger):
    """
    Extract information about research projects.
    
    Args:
        session_manager: SessionManager instance
        base_url: Base URL of the website
        logger: Logger instance
        
    Returns:
        List of dictionaries with project information
    """
    logger.info("Extracting project information")
    projects_urls = [
        urljoin(base_url, "index.php/en/projects"),
        urljoin(base_url, "index.php/es/proyectos"),
        urljoin(base_url, "proyectos"),
        urljoin(base_url, "projects"),
        urljoin(base_url, "en/projects"),
    ]
    
    # Try different URLs until a valid one is found
    soup = None
    used_url = None
    
    for url in projects_urls:
        soup = session_manager.get_soup(url, use_selenium=True)  # Use Selenium for JS
        if soup:
            used_url = url
            logger.debug(f"Projects URL found: {url}")
            break
    
    if not soup:
        logger.error("Could not find the projects page")
        return []
    
    projects = []
    
    # Strategy 1: Look for project containers
    project_containers = soup.select('.project, .item, .project-item')
    
    if project_containers:
        logger.debug(f"Found {len(project_containers)} project containers")
        
        for container in project_containers:
            # Extract title
            title_elem = container.select_one('h2, h3, h4, .title, .project-title')
            if not title_elem:
                continue
            
            title = title_elem.text.strip()
            
            # Extract description
            desc_elems = container.select('p, .description, .content')
            description = " ".join([elem.text.strip() for elem in desc_elems]) if desc_elems else ""
            
            # Extract period (dates)
            period = ""
            period_elem = container.select_one('.period, .dates, .timeline')
            if period_elem:
                period = period_elem.text.strip()
            else:
                # Look for date pattern in description
                period_match = re.search(r'(\d{4})\s*-\s*(\d{4}|\w+)', description)
                if period_match:
                    period = period_match.group(0)
            
            # Extract funding
            funding = ""
            funding_elem = container.select_one('.funding, .sponsor, .financed-by')
            if funding_elem:
                funding = funding_elem.text.strip()
            else:
                # Look for funding mention in text
                funding_match = re.search(r'(?:funded by|grant)[^\n\.]+', description, re.IGNORECASE)
                if funding_match:
                    funding = funding_match.group(0).strip()
            
            projects.append({
                'title': title,
                'description': description,
                'period': period,
                'funding': funding,
                'url': used_url
            })
    else:
        # Strategy 2: Look for structured elements on the page
        logger.debug("No project containers found, looking for alternative structure")
        
        # Look for headers that might be project titles
        headers = soup.select('h2, h3, h4')
        
        current_project = None
        
        for header in headers:
            header_text = header.text.strip()
            
            # Ignore headers that are probably not projects
            if len(header_text) < 10 or any(term in header_text.lower() for term in ['index', 'list', 'ongoing projects']):
                continue
            
            # If we already had a project in process, save it before creating a new one
            if current_project:
                projects.append(current_project)
            
            # Create new project
            current_project = {
                'title': header_text,
                'description': "",
                'period': "",
                'funding': "",
                'url': used_url
            }
            
            # Look for period in title
            period_match = re.search(r'(?:^|\(|\[)(\d{4})\s*[-–]\s*(\d{4}|\w+)(?:\)|\]|$)', header_text)
            if period_match:
                current_project['period'] = period_match.group(0).strip('()[]')
            
            # Extract following content (description)
            next_elems = []
            next_elem = header.find_next_sibling()
            
            while next_elem and next_elem.name not in ['h2', 'h3', 'h4']:
                if next_elem.name == 'p':
                    next_elems.append(next_elem.text.strip())
                next_elem = next_elem.find_next_sibling()
            
            if next_elems:
                current_project['description'] = " ".join(next_elems)
                
                # Look for funding in description
                funding_match = re.search(r'(?:funded by|grant)[^\n\.]+', current_project['description'], re.IGNORECASE)
                if funding_match:
                    current_project['funding'] = funding_match.group(0).strip()
                
                # If we still don't have period, look for it in description
                if not current_project['period']:
                    period_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|\w+)', current_project['description'])
                    if period_match:
                        current_project['period'] = period_match.group(0)
        
        # Add the last project if it exists
        if current_project:
            projects.append(current_project)
        
        # If still no projects found, try a more aggressive approach
        if not projects:
            logger.debug("Trying alternative approach to find projects")
            
            # Look for paragraphs that might contain project information
            content = soup.select_one('.item-page, .content, #content, main')
            
            if content:
                paragraphs = content.select('p')
                
                for i, para in enumerate(paragraphs):
                    text = para.text.strip()
                    
                    # Look for paragraphs that look like project descriptions
                    if len(text) > 100 and re.search(r'(project|research|development)', text, re.IGNORECASE):
                        # Try to extract a title from text
                        title_match = re.search(r'^([A-Z][^\.]{10,100}\.)', text)
                        title = title_match.group(1).strip() if title_match else f"Project #{i+1}"
                        
                        # Extract period if it exists
                        period_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|\w+)', text)
                        period = period_match.group(0) if period_match else ""
                        
                        # Extract funding information
                        funding_match = re.search(r'(?:funded by|grant)[^\n\.]+', text, re.IGNORECASE)
                        funding = funding_match.group(0).strip() if funding_match else ""
                        
                        projects.append({
                            'title': title,
                            'description': text,
                            'period': period,
                            'funding': funding,
                            'url': used_url
                        })
    
    # Normalize project data
    normalized_projects = []
    for project in projects:
        # Ensure we have all fields
        for field in ['title', 'description', 'period', 'funding', 'url']:
            if field not in project:
                project[field] = ""
        
        # Clean fields
        for field in project:
            if isinstance(project[field], str):
                project[field] = project[field].strip()
        
        # Only add if there's a title
        if project['title']:
            normalized_projects.append(project)
    
    logger.info(f"Extracted {len(normalized_projects)} projects")
    return normalized_projects