"""
Parsing utilities for cleaning and normalizing scraped data.
"""
import re


def clean_data(extracted_data, logger=None):
    """
    Clean and normalize all extracted data.
    
    Args:
        extracted_data: Dictionary with all extracted data
        logger: Logger instance for logging
        
    Returns:
        Dictionary with cleaned and normalized data
    """
    if logger:
        logger.info("Cleaning and normalizing data")
    else:
        print("Cleaning and normalizing data")
    
    cleaned_data = {}
    
    # Process each data type
    for data_type, data in extracted_data.items():
        if not data:
            continue
        
        if isinstance(data, list):
            cleaned_list = []
            
            for item in data:
                # Create clean copy of the item
                clean_item = {}
                
                for key, value in item.items():
                    # Convert to string if it's not a basic type
                    if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        value = str(value)
                    
                    # Clean strings
                    if isinstance(value, str):
                        # Remove extra spaces
                        value = re.sub(r'\s+', ' ', value).strip()
                        
                        # Truncate if very long
                        if len(value) > 10000:
                            value = value[:10000] + "..."
                    
                    clean_item[key] = value
                
                cleaned_list.append(clean_item)
            
            cleaned_data[data_type] = cleaned_list
        
        elif isinstance(data, dict):
            # Create clean copy of the dictionary
            clean_dict = {}
            
            for key, value in data.items():
                # Process recursively if it's a dictionary or list
                if isinstance(value, dict):
                    sub_clean = {}
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str):
                            sub_value = re.sub(r'\s+', ' ', sub_value).strip()
                            # Truncate if very long
                            if len(sub_value) > 10000:
                                sub_value = sub_value[:10000] + "..."
                        sub_clean[sub_key] = sub_value
                    clean_dict[key] = sub_clean
                elif isinstance(value, list):
                    clean_list = []
                    for item in value:
                        if isinstance(item, str):
                            item = re.sub(r'\s+', ' ', item).strip()
                            # Truncate if very long
                            if len(item) > 5000:
                                item = item[:5000] + "..."
                        elif isinstance(item, dict):
                            # Clean dictionaries within lists
                            clean_item = {}
                            for item_key, item_value in item.items():
                                if isinstance(item_value, str):
                                    item_value = re.sub(r'\s+', ' ', item_value).strip()
                                    # Truncate if very long
                                    if len(item_value) > 5000:
                                        item_value = item_value[:5000] + "..."
                                clean_item[item_key] = item_value
                            item = clean_item
                        clean_list.append(item)
                    clean_dict[key] = clean_list
                else:
                    # Clean strings
                    if isinstance(value, str):
                        value = re.sub(r'\s+', ' ', value).strip()
                        # Truncate if very long
                        if len(value) > 10000:
                            value = value[:10000] + "..."
                    clean_dict[key] = value
            
            cleaned_data[data_type] = clean_dict
    
    if logger:
        logger.info("Data cleaned and normalized")
    else:
        print("Data cleaned and normalized")
        
    return cleaned_data


def extract_date_from_text(text):
    """
    Try to extract a date from text using various patterns.
    
    Args:
        text: Text containing a date
        
    Returns:
        Extracted date string or empty string if not found
    """
    # Common date patterns
    patterns = [
        r'(\d{1,2})[/\.-](\d{1,2})[/\.-](\d{2,4})',  # DD/MM/YYYY, DD-MM-YYYY
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+)[,\s]+(\d{4})',  # DD Month YYYY
        r'([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})',  # Month DD, YYYY
        r'(\d{4})[/\.-](\d{1,2})[/\.-](\d{1,2})'  # YYYY/MM/DD, YYYY-MM-DD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return ""


def normalize_url(url, base_url):
    """
    Normalize a URL to ensure it's absolute.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs
        
    Returns:
        Normalized absolute URL
    """
    from urllib.parse import urljoin
    
    # Handle special cases
    if not url:
        return ""
    if url.startswith(('http://', 'https://')):
        return url
    if url.startswith(('#', 'javascript:', 'mailto:')):
        return ""
    
    # Join with base URL
    return urljoin(base_url, url)