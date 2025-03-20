"""
Extractors for staff information from research institute websites.
"""
import re
from urllib.parse import urljoin


def extract_staff(session_manager, base_url, logger):
    """
    Extract staff information using advanced techniques.
    
    Args:
        session_manager: SessionManager instance
        base_url: Base URL of the website
        logger: Logger instance
        
    Returns:
        List of dictionaries with staff information
    """
    logger.info("Extracting staff information")
    staff_urls = [
        urljoin(base_url, "index.php/en/people"),
        urljoin(base_url, "index.php/es/personal"),
        urljoin(base_url, "index.php/en/staff"),
        urljoin(base_url, "personal"),
        urljoin(base_url, "staff"),
        urljoin(base_url, "people"),
        urljoin(base_url, "team"),
    ]
    
    # Try different URLs until a valid one is found
    soup = None
    used_url = None
    
    for url in staff_urls:
        # Use Selenium to load dynamic content
        soup = session_manager.get_soup(url, use_selenium=True)
        if soup:
            used_url = url
            logger.debug(f"Staff URL found: {url}")
            break
    
    if not soup:
        logger.error("Could not find the staff page")
        return []
    
    staff = []
    
    # Strategy 1: Look for staff tables
    tables = soup.select('table')
    
    if tables:
        logger.debug(f"Found {len(tables)} tables")
        
        for table in tables:
            rows = table.select('tr')
            
            # If very few rows, might not be a staff table
            if len(rows) < 3:
                continue
            
            # Extract headers if they exist
            headers = []
            header_row = rows[0]
            header_cells = header_row.select('th')
            
            if header_cells:
                for cell in header_cells:
                    headers.append(cell.text.strip().lower())
            else:
                # If no th cells, use first row as reference
                for cell in rows[0].select('td'):
                    headers.append(cell.text.strip().lower())
            
            # Check if this table appears to contain staff information
            is_staff_table = any(keyword in " ".join(headers).lower() for keyword in 
                                ['name', 'position', 'email', 'phone', 'department'])
            
            if not is_staff_table:
                continue
            
            # Map headers to standard fields
            header_mapping = {}
            for i, header in enumerate(headers):
                if any(name in header for name in ['name', 'nombre']):
                    header_mapping['name'] = i
                elif any(position in header for position in ['position', 'cargo', 'puesto']):
                    header_mapping['position'] = i
                elif any(email in header for email in ['email', 'e-mail', 'correo']):
                    header_mapping['email'] = i
                elif any(phone in header for phone in ['phone', 'telefono', 'teléfono']):
                    header_mapping['phone'] = i
                elif any(dept in header for dept in ['department', 'departamento', 'group', 'grupo']):
                    header_mapping['department'] = i
            
            # If we don't detect at least name, this table might not be staff
            if 'name' not in header_mapping:
                continue
            
            # Process data rows (skip first if headers)
            start_idx = 1 if header_cells else 0
            for row in rows[start_idx:]:
                cells = row.select('td')
                
                if len(cells) < max(header_mapping.values()) + 1:
                    continue
                
                person = {}
                
                # Extract information based on header mapping
                for field, idx in header_mapping.items():
                    if idx < len(cells):
                        person[field] = cells[idx].text.strip()
                
                # Check if name was extracted (required field)
                if 'name' in person and person['name']:
                    # Look for email in mailto links
                    if 'email' not in person or not person['email']:
                        email_elem = row.select_one('a[href^="mailto:"]')
                        if email_elem:
                            person['email'] = email_elem['href'].replace('mailto:', '')
                    
                    # Fill in missing fields
                    for field in ['position', 'email', 'phone', 'department']:
                        if field not in person:
                            person[field] = ""
                    
                    # Add page URL
                    person['source_url'] = used_url
                    
                    staff.append(person)
    
    # Strategy 2: If no tables found, look for lists or structured sections
    if not staff:
        logger.debug("No staff tables found, looking for lists or divs")
        
        # Look for elements with classes indicating staff
        person_containers = soup.select('.person, .staff-member, .team-member, .contact-info, .user-details')
        
        if person_containers:
            logger.debug(f"Found {len(person_containers)} staff containers")
            
            for container in person_containers:
                # Extract name
                name_elem = container.select_one('h3, h4, .name, strong, .title')
                if not name_elem:
                    continue
                
                name = name_elem.text.strip()
                
                # Extract position
                position_elem = container.select_one('.position, .job, .role, em, .subtitle')
                position = position_elem.text.strip() if position_elem else ""
                
                # Extract email
                email = ""
                email_elem = container.select_one('a[href^="mailto:"]')
                if email_elem:
                    email = email_elem['href'].replace('mailto:', '')
                else:
                    # Look for text that looks like email
                    email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', container.get_text())
                    if email_match:
                        email = email_match.group(0)
                
                # Extract phone
                phone = ""
                phone_elem = container.select_one('.phone, .tel, .telephone')
                if phone_elem:
                    phone = phone_elem.text.strip()
                else:
                    # Look for phone pattern
                    phone_match = re.search(r'(?:Telephone|Phone|Tel)[:.\s]+([+\d\s\(\).-]{7,})', container.get_text())
                    if phone_match:
                        phone = phone_match.group(1).strip()
                
                # Extract department/group
                department = ""
                dept_elem = container.select_one('.department, .dept, .group')
                if dept_elem:
                    department = dept_elem.text.strip()
                
                staff.append({
                    'name': name,
                    'position': position,
                    'email': email,
                    'phone': phone,
                    'department': department,
                    'source_url': used_url
                })
        else:
            # Strategy 3: Look for lists (ul/li) that might contain staff
            staff_lists = soup.select('ul')
            
            for ul in staff_lists:
                # Check if this list appears to contain staff
                list_text = ul.get_text().lower()
                if any(term in list_text for term in ['professor', 'doctor', 'researcher', 'phd']):
                    list_items = ul.select('li')
                    
                    for li in list_items:
                        text = li.get_text().strip()
                        if not text or len(text) < 5:
                            continue
                        
                        # Try to separate name and position
                        parts = re.split(r'[,;:-]', text, 1)
                        
                        name = parts[0].strip()
                        position = parts[1].strip() if len(parts) > 1 else ""
                        
                        # Extract email if it exists
                        email = ""
                        email_elem = li.select_one('a[href^="mailto:"]')
                        if email_elem:
                            email = email_elem['href'].replace('mailto:', '')
                        else:
                            email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
                            if email_match:
                                email = email_match.group(0)
                        
                        staff.append({
                            'name': name,
                            'position': position,
                            'email': email,
                            'phone': "",
                            'department': "",
                            'source_url': used_url
                        })
    
    # Strategy 4: Last resort - analyze full text
    if not staff:
        logger.debug("No structured elements found, analyzing full text")
        
        content = soup.select_one('.item-page, .content, #content, main')
        if content:
            text = content.get_text()
            
            # Look for patterns that look like staff information
            # Pattern 1: Name, position
            person_patterns = [
                r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)[,:\.]?\s+((?:Professor|Prof|Dr|Director|Researcher|Head)[^,\n]+)',
                r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)[,:\.]?\s+([\w\s]+@[\w\s]+\.[a-z]{2,3})'
            ]
            
            for pattern in person_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) >= 2:
                        name = match[0].strip()
                        info = match[1].strip()
                        
                        # Determine if second group is position or email
                        if '@' in info:
                            position = ""
                            email = info
                        else:
                            position = info
                            email = ""
                        
                        staff.append({
                            'name': name,
                            'position': position,
                            'email': email,
                            'phone': "",
                            'department': "",
                            'source_url': used_url
                        })
    
    # Remove duplicates based on name
    unique_staff = []
    seen_names = set()
    
    for person in staff:
        # Normalize name for comparison
        norm_name = re.sub(r'\W+', ' ', person['name'].lower()).strip()
        
        if norm_name and norm_name not in seen_names:
            seen_names.add(norm_name)
            
            # Ensure all necessary fields are present
            for field in ['position', 'email', 'phone', 'department', 'source_url']:
                if field not in person:
                    person[field] = ""
            
            unique_staff.append(person)
    
    logger.info(f"Extracted {len(unique_staff)} unique staff entries")
    return unique_staff