import asyncio
import time
from typing import Callable
import logging

from data_collector.crawler import crawl_with_crawl4ai, crawl_with_httpx
from database.connection.postgres_conn import async_db_session
from data_collector.workflows.tasks import (
    scrap_all_events_task,
    scrap_all_fighter_task,
    scrap_event_detail_task,
    scrap_match_detail_task,
    scrap_rankings_task
)

LOGGER = logging.getLogger(__name__)

# TODO : session 분리해서 하위 프로세스에서 별도의 session을 사용하도록 수정
async def run_ufc_stats_flow():
    LOGGER.info("UFC 통계 크롤링 시작")
    start_time = time.time()
    
    # # 파이터 크롤링
    # async with async_db_session() as session:
    #     LOGGER.info("Fighters scraping started")
    #     await scrap_all_fighter_task(session, crawl_with_httpx)
    #     LOGGER.info("Fighters scraping completed")

    # # 이벤트 크롤링
    # async with async_db_session() as session:
    #     LOGGER.info("Events scraping started")
    #     await scrap_all_events_task(session, crawl_with_httpx)
    #     LOGGER.info("Events scraping completed")


    # # 이벤트 세부 정보 크롤링
    # async with async_db_session() as session:
    #     LOGGER.info("Event details scraping started")
    #     await scrap_event_detail_task(session, crawl_with_httpx)
    #     LOGGER.info("Event details scraping completed")

    # 매치 세부 정보 크롤링
    async with async_db_session() as session:
        LOGGER.info("Match details scraping started")
        await scrap_match_detail_task(session, crawl_with_httpx)
        LOGGER.info("Match details scraping completed")

    async with async_db_session() as session:
        LOGGER.info("Rankings scraping started")
        await scrap_rankings_task(session, crawl_with_httpx)
        LOGGER.info("Rankings scraping completed")
    
    LOGGER.info("UFC 통계 크롤링 완료")
    end_time = time.time()
    LOGGER.info(f"Total time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    # 비동기 이벤트 루프에서 메인 함수 실행
    asyncio.run(run_ufc_stats_flow())