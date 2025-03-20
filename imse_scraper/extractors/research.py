"""
Extractors for research group data from institute websites.
"""
import re
from urllib.parse import urljoin


def extract_research_groups(session_manager, base_url, logger, staff_data=None, sections=None):
    """
    Extract information about research groups.
    
    Args:
        session_manager: SessionManager instance
        base_url: Base URL of the website
        logger: Logger instance
        staff_data: Optional staff data to help identify research groups
        sections: Optional website sections data
        
    Returns:
        List of dictionaries with research group information
    """
    logger.info("Extracting research groups")
    research_urls = [
        urljoin(base_url, "index.php/en/research"),
        urljoin(base_url, "index.php/es/investigacion"),
        urljoin(base_url, "investigacion"),
        urljoin(base_url, "research"),
        urljoin(base_url, "research-groups"),
        urljoin(base_url, "en/research-groups"),
    ]
    
    groups = []
    
    # Try different URLs until research group information is found
    for url in research_urls:
        soup = session_manager.get_soup(url, use_selenium=True)  # Use Selenium for dynamic content
        if not soup:
            continue
            
        logger.debug(f"Analyzing URL for research groups: {url}")
        
        # 1. Look for sections that look like research groups
        group_candidates = []
        
        # Look for headers that might be group names
        headers = soup.select('h2, h3, h4')
        for header in headers:
            header_text = header.get_text().strip()
            
            # Filter headers that are likely group names
            if len(header_text) > 10 and not header_text.lower().startswith(('index', 'table')):
                # Take the next element as description
                description = ""
                next_elem = header.find_next('p')
                if next_elem:
                    description = next_elem.get_text().strip()
                
                # Look for researchers associated with the group
                researchers = []
                researchers_elem = header.find_next('ul')
                if researchers_elem:
                    for li in researchers_elem.find_all('li'):
                        researchers.append(li.get_text().strip())
                
                group_candidates.append({
                    'name': header_text,
                    'description': description,
                    'researchers': researchers
                })
        
        # If we found at least one candidate group, consider that we've found information
        if group_candidates:
            logger.debug(f"Found {len(group_candidates)} potential groups in {url}")
            groups.extend(group_candidates)
            break
    
    # If no groups found on main pages, try to extract from site structure
    if not groups:
        logger.debug("Looking for groups in site structure")
        
        # Get all sections if not provided
        if not sections:
            from imse_scraper.extractors.base import extract_main_sections
            sections = extract_main_sections(session_manager, base_url, logger)
        
        # Look for specific research group section
        research_section = None
        for section in sections:
            if any(term in section['title'].lower() for term in ['group', 'research', 'investigación']):
                research_section = section
                break
        
        if research_section:
            logger.debug(f"Analyzing specific section: {research_section['title']}")
            soup = session_manager.get_soup(research_section['url'], use_selenium=True)
            
            if soup:
                # Try to extract specific information from this page
                main_content = soup.select_one('.item-page, #content, main')
                
                if main_content:
                    # Look for divisions that could be groups
                    divisions = main_content.select('div.item, article, section')
                    
                    if divisions:
                        for div in divisions:
                            title_elem = div.select_one('h2, h3, h4, .title')
                            if not title_elem:
                                continue
                                
                            name = title_elem.get_text().strip()
                            
                            desc_elem = div.select_one('p, .description')
                            description = desc_elem.get_text().strip() if desc_elem else ""
                            
                            groups.append({
                                'name': name,
                                'description': description,
                                'researchers': []
                            })
                    else:
                        # If no clear divisions, try to extract from headers and paragraphs
                        headers = main_content.select('h2, h3')
                        for header in headers:
                            name = header.get_text().strip()
                            
                            # Extract description (next paragraph)
                            description = ""
                            next_p = header.find_next('p')
                            if next_p:
                                description = next_p.get_text().strip()
                            
                            groups.append({
                                'name': name,
                                'description': description,
                                'researchers': []
                            })
    
    # If still no groups, try to analyze staff page
    if not groups:
        logger.debug("Trying to extract research groups from staff page")
        
        if not staff_data:
            from imse_scraper.extractors.staff import extract_staff
            staff_data = extract_staff(session_manager, base_url, logger)
        
        if staff_data:
            # Try to group staff by departments or groups
            departments = {}
            
            for person in staff_data:
                if 'position' in person and person['position']:
                    # Try to extract group/department from position
                    position = person['position'].lower()
                    
                    # Look for keywords indicating a group
                    for keyword in ['group', 'grupo', 'department', 'departamento', 'area', 'team']:
                        if keyword in position:
                            # Extract group name (text after keyword)
                            match = re.search(f"{keyword}[:\s]+([^,;]+)", position, re.IGNORECASE)
                            if match:
                                group_name = match.group(1).strip()
                                
                                if group_name not in departments:
                                    departments[group_name] = []
                                
                                departments[group_name].append(person['name'])
            
            # Convert departments to groups
            for dept_name, members in departments.items():
                if len(members) >= 2:  # Only consider as group if there are at least 2 members
                    groups.append({
                        'name': dept_name,
                        'description': f"Group extracted from staff information with {len(members)} members.",
                        'researchers': members
                    })
    
    # Normalize group data
    for group in groups:
        # Ensure we have all fields
        if 'name' not in group:
            group['name'] = "Unnamed Group"
        
        if 'description' not in group:
            group['description'] = ""
        
        if 'researchers' not in group:
            group['researchers'] = []
        elif isinstance(group['researchers'], list):
            group['researchers'] = [r.strip() for r in group['researchers'] if r.strip()]
        
        # Create additional field to show researchers as text
        if isinstance(group['researchers'], list) and group['researchers']:
            group['researchers_text'] = ", ".join(group['researchers'])
        else:
            group['researchers_text'] = ""
    
    logger.info(f"Extracted {len(groups)} research groups")
    return groups