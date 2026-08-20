from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Callable
import asyncio
import traceback
import logging
import posixpath
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from match.models import MatchSchema
from common.models import WeightClassSchema
from common.utils import utc_now
from data_collector.scrapers.fighter_lookup import resolve_fighter_id

import re

_PLURAL_SUFFIX = re.compile(r'(Punches|Elbows|Kicks|Knees|Headbutts|Slams)$')
_PLURAL_TO_SINGULAR = {
    'Punches': 'Punch',
    'Elbows': 'Elbow',
    'Kicks': 'Kick',
    'Knees': 'Knee',
    'Headbutts': 'Headbutt',
    'Slams': 'Slam',
}
_TITLE_BOUT_ICON_FILE = "belt.png"
_FIGHT_OF_THE_NIGHT_ICON_FILE = "fight.png"
_PERFORMANCE_OF_THE_NIGHT_ICON_FILE = "perf.png"
_KNOWN_EVENT_ROW_ICON_FILES = {
    _TITLE_BOUT_ICON_FILE,
    _FIGHT_OF_THE_NIGHT_ICON_FILE,
    _PERFORMANCE_OF_THE_NIGHT_ICON_FILE,
}


@dataclass(frozen=True)
class EventRowIconMetadata:
    is_title_bout: bool = False
    has_fight_of_the_night_bonus: bool = False
    has_performance_of_the_night_bonus: bool = False


def _normalize_method(method: str) -> str:
    """복수형 기술명을 단수형으로 통일 (KO/TKO-Punches → KO/TKO-Punch)"""
    return _PLURAL_SUFFIX.sub(lambda m: _PLURAL_TO_SINGULAR[m.group()], method)


def _extract_event_row_icon_metadata(weight_class_cell) -> EventRowIconMetadata:
    """UFCStats 이벤트 row의 weight-class cell 이미지 파일명에서 보너스 메타데이터 추출."""
    icon_files = set()
    for image in weight_class_cell.find_all("img"):
        src = image.get("src") or ""
        icon_file = posixpath.basename(urlparse(src).path).lower()
        if icon_file:
            icon_files.add(icon_file)

    unknown_icon_files = tuple(sorted(icon_files - _KNOWN_EVENT_ROW_ICON_FILES))
    if unknown_icon_files:
        logging.info("Unknown UFCStats event row icon files ignored: %s", unknown_icon_files)

    return EventRowIconMetadata(
        is_title_bout=_TITLE_BOUT_ICON_FILE in icon_files,
        has_fight_of_the_night_bonus=_FIGHT_OF_THE_NIGHT_ICON_FILE in icon_files,
        has_performance_of_the_night_bonus=_PERFORMANCE_OF_THE_NIGHT_ICON_FILE in icon_files,
    )


async def scrap_event_detail(crawler_fn: Callable, event_url: str, event_id: int, fighter_name_to_id_map: Dict[str, int]) -> List[Dict]:
    """
    Extract event details from a UFC event detail page HTML file
    """
    try:
        # Check if event is future event
        is_future_event = False
        event_details = {}
        match_data_list = []

        html_content = await crawler_fn(event_url)
        if not html_content:
            return []

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
        current_time = utc_now()
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
        fighter_links = cols[1].find_all('a')
        fighters = [link.get_text(strip=True) for link in fighter_links if link.get_text(strip=True)]
        if len(fighters) < 2:
            fighter_text = cols[1].get_text(strip=False).lstrip().replace('\n', '')
            fighters = [f.strip() for f in fighter_text.split('  ') if f.strip()]
        fighter_1, fighter_2 = fighters[:2]
        fighter_1_link = fighter_links[0].get("href") if len(fighter_links) > 0 else None
        fighter_2_link = fighter_links[1].get("href") if len(fighter_links) > 1 else None
        fighter_1_id = resolve_fighter_id(fighter_1, fighter_1_link, fighter_name_to_id_map)
        fighter_2_id = resolve_fighter_id(fighter_2, fighter_2_link, fighter_name_to_id_map)

        # fighter_id가 None이면 로그 남기고 해당 매치 건너뛰기
        if fighter_1_id is None or fighter_2_id is None:
            missing_fighters = []
            if fighter_1_id is None:
                missing_fighters.append(fighter_1)
            if fighter_2_id is None:
                missing_fighters.append(fighter_2)
            logging.warning(f"Fighter not found in DB, skipping match: {missing_fighters}")
            continue

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
            weight_class_cell = cols[6]
            weight_class = weight_class_cell.get_text(strip=True)
            icon_metadata = _extract_event_row_icon_metadata(weight_class_cell)
            method_text = cols[7].get_text().lstrip().replace('\n', '').split('  ')
            method_list = [m.strip() for m in method_text if m.strip()]
            if len(method_list)>1:
                method = '-'.join(method_list)
            else:
                method = method_list[0] if method_list else None

            # 복수형 → 단수형 정규화 (Punches→Punch, Elbows→Elbow 등)
            if method:
                method = _normalize_method(method)

            round_num_text = cols[8].get_text(strip=True)
            round_num = int(round_num_text) if round_num_text else None
            time = cols[9].get_text(strip=True) or None

            weight_class_id = WeightClassSchema.get_id_by_name(weight_class)
            if not weight_class_id:
                print("weight_class", weight_class)
                
            # Create new fight entry
            match_data ={
                "match" : MatchSchema(
                event_id=event_id,
                order=current_order,
                weight_class_id=weight_class_id,
                detail_url=detail_url if detail_url else None,
                method=method,
                result_round=round_num,
                time=time,
                is_main_event=(current_order == total_fights),
                is_title_bout=icon_metadata.is_title_bout,
                has_fight_of_the_night_bonus=icon_metadata.has_fight_of_the_night_bonus),
                "fighters" : [
                    {
                        "fighter_id": fighter_1_id,
                        "result": fighter_1_result,
                        "has_performance_of_the_night_bonus": (
                            icon_metadata.has_performance_of_the_night_bonus
                            and fighter_1_result == "win"
                        ),
                    },
                    {
                        "fighter_id": fighter_2_id,
                        "result": fighter_2_result,
                        "has_performance_of_the_night_bonus": (
                            icon_metadata.has_performance_of_the_night_bonus
                            and fighter_2_result == "win"
                        ),
                    }
                ]
            }
            current_order -= 1
            match_data_list.append(match_data)
    
    return match_data_list

async def main():
    from data_collector.crawler import crawl_with_httpx
    
    try:
        match_data_list = await scrap_event_detail(crawl_with_httpx, "http://ufcstats.com/event-details/ca936c67687789e9", 1, {})
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
