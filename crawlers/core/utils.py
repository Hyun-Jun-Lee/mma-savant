import re
import logging
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path
from urllib.parse import urlparse
from functools import wraps

from playwright.sync_api import Page

from core.driver import PlaywrightDriver

def with_retry(max_attempts: int = 3):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logging.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    logging.warning(f"Attempt {attempts} failed: {str(e)}. Retrying...")
            return None
        return wrapper
    return decorator

def download_html(url: str, output_dir: str = "downloaded_pages", wait_for_load: bool = True) -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    
    if not path:
        path = parsed_url.netloc.replace('www.', '')
    
    clean_path = re.sub(r'[^\w\-_\.]', '_', path)
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{clean_path}_{timestamp}.html"
    file_path = output_path / filename
    
    with PlaywrightDriver() as driver:
        page = driver.new_page()
        try:
            page.goto(url)
            
            if wait_for_load:
                page.wait_for_load_state('networkidle')
            
            html_content = page.content()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logging.info(f"Successfully downloaded HTML from {url} to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logging.error(f"Failed to download HTML from {url}: {str(e)}")
            raise

def convert_height(height_str: str) -> tuple[float, float]:
    """Convert height from '5' 11"' format to 5.11 and calculate cm"""
    if not height_str or height_str == '--':
        return 0.0, 0.0
    
    try:
        # Extract feet and inches using regex
        match = re.match(r"(\d+)'\s*(\d+)", height_str)
        if match:
            feet, inches = map(int, match.groups())
            # Convert to cm: 1 foot = 30.48 cm, 1 inch = 2.54 cm
            cm = round((feet * 30.48) + (inches * 2.54), 1)
            # Convert to decimal format (e.g., 5'11" -> 5.11)
            decimal_height = float(f"{feet}.{inches:02d}")
            return decimal_height, cm
    except (ValueError, AttributeError):
        pass
    return 0.0, 0.0

def convert_weight(weight_str: str) -> tuple[float, float]:
    """Convert weight from 'X lbs.' format to numeric values"""
    if not weight_str or weight_str == '--':
        return 0.0, 0.0
    
    try:
        # Extract numeric value
        lbs = float(weight_str.replace('lbs.', '').strip())
        # Convert to kg
        kg = round(lbs * 0.453592, 1)
        return lbs, kg
    except ValueError:
        return 0.0, 0.0

def convert_reach(reach_str: str) -> tuple[float, float]:
    """Convert reach from 'XX"' format to numeric values and calculate cm"""
    if not reach_str or reach_str == '--':
        return 0.0, 0.0
    
    try:
        # Extract numeric value (e.g., '72.0"' -> 72.0)
        inches = float(reach_str.replace('"', '').strip())
        # Convert to cm
        cm = round(inches * 2.54, 1)
        return inches, cm
    except ValueError:
        return 0.0, 0.0