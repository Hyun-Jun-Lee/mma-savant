import logging

from prefect import flow
from prefect.schedules import Cron


from database.session import db_session
from workflows.tasks import scrap_all_fighter_task, scrap_all_events_task, scrap_event_detail_task, scrap_match_detail_task

logger = logging.getLogger(__name__)

@flow(log_prints=True)
async def run_ufc_stats_flow():
    logger.info("UFC 통계 크롤링 시작")
    with db_session() as session:
        logger.info("Events scraping started")
        events_list = await scrap_all_events_task(session)
        logger.info(f"Events scraping completed : {len(events_list)} events saved")

    # scrape fighters
    with db_session() as session:
        logger.info("Fighters scraping started")
        fighter_list = await scrap_all_fighter_task(session)
        logger.info(f"Fighters scraping completed : {len(fighter_list)} fighters saved")

    # scrape event details
    with db_session() as session:
        logger.info("Event details scraping started")
        fighter_match_dict = await scrap_event_detail_task(session)
        logger.info(f"Event details scraping completed : {len(fighter_match_dict)} event details saved")

    # scrape match details
    with db_session() as session:
        logger.info("Match details scraping started")
        await scrap_match_detail_task(session)
        logger.info("Match details scraping completed")
    logger.info("UFC 통계 크롤링 완료")


