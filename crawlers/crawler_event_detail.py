import logging
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import json

def scrap_event_detail(html_path):
    """
    Extract event details from a UFC event detail page HTML file
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    event_details = {}
    
    # Find event title
    title_element = soup.find('span', class_='b-content__title-highlight')
    event_details['title'] = title_element.get_text(strip=True) if title_element else ''
    
    # Find event info
    info_box = soup.find('div', class_='b-list__info-box')
    if info_box:
        info_items = info_box.find_all('li', class_='b-list__box-list-item')
        for item in info_items:
            title = item.find('i', class_='b-list__box-item-title')
            if title:
                key = title.get_text(strip=True).lower().replace(':', '')
                value = item.get_text(strip=True).replace(title.get_text(strip=True), '').strip()
                event_details[key] = value
    
    # Find fights
    fights = []
    fight_rows = soup.find_all('tr', class_='b-fight-details__table-row')
    
    for row in fight_rows[1:]:  # Skip header row
        cols = row.find_all('td', class_='b-fight-details__table-col')
        if not cols:
            continue
            
        # Extract fighter information
        fighter_text = cols[1].get_text(strip=False).lstrip().replace('\n', '')
        fighters = [f.strip() for f in fighter_text.split('  ') if f.strip()]
        fighter_1, fighter_2 = fighters
        
        # Check fight result
        win_element = cols[0].find('a', class_='b-flag b-flag_style_green')
        draw_nc_element = cols[0].find('a', class_='b-flag b-flag_style_bordered')
        
        if win_element:
            fighter_1_result = "win"
            fighter_2_result = "loss"
        elif draw_nc_element:
            result = draw_nc_element.get_text(strip=True).lower()
            if result == "draw":
                fighter_1_result = fighter_2_result = "draw"
            elif result == "nc":
                fighter_1_result = fighter_2_result = "nc"
        else:
            fighter_1_result = "loss"
            fighter_2_result = "win"
        
        # Extract other stats
        kd_text = cols[2].get_text().lstrip().replace('\n', '').split('  ')
        kd_list = [k.strip() for k in kd_text if k.strip()]
        kd_fighter_1, kd_fighter_2 = kd_list
        
        # Extract striking stats
        str_text = cols[3].get_text().lstrip().replace('\n', '').split('  ')
        str_list = [s.strip() for s in str_text if s.strip()]
        str_fighter_1, str_fighter_2 = str_list
        
        # Extract takedown stats
        td_text = cols[4].get_text().lstrip().replace('\n', '').split('  ')
        td_list = [t.strip() for t in td_text if t.strip()]
        td_fighter_1, td_fighter_2 = td_list
        
        # Extract submission attempts
        sub_text = cols[5].get_text().lstrip().replace('\n', '').split('  ')
        sub_list = [s.strip() for s in sub_text if s.strip()]
        sub_fighter_1, sub_fighter_2 = sub_list
        
        # Get fight details (only for first row of each fight)
        if len(fights) == 0 or fights[-1]['fighters']:  # If no fights or last fight is complete
            weight_class = cols[6].get_text(strip=True)
            method_text = cols[7].get_text().lstrip().replace('\n', '').split('  ')
            method_list = [m.strip() for m in method_text if m.strip()]
            if len(method_list)>1:
                method = '-'.join(method_list)
            else:
                method = method_list[0]

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
        fights[-1]['fighters'].extend([
            {
                'name': fighter_1,
                'result': fighter_1_result,
                'kd': kd_fighter_1,
                'str': str_fighter_1,
                'td': td_fighter_1,
                'sub': sub_fighter_1
            },
            {
                'name': fighter_2,
                'result': fighter_2_result,
                'kd': kd_fighter_2,
                'str': str_fighter_2,
                'td': td_fighter_2,
                'sub': sub_fighter_2
            }
        ])
    
    event_details['fights'] = fights
    
    return event_details

if __name__ == "__main__":
    html_path = "./downloaded_pages/event-details_39f68882def7a507_20250119.html"
    # html_path = "./downloaded_pages/event-details_13a0fb8fbdafb54f_20250125.html"
    event_details = scrap_event_detail(html_path)
    
    # Create sample_data directory if it doesn't exist
    Path("sample_data").mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"sample_data/event_details_{timestamp}.json"
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(event_details, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved event details to {output_path}")