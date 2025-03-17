import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

from bs4 import BeautifulSoup

from core.driver import PlaywrightDriver

def scrap_event_detail(event_detail_url: str, event_id: int, fighter_data: Dict[str, int]) -> Dict[str, str]:
    """
    Extract event details from a UFC event detail page HTML file
    """
    # TODO : Need to scrap fight-detail url
    # Check if event is future event
    is_future_event = False

    with PlaywrightDriver() as driver:
        page = driver.new_page()
        page.goto(event_detail_url)
        html_content = page.content()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
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

    fight_date = event_details.get('date', '')
    if fight_date:
        date_obj = datetime.strptime(fight_date, '%B %d, %Y')
        kst_date_obj = date_obj + timedelta(days=1)
        
        # Compare with current time
        current_time = datetime.now()
        if kst_date_obj > current_time:
            is_future_event = True
        
    
    # Find fights
    fights = []
    fight_rows = soup.find_all('tr', class_='b-fight-details__table-row')
    
    # calculate total fights
    total_fights = len([row for row in fight_rows[1:] if row.find_all('td', class_='b-fight-details__table-col')])
    # order of fighter (main event is biggest number)
    current_order = total_fights
    
    for row in fight_rows[1:]:
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
        
        if is_future_event:
            fighter_1_result = fighter_2_result = None
        else:
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
        if not kd_list:
            kd_fighter_1, kd_fighter_2 = 0, 0
        else:
            kd_fighter_1, kd_fighter_2 = kd_list
        
        # Extract striking stats
        str_text = cols[3].get_text().lstrip().replace('\n', '').split('  ')
        str_list = [s.strip() for s in str_text if s.strip()]
        if not str_list:
            str_fighter_1, str_fighter_2 = 0, 0
        else:
            str_fighter_1, str_fighter_2 = str_list
        
        # Extract takedown stats
        td_text = cols[4].get_text().lstrip().replace('\n', '').split('  ')
        td_list = [t.strip() for t in td_text if t.strip()]
        if not td_list or td_list[0] == 'View Matchup':
            td_fighter_1, td_fighter_2 = 0, 0
        else:
            td_fighter_1, td_fighter_2 = td_list
        
        # Extract submission attempts
        sub_text = cols[5].get_text().lstrip().replace('\n', '').split('  ')
        sub_list = [s.strip() for s in sub_text if s.strip()]
        if not sub_list:
            sub_fighter_1, sub_fighter_2 = 0, 0
        else:
            sub_fighter_1, sub_fighter_2 = sub_list
        
        # Get fight details
        if len(fights) == 0 or fights[-1]['fighters']:
            weight_class = cols[6].get_text(strip=True)
            method_text = cols[7].get_text().lstrip().replace('\n', '').split('  ')
            method_list = [m.strip() for m in method_text if m.strip()]
            if len(method_list)>1:
                method = '-'.join(method_list)
            else:
                method = method_list[0] if method_list else None

            round_num = cols[8].get_text(strip=True)
            time = cols[9].get_text(strip=True)
            
            # Create new fight entry
            current_fight = {
                'order': current_order,
                'weight_class': weight_class,
                'method': method,
                'round': round_num,
                'time': time,
                'fighters': []
            }
            current_order -= 1
            
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
    event_details = scrap_event_detail("http://ufcstats.com/event-details/ca936c67687789e9")
    
    # Create sample_data directory if it doesn't exist
    Path("sample_data").mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"sample_data/event_details_{timestamp}.json"
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(event_details, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved event details to {output_path}")