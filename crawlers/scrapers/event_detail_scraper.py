from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
import traceback
import logging

from bs4 import BeautifulSoup

from core.driver import PlaywrightDriver
from schemas import Match, FighterMatch, WeightClass

async def scrap_event_detail(event_url: str, event_id: int, fighter_dict: Dict[str, int]) -> List[Dict]:
    """
    Extract event details from a UFC event detail page HTML file
    """
    try:
        # Check if event is future event
        is_future_event = False
        event_details = {}
        match_data_list = []

        async with PlaywrightDriver() as driver:
            page = await driver.new_page()
            await page.goto(event_url)
            html_content = await page.content()
        
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logging.error(f"이벤트 상세정보 크롤링 중 오류 발생: {traceback.format_exc()}")
        return []

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
        detail_url = None
        # fight-details 링크 추출
        if 'js-fight-details-click' in row.get('class', []):
            detail_url = row.get('data-link')
        cols = row.find_all('td', class_='b-fight-details__table-col')
        if not cols:
            continue
            
        # Extract fighter information
        fighter_text = cols[1].get_text(strip=False).lstrip().replace('\n', '')
        fighters = [f.strip() for f in fighter_text.split('  ') if f.strip()]
        fighter_1, fighter_2 = fighters
        fighter_1_id = fighter_dict.get(fighter_1)
        fighter_2_id = fighter_dict.get(fighter_2)
        
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

            weight_class_id = WeightClass.get_id_by_name(weight_class)
            
            # Create new fight entry
            match_data ={ 
                "match" : Match(
                event_id=event_id,
                order=current_order,
                weight_class_id=weight_class_id,
                detail_url=detail_url if detail_url else None,
                method=method,
                round=round_num,
                time=time),
                "fighters" : [
                    {"fighter_id": fighter_1_id, "result": fighter_1_result},
                    {"fighter_id": fighter_2_id, "result": fighter_2_result}
                ]
            }
            current_order -= 1
            match_data_list.append(match_data)
    
    return match_data_list

async def main():
    try:
        match_data_list = await scrap_event_detail("http://ufcstats.com/event-details/ca936c67687789e9", 1, {})
        print(f"이벤트 상세정보: {len(match_data_list)}개의 매치 데이터 추출됨")
        for match in match_data_list:
            print(match)
    except Exception as e:
        logging.error(f"메인 함수 오류 발생: {traceback.format_exc()}")

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 비동기 실행
    asyncio.run(main())