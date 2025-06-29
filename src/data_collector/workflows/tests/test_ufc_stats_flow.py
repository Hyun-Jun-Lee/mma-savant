import asyncio
import time
from typing import Callable
import logging

from database.session import db_session
from workflows.tasks import (
    scrap_all_events_task,
    scrap_all_fighter_task,
    scrap_event_detail_task,
    scrap_match_detail_task,
)

LOGGER = logging.getLogger(__name__)


async def run_ufc_stats_flow(crawler_fn : Callable):
    LOGGER.info("UFC 통계 크롤링 시작")
    start_time = time.time()
    
    # # # 파이터 크롤링
    # with db_session() as session:
    #     LOGGER.info("Fighters scraping started")
    #     await scrap_all_fighter_task(session, crawler_fn)
    #     LOGGER.info("Fighters scraping completed")

    # # 이벤트 크롤링
    # with db_session() as session:
    #     LOGGER.info("Events scraping started")
    #     await scrap_all_events_task(session, crawler_fn)
    #     LOGGER.info("Events scraping completed")


    # # 이벤트 세부 정보 크롤링
    # with db_session() as session:
    #     LOGGER.info("Event details scraping started")
    #     await scrap_event_detail_task(session, crawler_fn)
    #     LOGGER.info("Event details scraping completed")

    # 매치 세부 정보 크롤링
    with db_session() as session:
        LOGGER.info("Match details scraping started")
        await scrap_match_detail_task(session, crawler_fn)
        LOGGER.info("Match details scraping completed")
    
    LOGGER.info("UFC 통계 크롤링 완료")
    end_time = time.time()
    LOGGER.info(f"Total time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    from core.crawler import crawl_with_httpx
    # 비동기 이벤트 루프에서 메인 함수 실행
    asyncio.run(run_ufc_stats_flow(crawl_with_httpx))