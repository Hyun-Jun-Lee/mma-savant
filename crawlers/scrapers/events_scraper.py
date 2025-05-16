import logging
import json
from datetime import datetime
from typing import List
from pathlib import Path
import asyncio
import traceback

from bs4 import BeautifulSoup

from core.driver import PlaywrightDriver
from schemas import Event

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%B %d, %Y").date()
    except ValueError:
        return None

async def scrap_all_events(all_events_url: str) -> List[Event]:
    try:
        async with PlaywrightDriver() as driver:
            page = await driver.new_page()
            await page.goto(all_events_url)
            html_content = await page.content()
        
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        logging.error(f"크롤링 중 오류 발생: {traceback.format_exc()}")
        return []
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
            
        # Find event link
        event_link = row.find('a', class_='b-link')
        if not event_link:
            continue
            
        event_url = event_link.get('href', '')
        event_name = event_link.get_text(strip=True)
        
        # Find date
        event_date_span = row.find('span', class_='b-statistics__date')
        event_date = event_date_span.get_text(strip=True) if event_date_span else ''
        if not event_date:
            print(event_name, event_date)
        parsed_event_date = parse_date(event_date)
        # Find location
        location_col = row.find('td', class_='b-statistics__table-col_style_big-top-padding')
        event_location = location_col.get_text(strip=True) if location_col else ''
        
        events.append(Event(
            name=event_name,
            date=parsed_event_date,
            location=event_location,
            url=event_url
        ))
    
    return events

async def main():
    try:
        events = await scrap_all_events("http://ufcstats.com/statistics/events/completed?page=all")
        
        # Create data directory if it doesn't exist
        Path("sample_data").mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"sample_data/events_{timestamp}.json"
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([event.dict() for event in events], f, indent=2, ensure_ascii=False)
        
        logging.info(f"저장 완료: {len(events)}개 이벤트를 {output_path}에 저장")
    except Exception as e:
        logging.error(f"데이터 저장 중 오류 발생: {traceback.format_exc()}")

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 비동기 실행
    asyncio.run(main())