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
