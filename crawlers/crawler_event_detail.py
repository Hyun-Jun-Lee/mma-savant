import logging
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import json

def extract_event_details_from_html(html_path):
    """
    Extract event details from a UFC event detail page HTML file
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    event_details = {}
    
    # Find event title
    event_title = soup.find('h1', class_='c-EventHeader__title')
    event_details['title'] = event_title.get_text(strip=True)
    
    # Find event date and location
    event_info = soup.find('div', class_='c-EventHeader__info')
    event_date = event_info.find('span', class_='c-EventHeader__date')
    event_details['date'] = event_date.get_text(strip=True)
    event_location = event_info.find('span', class_='c-EventHeader__location')
    event_details['location'] = event_location.get_text(strip=True)
    
    # Find fights
    fights = []
    fight_rows = soup.find_all('tr', class_='b-fight-details__table-row')
    for row in fight_rows[1:]:  # Skip header row
        cols = row.find_all('td', class_='b-fight-details__table-col')
        if not cols:
            continue
            
        # Extract fighter information
        fighter = cols[1].get_text(strip=True)
        
        # Check if this fighter won
        win_element = cols[0].find('i', class_='b-fight-details__table-title')
        is_winner = bool(win_element and 'win' in win_element.get_text(strip=True).lower())
        
        # Extract other stats
        kd = cols[2].get_text(strip=True)
        str_stats = cols[3].get_text(strip=True)
        td = cols[4].get_text(strip=True)
        sub = cols[5].get_text(strip=True)
        
        # Get fight details (only for first fighter in the pair)
        if len(fights) % 2 == 0:
            weight_class = cols[6].get_text(strip=True)
            method = cols[7].get_text(strip=True)
            round_num = cols[8].get_text(strip=True)
            time = cols[9].get_text(strip=True)
            
            # Create new fight entry
            current_fight = {
                'weight_class': weight_class,
                'method': method,
                'round': round_num,
                'time': time,
                'fighters': []
            }
            fights.append(current_fight)
        
        # Add fighter details to current fight
        fights[-1]['fighters'].append({
            'name': fighter,
            'winner': is_winner,
            'kd': kd,
            'str': str_stats,
            'td': td,
            'sub': sub
        })
    
    event_details['fights'] = fights
    
    return event_details

if __name__ == "__main__":
    html_path = "./downloaded_pages/event-details_39f68882def7a507_20250119.html"
    event_details = extract_event_details_from_html(html_path)
    
    # Create sample_data directory if it doesn't exist
    Path("sample_data").mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"sample_data/event_details_{timestamp}.json"
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(event_details, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved event details to {output_path}")