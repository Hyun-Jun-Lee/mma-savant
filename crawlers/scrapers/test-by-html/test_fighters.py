from bs4 import BeautifulSoup
from typing import List, Dict
from pathlib import Path
import json
import logging
from datetime import datetime

from domain.fighter import Fighter, FighterRecord
from core.utils import convert_height, convert_weight, convert_reach


def scrap_fighters(html_path: str) -> List[Dict[str, str]]:
        """
        Extract fighters information from HTML file
        """
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Find the table
        table = soup.find('table', class_='b-statistics__table')
        if not table:
            return []
        
        # Get column names from thead
        thead = table.find('thead', class_='b-statistics__table-caption')
        columns = []
        if thead:
            for th in thead.find_all('th', class_='b-statistics__table-col'):
                columns.append(th.get_text(strip=True))
        
        # Create a mapping for column name changes
        column_mapping = {
            'Ht.': 'height',
            'Wt.': 'weight',
            'W': 'wins',
            'L': 'losses',
            'D': 'draws',
            'Reach': 'reach'
        }
        
        # Get fighters data from tbody
        fighters = []
        tbody = table.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr', class_='b-statistics__table-row'):
                # Skip empty rows
                if tr.find('td', class_='b-statistics__table-col_type_clear'):
                    continue
                    
                # Extract data from each column
                cols = tr.find_all('td', class_='b-statistics__table-col')
                if len(cols) != len(columns):
                    continue
                    
                fighter_data = {}
                first_name = ''
                last_name = ''
                
                for i, col in enumerate(cols):
                    column_name = columns[i]
                    # Map column name if it exists in mapping
                    key = column_mapping.get(column_name, column_name.lower())
                    
                    # For name columns, get the text from the link
                    if i < 3:  # First, Last, Nickname columns
                        link = col.find('a', class_='b-link b-link_style_black')
                        value = link.get_text(strip=True) if link else None
                        
                        if key == 'first':
                            first_name = value
                            continue
                        elif key == 'last':
                            last_name = value
                            # Combine first and last name
                            fighter_data['name'] = f"{first_name} {last_name}".strip()
                            continue
                        else:
                            fighter_data[key] = value
                    else:
                        # For other columns, just get the text
                        value = col.get_text(strip=True)
                        
                        # Convert height and add cm
                        if key == 'height':
                            height, cm = convert_height(value)
                            fighter_data[key] = height
                            fighter_data['height_cm'] = cm
                        # Convert weight and add kg
                        elif key == 'weight':
                            lbs, kg = convert_weight(value)
                            fighter_data[key] = lbs
                            fighter_data['weight_kg'] = kg
                        # Convert reach and add cm
                        elif key == 'reach':
                            inches, cm = convert_reach(value)
                            fighter_data[key] = inches
                            fighter_data['reach_cm'] = cm
                        # Convert wins, losses, draws to int
                        elif key in ['wins', 'losses', 'draws']:
                            try:
                                fighter_data[key] = int(value)
                            except ValueError:
                                fighter_data[key] = 0
                        else:
                            fighter_data[key] = value
                
                fighters.append(fighter_data)
        
        return fighters


if __name__ == "__main__":
    html_path = "./downloaded_pages/statistics_fighters_20250125.html"
    fighters = scrap_fighters(html_path)
    
    # Create sample_data directory if it doesn't exist
    Path("sample_data").mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"sample_data/fighters_{timestamp}.json"
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fighters, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved fighters data to {output_path}")