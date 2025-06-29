from prefect import flow
from prefect.logging import get_run_logger

from database.session import db_session
from core.crawler import crawl_with_httpx
from workflows.tasks import scrap_all_fighter_task, scrap_all_events_task, scrap_event_detail_task, scrap_match_detail_task

logger = get_run_logger()

@flow(log_prints=True)
async def run_ufc_stats_flow():
    logger.info("======================")
    logger.info("Start UFC stats scraping")
    logger.info("======================")
    with db_session() as session:
        await scrap_all_events_task(session, crawl_with_httpx)

    # scrape fighters
    with db_session() as session:
        await scrap_all_fighter_task(session, crawl_with_httpx)

    # scrape event details
    with db_session() as session:
        await scrap_event_detail_task(session, crawl_with_httpx)

    # scrape match details
    with db_session() as session:
        await scrap_match_detail_task(session, crawl_with_httpx)
    logger.info("======================")
    logger.info("UFC stats scraping completed")
    logger.info("======================")


