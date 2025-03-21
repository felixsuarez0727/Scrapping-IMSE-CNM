"""
Extractors for project information from research institute websites.
"""
import re
from urllib.parse import urljoin


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
        urljoin(base_url, "es/proyectos.php"),  # Try this specific URL first
        urljoin(base_url, "index.php/es/proyectos"),
        urljoin(base_url, "es/proyectos"),
        urljoin(base_url, "proyectos"),
        urljoin(base_url, "index.php/en/projects"),
        urljoin(base_url, "en/projects"),
        urljoin(base_url, "projects"),
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
    
    # First, look for section titles that indicate project categories
    section_titles = soup.select('h2, h3, h4')
    section_title_texts = [title.text.strip() for title in section_titles]
    
    # Check if we're on a page with the expected structure (like in the screenshot)
    if any('vigor' in title.lower() for title in section_title_texts) or any('proyectos' in title.lower() for title in section_title_texts):
        logger.debug("Found page with project categories")
        
        # Extract projects directly from the page structure
        # First, find all links that might be project names
        project_links = soup.select('a')
        
        # Filter for links that are likely to be project names/titles
        potential_projects = []
        for link in project_links:
            link_text = link.text.strip()
            
            # Skip empty links, navigation links, etc.
            if (not link_text or len(link_text) < 4 or 
                link_text.lower() in ['es', 'en', 'inicio', 'home'] or
                any(nav in link_text.lower() for nav in ['menu', 'login', 'register'])):
                continue
                
            # Check if this looks like a project name (all caps or specific format)
            if (link_text.isupper() or 
                re.match(r'^[A-Z0-9-]{3,}$', link_text) or 
                "project" in link_text.lower() or
                "proyecto" in link_text.lower()):
                
                # Get the next elements after the link - these should be the project description
                parent = link.parent
                next_siblings = []
                
                # Collect text from the next few siblings until we hit another link or heading
                sibling = parent.next_sibling
                while sibling:
                    if (sibling.name in ['a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'] or
                        (hasattr(sibling, 'select') and sibling.select('a'))):
                        break
                    
                    if hasattr(sibling, 'text'):
                        text = sibling.text.strip()
                        if text:
                            next_siblings.append(text)
                    
                    sibling = sibling.next_sibling
                
                # Create a project entry
                project_data = {
                    'title': link_text,
                    'description': "",
                    'period': "",
                    'funding': "",
                    'url': urljoin(used_url, link.get('href', '')) if link.get('href') else used_url,
                    'principal_investigator': ""
                }
                
                # Try to find the project details after the link
                for i in range(len(next_siblings)):
                    text = next_siblings[i]
                    
                    # Check if it looks like a project description
                    if len(text) > 20 and not text.startswith('IP:'):
                        project_data['description'] = text
                    
                    # Check if it contains principal investigator info
                    if text.startswith('IP:'):
                        project_data['principal_investigator'] = text.replace('IP:', '').strip()
                
                # If we didn't find a description in the siblings, look for following paragraphs
                if not project_data['description']:
                    desc_paras = []
                    next_elem = parent
                    
                    while next_elem and len(desc_paras) < 3:
                        next_elem = next_elem.next_sibling
                        if next_elem and hasattr(next_elem, 'name') and next_elem.name == 'p':
                            text = next_elem.text.strip()
                            if text and not text.startswith('IP:'):
                                desc_paras.append(text)
                    
                    if desc_paras:
                        project_data['description'] = " ".join(desc_paras)
                
                # Try to extract period from the description
                period_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|\w+)', project_data['description'])
                if period_match:
                    project_data['period'] = period_match.group(0)
                
                potential_projects.append(project_data)
    
        # Now, look for actual project sections in the page
        # This is specifically targeting the structure shown in your screenshot
        # Look for project sections that contain a name followed by a description and IP information
        project_sections = []
        
        # Find all sections with project info
        # This targets the structure from the screenshot with blue links followed by descriptions and PI info
        for a_tag in soup.select('a'):
            # Skip links that don't look like project acronyms
            if not a_tag.text.strip() or len(a_tag.text.strip()) < 3:
                continue
                
            # Get the parent container that might hold the entire project info
            parent = a_tag.parent
            
            # Look for the next sibling element that might contain the project title/description
            next_elem = parent.next_sibling
            while next_elem and (not hasattr(next_elem, 'name') or not next_elem.name):
                next_elem = next_elem.next_sibling
                
            if next_elem and hasattr(next_elem, 'text'):
                description = next_elem.text.strip()
                
                # Look for PI information
                pi_elem = next_elem.next_sibling
                pi_info = ""
                
                while pi_elem and (not hasattr(pi_elem, 'name') or not pi_elem.name):
                    pi_elem = pi_elem.next_sibling
                    
                if pi_elem and hasattr(pi_elem, 'text') and 'IP:' in pi_elem.text:
                    pi_info = pi_elem.text.strip()
                
                # Add to project sections if we have enough info
                if description and len(description) > 20:
                    project_sections.append({
                        'acronym': a_tag.text.strip(),
                        'title': description,
                        'pi': pi_info.replace('IP:', '').strip() if pi_info else "",
                        'url': urljoin(used_url, a_tag.get('href', '')) if a_tag.get('href') else used_url
                    })
        
        # If we found project sections with the expected structure, process them
        if project_sections:
            logger.debug(f"Found {len(project_sections)} project sections with expected structure")
            
            for section in project_sections:
                projects.append({
                    'title': f"{section['acronym']} - {section['title']}",
                    'description': section['title'],
                    'principal_investigator': section['pi'],
                    'period': "",
                    'funding': "",
                    'url': section['url']
                })
        else:
            # Use the potential projects we found earlier
            projects = potential_projects
    
    # If no projects found with the specific page structure, fall back to generic methods
    if not projects:
        logger.debug("No specific project structure found, using generic methods")
        
        # Look for project containers
        project_containers = soup.select('.project, .item, .project-item, div[class*="project"]')
        
        if project_containers:
            logger.debug(f"Found {len(project_containers)} generic project containers")
            
            for container in project_containers:
                # Extract title
                title_elem = container.select_one('h2, h3, h4, .title, .project-title, strong, b')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Skip non-project titles
                if len(title) < 4 or title.lower() in ['es', 'en', 'inicio', 'home']:
                    continue
                
                # Extract description
                desc_elems = container.select('p, .description, .content')
                description = " ".join([elem.text.strip() for elem in desc_elems]) if desc_elems else ""
                
                # Extract principal investigator
                pi = ""
                pi_elem = container.select_one('*:contains("IP:")')
                if pi_elem:
                    pi_text = pi_elem.text.strip()
                    pi_match = re.search(r'IP:\s*(.*?)(?:$|;|\.|,)', pi_text)
                    if pi_match:
                        pi = pi_match.group(1).strip()
                
                # Extract period
                period = ""
                period_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|\w+)', description)
                if period_match:
                    period = period_match.group(0)
                
                # Extract funding
                funding = ""
                funding_match = re.search(r'(?:financiado por|funded by)[^\n\.]+', description, re.IGNORECASE)
                if funding_match:
                    funding = funding_match.group(0).strip()
                
                projects.append({
                    'title': title,
                    'description': description,
                    'principal_investigator': pi,
                    'period': period,
                    'funding': funding,
                    'url': used_url
                })
    
    # If still no projects, try parsing the entire page text for sections that look like projects
    if not projects:
        logger.debug("No project containers found, analyzing entire page text")
        
        # Get all text from the page
        text = soup.get_text()
        
        # Look for sections that might be projects
        # This pattern looks for uppercase acronyms followed by descriptions
        project_pattern = r'([A-Z0-9-]{3,})\s*\n+\s*([^\n]{20,})\s*\n+\s*IP:\s*([^\n]+)'
        
        matches = re.findall(project_pattern, text)
        for match in matches:
            if len(match) >= 3:
                projects.append({
                    'title': f"{match[0]} - {match[1]}",
                    'description': match[1],
                    'principal_investigator': match[2].strip(),
                    'period': "",
                    'funding': "",
                    'url': used_url
                })
    
    # Ensure all projects have the required fields and normalize data
    normalized_projects = []
    for project in projects:
        # Ensure all required fields exist
        for field in ['title', 'description', 'period', 'funding', 'url', 'principal_investigator']:
            if field not in project:
                project[field] = ""
        
        # Clean fields
        for field in project:
            if isinstance(project[field], str):
                project[field] = project[field].strip()
        
        # Only add if there's a meaningful title
        if project['title'] and len(project['title']) > 3:
            normalized_projects.append(project)
    
    # Remove duplicates based on title
    unique_projects = []
    seen_titles = set()
    
    for project in normalized_projects:
        # Normalize title for comparison
        norm_title = re.sub(r'\W+', ' ', project['title'].lower()).strip()
        
        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            unique_projects.append(project)
    
    logger.info(f"Extracted {len(unique_projects)} projects")
    return unique_projects


def is_valid_project_title(title):
    """
    Check if a title seems to be a valid project title.
    
    Args:
        title: Title to check
        
    Returns:
        Boolean indicating if it's likely a valid project title
    """
    # Exclude common non-project titles
    exclude_terms = [
        'áreas', 'areas', 'introducción', 'introduction', 'listado', 'list',
        'qué hacemos', 'what we do', 'webs', 'web', 'video', 'formación', 'training',
        'nueva directora', 'director', '11 de febrero', 'día', 'day', 'niña', 'girl',
        'science', 'publicaciones', 'publications', 'recientes', 'recent',
        'institucional', 'institutional', 'relacionadas', 'related'
    ]
    
    if any(term in title.lower() for term in exclude_terms):
        return False
    
    # Look for project indicators
    project_indicators = [
        'proyecto', 'project', 'grant', 'financiado', 'funded', 'investigación', 'research',
        'desarrollo', 'development', 'ministerio', 'european', 'EU', 'nacional', 'TEC', 'RTI'
    ]
    
    # Return True if title contains a project indicator or a year
    return any(indicator in title.lower() for indicator in project_indicators) or re.search(r'\d{4}', title)


def is_valid_project(project):
    """
    Check if a project entry seems to be a valid research project.
    
    Args:
        project: Project dictionary to check
        
    Returns:
        Boolean indicating if it's likely a valid project
    """
    # Must have a title
    if not project['title']:
        return False
    
    # Title validation
    if not is_valid_project_title(project['title']):
        # If title doesn't look like a project, check if description clearly indicates a project
        project_indicators = [
            'proyecto', 'project', 'grant', 'financiado', 'funded', 'investigación', 'research',
            'desarrollo', 'development', 'ministerio', 'european', 'EU', 'nacional'
        ]
        
        if not (project['description'] and any(indicator in project['description'].lower() for indicator in project_indicators)):
            return False
    
    # Skip entries with very short descriptions and no period or funding info
    if (len(project['description']) < 50 and 
        not project['period'] and 
        not project['funding'] and 
        'LEER MÁS' in project['description']):
        return False
    
    return True


def extract_period(text):
    """
    Extract project period from text.
    
    Args:
        text: Text to extract period from
        
    Returns:
        Extracted period string or empty string if not found
    """
    # Look for common period patterns
    patterns = [
        r'(\d{4})\s*[-–]\s*(\d{4}|\w+)',  # 2020-2023 or 2020-present
        r'(?:period|período|duration|duración|vigencia)[:\s]+([^.]*\d{4}[^.]*)',  # Period: 2020-2023
        r'(?:from|desde)\s+\d{4}\s+(?:to|hasta|until)\s+\d{4}',  # From 2020 to 2023
        r'\(\s*\d{4}\s*[-–]\s*\d{4}\s*\)'  # (2020-2023)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if match.groups():
                return match.group(1).strip()
            else:
                return match.group(0).strip()
    
    return ""


def extract_funding(text):
    """
    Extract project funding information from text.
    
    Args:
        text: Text to extract funding from
        
    Returns:
        Extracted funding string or empty string if not found
    """
    # Look for common funding patterns
    patterns = [
        r'(?:financiad[oa] por|funded by|grant|financiación)[^\n\.]+(?:ministerio|european|EU|commission|nacional)[^\n\.]+',
        r'(?:project|proyecto|ref)[\.:\s]+[A-Z0-9-]+/\d+',  # Project ref: TEC2015-123456
        r'(?:grant|ayuda|funding)[\.:\s]+[A-Z0-9-]+',
        r'(?:RTI|TEC|BES|FPI|FPU|ERC|H2020)[A-Z0-9-]+/\d+'  # Common Spanish and European funding codes
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return ""


def extract_project_title_from_text(text):
    """
    Extract a likely project title from text.
    
    Args:
        text: Text to extract title from
        
    Returns:
        Extracted title or None if no good candidate found
    """
    # Look for patterns that suggest project titles
    patterns = [
        r'"([^"]+)"',  # Text in quotes
        r'["\']([^"\']+)["\']',  # Text in quotes (any type)
        r'(?:project|proyecto|entitled)[:\s]+([^.]+)',  # After "Project:" or similar
        r'([A-Z][A-Za-z\s]+)(?:\s*[-:]\s|\.\s+)',  # Capitalized phrase followed by colon or period
        r'([A-Z][^.]{10,80}?\.)',  # Capitalized sentence of reasonable length
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1).strip():
            candidate = match.group(1).strip()
            # Check if the candidate looks like a project title
            if len(candidate) > 10 and not candidate.lower().startswith(('http', 'www')):
                return candidate
    
    # Look for project reference codes that might indicate a title
    code_match = re.search(r'(?:RTI|TEC|BES|FPI|FPU|ERC|H2020)[A-Z0-9-]+/\d+', text, re.IGNORECASE)
    if code_match:
        # Use the sentence containing the code
        code = code_match.group(0)
        sentence_match = re.search(r'[^.]*' + re.escape(code) + r'[^.]*\.', text)
        if sentence_match:
            return sentence_match.group(0).strip()
    
    return None