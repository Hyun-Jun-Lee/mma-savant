import asyncio

from prefect import flow
from prefect.logging import get_run_logger

from data_collector.crawler import (
    close_playwright_crawler,
    close_tapology_scrapling_worker,
    crawl_tapology_with_scrapling_worker as crawl_tapology_with_scrapling,
    crawl_with_playwright,
)
from dashboard.services import invalidate_all_cache
from data_collector.workflows.tasks import (
    scrap_all_fighter_task,
    scrap_all_events_task,
    scrap_upcoming_events_task,
    scrap_event_detail_task,
    scrap_match_detail_task,
    scrap_rankings_task,
    enrich_event_geocoding_task,
    enrich_fighter_tapology_profile_task,
)


@flow(name="UFC Stats Scraping", log_prints=True)
async def run_ufc_stats_flow():
    logger = get_run_logger()

    logger.info("======================")
    logger.info("Start UFC stats scraping")
    logger.info("======================")

    try:
        # scrape fighters
        logger.info("Fighters scraping started")
        await scrap_all_fighter_task(crawl_with_playwright)
        logger.info("Fighters scraping completed")

        # enrich Tapology fighter profiles
        logger.info("Tapology fighter profile enrichment started")
        await enrich_fighter_tapology_profile_task(crawl_tapology_with_scrapling)
        logger.info("Tapology fighter profile enrichment completed")

        # scrape events
        logger.info("Events scraping started")
        await scrap_all_events_task(crawl_with_playwright)
        logger.info("Events scraping completed")

        # scrape upcoming events
        logger.info("Upcoming events scraping started")
        await scrap_upcoming_events_task(crawl_with_playwright)
        logger.info("Upcoming events scraping completed")

        # enrich event geocoding
        logger.info("Event geocoding enrichment started")
        await enrich_event_geocoding_task()
        logger.info("Event geocoding enrichment completed")

        # scrape event details
        logger.info("Event details scraping started")
        await scrap_event_detail_task(crawl_with_playwright)
        logger.info("Event details scraping completed")

        # scrape match details
        logger.info("Match details scraping started")
        await scrap_match_detail_task(crawl_with_playwright)
        logger.info("Match details scraping completed")

        # scrape rankings
        logger.info("Rankings scraping started")
        await scrap_rankings_task(crawl_with_playwright)
        logger.info("Rankings scraping completed")

        # invalidate dashboard cache so stale data is not served
        deleted = invalidate_all_cache()
        logger.info(f"Dashboard cache invalidated ({deleted} keys deleted)")
    finally:
        await close_playwright_crawler()
        await close_tapology_scrapling_worker()

    logger.info("======================")
    logger.info("UFC stats scraping completed")
    logger.info("======================")


if __name__ == "__main__":
    asyncio.run(run_ufc_stats_flow())
