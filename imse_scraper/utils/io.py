"""
Input/Output utilities for saving scraped data to files.
"""
import os
import csv
import json


def save_to_csv(data, filename, output_dir, logger=None):
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries with data to save
        filename: Name of the CSV file (without extension)
        output_dir: Directory where the file will be saved
        logger: Logger instance for logging
        
    Returns:
        Path to the saved file or None if there was an error
    """
    if not data:
        if logger:
            logger.warning(f"No data to save to {filename}.csv")
        else:
            print(f"No data to save to {filename}.csv")
        return
    
    filepath = os.path.join(output_dir, f"{filename}.csv")
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Detect all possible fields in the data
            fieldnames = set()
            for item in data:
                for key in item.keys():
                    fieldnames.add(key)
            
            fieldnames = sorted(list(fieldnames))
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                # Ensure all values are strings to avoid errors
                clean_item = {}
                for key, value in item.items():
                    if isinstance(value, (list, dict)):
                        clean_item[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        clean_item[key] = str(value) if value is not None else ""
                
                writer.writerow(clean_item)
        
        if logger:
            logger.info(f"Data saved to {filepath}")
        else:
            print(f"Data saved to {filepath}")
        return filepath
    except Exception as e:
        if logger:
            logger.error(f"Error saving {filename}.csv: {e}")
        else:
            print(f"Error saving {filename}.csv: {e}")
        return None


def save_to_json(data, filename, output_dir, logger=None):
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save (list or dictionary)
        filename: Name of the JSON file (without extension)
        output_dir: Directory where the file will be saved
        logger: Logger instance for logging
        
    Returns:
        Path to the saved file or None if there was an error
    """
    if not data:
        if logger:
            logger.warning(f"No data to save to {filename}.json")
        else:
            print(f"No data to save to {filename}.json")
        return
    
    filepath = os.path.join(output_dir, f"{filename}.json")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        if logger:
            logger.info(f"Data saved to {filepath}")
        else:
            print(f"Data saved to {filepath}")
        return filepath
    except Exception as e:
        if logger:
            logger.error(f"Error saving {filename}.json: {e}")
        else:
            print(f"Error saving {filename}.json: {e}")
        return None