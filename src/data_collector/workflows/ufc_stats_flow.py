from prefect import flow
from prefect.logging import get_run_logger

from database.connection.postgres_conn import get_async_db
from core.crawler import crawl_with_httpx, crawl_with_crawl4ai
from workflows.tasks import scrap_all_fighter_task, scrap_all_events_task, scrap_event_detail_task, scrap_match_detail_task

logger = get_run_logger()

@flow(log_prints=True)
async def run_ufc_stats_flow():
    # TODO : session 분리해서 하위 프로세스에서 별도의 session을 사용하도록 수정
    logger.info("======================")
    logger.info("Start UFC stats scraping")
    logger.info("======================")
    async with get_async_db() as session:
        await scrap_all_events_task(session, crawl_with_httpx)

    # scrape fighters
    async with get_async_db() as session:
        await scrap_all_fighter_task(session, crawl_with_httpx)

    # scrape event details
    async with get_async_db() as session:
        await scrap_event_detail_task(session, crawl_with_httpx)

    # scrape match details
    async with get_async_db() as session:
        await scrap_match_detail_task(session, crawl_with_httpx)

    async with get_async_db() as session:
        await scrap_rankings_task(session, crawl_with_crawl4ai)
    logger.info("======================")
    logger.info("UFC stats scraping completed")
    logger.info("======================")


