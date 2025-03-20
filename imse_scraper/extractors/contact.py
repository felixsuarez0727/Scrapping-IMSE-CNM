"""
Extractors for contact information from research institute websites.
"""
import re
from urllib.parse import urljoin


def extract_contact_info(session_manager, base_url, logger):
    """
    Extract institute contact information.
    
    Args:
        session_manager: SessionManager instance
        base_url: Base URL of the website
        logger: Logger instance
        
    Returns:
        Dictionary with contact information
    """
    logger.info("Extracting contact information")
    contact_urls = [
        urljoin(base_url, "index.php/en/contact"),
        urljoin(base_url, "index.php/es/contacto"),
        urljoin(base_url, "contacto"),
        urljoin(base_url, "contact"),
        base_url  # Sometimes contact information is in the footer
    ]
    
    contact_info = {
        'institute_name': "Institute of Microelectronics of Seville (IMSE-CNM)",
        'address': '',
        'city': '',
        'postal_code': '',
        'country': 'Spain',
        'phone': '',
        'fax': '',
        'email': '',
        'website': base_url,
        'social_media': {}
    }
    
    # Try different URLs until contact information is found
    for url in contact_urls:
        soup = session_manager.get_soup(url, use_selenium=True)  # Use Selenium to capture dynamic content
        if not soup:
            continue
        
        logger.debug(f"Looking for contact information in: {url}")
        
        # Look for specific contact content
        contact_divs = soup.select('.contact, .address, .contact-info, footer, .footer')
        
        if not contact_divs and url == base_url:
            # If we're on the main page and no specific divs found, 
            # look in the footer
            contact_divs = soup.select('footer, .footer, #footer')
        
        if contact_divs:
            for div in contact_divs:
                text = div.get_text()
                
                # Extract address
                address_patterns = [
                    r'Address:?\s*([^,\n]+(?:,[^,\n]+){0,3})',
                    r'(?:Ave\.?|Avenue|Street|St).*?(?:\d+[^\d\n,]*)',
                ]
                
                for pattern in address_patterns:
                    address_match = re.search(pattern, text, re.IGNORECASE)
                    if address_match:
                        contact_info['address'] = address_match.group(0).strip()
                        break
                
                # Extract postal code
                postal_match = re.search(r'(?:ZIP|Postal Code)?\s*(\d{5})', text)
                if postal_match:
                    contact_info['postal_code'] = postal_match.group(1).strip()
                
                # Extract city
                city_patterns = [
                    r'(?:Seville|Sevilla)',
                    r'(?:,\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s*\d{5})'
                ]
                
                for pattern in city_patterns:
                    city_match = re.search(pattern, text, re.IGNORECASE)
                    if city_match:
                        if city_match.groups():
                            contact_info['city'] = city_match.group(1).strip()
                        else:
                            contact_info['city'] = city_match.group(0).strip()
                        break
                
                # Extract phone
                phone_patterns = [
                    r'Telephone:?\s*([+\d\s\(\)\.,-]{7,})',
                    r'Phone:?\s*([+\d\s\(\)\.,-]{7,})',
                    r'(?:Tel|Tlf)\.?:?\s*([+\d\s\(\)\.,-]{7,})'
                ]
                
                for pattern in phone_patterns:
                    phone_match = re.search(pattern, text, re.IGNORECASE)
                    if phone_match:
                        contact_info['phone'] = phone_match.group(1).strip()
                        break
                
                # Extract fax
                fax_match = re.search(r'Fax:?\s*([+\d\s\(\)\.,-]{7,})', text, re.IGNORECASE)
                if fax_match:
                    contact_info['fax'] = fax_match.group(1).strip()
                
                # Extract email
                email_elem = div.select_one('a[href^="mailto:"]')
                if email_elem:
                    contact_info['email'] = email_elem['href'].replace('mailto:', '')
                else:
                    # Look for email pattern in text
                    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                    if email_match:
                        contact_info['email'] = email_match.group(0)
                
                # Extract social media
                social_media = {
                    'twitter': None,
                    'facebook': None,
                    'linkedin': None,
                    'youtube': None,
                    'instagram': None
                }
                
                # Look for social media links
                social_links = div.select('a[href*="twitter"], a[href*="facebook"], a[href*="linkedin"], a[href*="youtube"], a[href*="instagram"]')
                for link in social_links:
                    href = link.get('href', '')
                    for network in social_media.keys():
                        if network in href:
                            social_media[network] = href
                
                # Add found social media
                contact_info['social_media'] = {k: v for k, v in social_media.items() if v}
        
        # If we've found at least address or phone, consider that we have valid information
        if contact_info['address'] or contact_info['phone']:
            break
    
    # If we still don't have city but we have address, try to extract from address
    if not contact_info['city'] and contact_info['address']:
        city_match = re.search(r'(?:,\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', contact_info['address'])
        if city_match:
            contact_info['city'] = city_match.group(1).strip()
        else:
            # Assume Seville if no other information
            contact_info['city'] = "Seville"
    
    # Check for Twitter and LinkedIn links on the entire page
    if not contact_info['social_media'] and soup:
        social_links = soup.select('a[href*="twitter"], a[href*="facebook"], a[href*="linkedin"], a[href*="youtube"], a[href*="instagram"]')
        social_media = {}
        
        for link in social_links:
            href = link.get('href', '')
            if 'twitter' in href:
                social_media['twitter'] = href
            elif 'facebook' in href:
                social_media['facebook'] = href
            elif 'linkedin' in href:
                social_media['linkedin'] = href
            elif 'youtube' in href:
                social_media['youtube'] = href
            elif 'instagram' in href:
                social_media['instagram'] = href
        
        if social_media:
            contact_info['social_media'] = social_media
    
    logger.info("Contact information extracted")
    return contact_info