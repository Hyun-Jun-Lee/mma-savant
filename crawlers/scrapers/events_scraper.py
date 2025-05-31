import logging
import json
from datetime import datetime
from typing import List, Callable
from pathlib import Path
import asyncio
import traceback
import re
from bs4 import BeautifulSoup

from core.driver import PlaywrightDriver
from schemas import Event

def parse_date(date_str):
    if not date_str:
        return None
        
    cleaned_str = re.sub(r'\s+', ' ', date_str.strip())  # 다중 공백을 단일 공백으로
    cleaned_str = re.sub(r'\s*,\s*', ', ', cleaned_str)  # 쉼표 주변 공백 정규화

    try:
        parsed_date = datetime.strptime(cleaned_str, "%B %d, %Y").date()
        return parsed_date
    except ValueError as e:
        print(e)
        # 추가 형식 시도 (예: 'May 17 1996')
        try:
            cleaned_str = re.sub(r',\s*', ' ', cleaned_str)  # 쉼표 제거
            parsed_date = datetime.strptime(cleaned_str, "%B %d %Y").date()
            return parsed_date
        except ValueError as e:
            print(e)
            return None

async def scrap_all_events(crawler_fn: Callable, all_events_url: str) -> List[Event]:
    try:
        html_content = await crawler_fn(all_events_url) 
        if not html_content:
            return []
        
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
        parsed_event_date = parse_date(event_date)
            
        # Find location
        location_col = row.find('td', class_='b-statistics__table-col_style_big-top-padding')
        event_location = location_col.get_text(strip=True) if location_col else ''
        event_schema = Event(
            name=event_name,
            event_date=parsed_event_date,
            location=event_location,
            url=event_url
        )
        
        events.append(event_schema)
    
    return events

async def main():
    from core.crawler import crawl_with_httpx
    
    try:
        events = await scrap_all_events(crawl_with_httpx, "http://ufcstats.com/statistics/events/completed?page=all")
        
        for event in events[:5]:
            print(event)
    except Exception as e:
        logging.error(f"데이터 저장 중 오류 발생: {traceback.format_exc()}")

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 비동기 실행
    asyncio.run(main())