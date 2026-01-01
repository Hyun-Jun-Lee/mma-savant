import asyncio

from prefect import flow
from prefect.logging import get_run_logger

from data_collector.crawler import crawl_with_httpx
from data_collector.workflows.tasks import (
    scrap_all_fighter_task,
    scrap_all_events_task,
    scrap_event_detail_task,
    scrap_match_detail_task,
    scrap_rankings_task
)


@flow(name="UFC Stats Scraping", log_prints=True)
async def run_ufc_stats_flow():
    logger = get_run_logger()

    logger.info("======================")
    logger.info("Start UFC stats scraping")
    logger.info("======================")

    # scrape fighters
    logger.info("Fighters scraping started")
    await scrap_all_fighter_task(crawl_with_httpx)
    logger.info("Fighters scraping completed")

    # scrape events
    logger.info("Events scraping started")
    await scrap_all_events_task(crawl_with_httpx)
    logger.info("Events scraping completed")

    # scrape event details
    logger.info("Event details scraping started")
    await scrap_event_detail_task(crawl_with_httpx)
    logger.info("Event details scraping completed")

    # scrape match details
    logger.info("Match details scraping started")
    await scrap_match_detail_task(crawl_with_httpx)
    logger.info("Match details scraping completed")

    # scrape rankings
    logger.info("Rankings scraping started")
    await scrap_rankings_task(crawl_with_httpx)
    logger.info("Rankings scraping completed")

    logger.info("======================")
    logger.info("UFC stats scraping completed")
    logger.info("======================")


if __name__ == "__main__":
    asyncio.run(run_ufc_stats_flow())


