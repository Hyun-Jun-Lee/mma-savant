from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from pathlib import Path
import logging

def scrap_all_events(html_path: str) -> List[Dict[str, str]]:
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    events_table = soup.find('table', class_='b-statistics__table-events')
    
    if not events_table:
        logging.error("Could not find events table in HTML")
        return []
    
    events = []
    rows = events_table.find('tbody').find_all('tr')
    
    for row in rows:
        # Skip empty rows
        if not row.find_all('td'):
            continue
            
        # Find event link and name
        event_link = row.find('a', class_='b-link')
        if not event_link:
            continue
            
        event_url = event_link.get('href', '')
        event_name = event_link.get_text(strip=True)
        
        # Find date
        event_date_span = row.find('span', class_='b-statistics__date')
        event_date = event_date_span.get_text(strip=True) if event_date_span else ''
        
        # Find location
        location_col = row.find('td', class_='b-statistics__table-col_style_big-top-padding')
        event_location = location_col.get_text(strip=True) if location_col else ''
        
        events.append({
            'name': event_name,
            'date': event_date,
            'location': event_location,
            'url': event_url
        })
    
    return events

if __name__ == "__main__":
    import json
    from datetime import datetime
    
    html_path = "./downloaded_pages/statistics_events_completed_20250118_225554.html"
    events = scrap_all_events(html_path)
    
    # Create data directory if it doesn't exist
    Path("data").mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"sample_data/events_{timestamp}.json"
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved {len(events)} events to {output_path}")