import logging
import asyncio
from typing import List, Dict
from database.session import db_session
from workflows.tasks import (
    scrap_all_events_task,
    scrap_all_fighter_task,
    scrap_event_detail_task,
    scrap_match_detail_task,
)

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

async def run_ufc_stats_flow():
    logger.info("UFC 통계 크롤링 시작")
    
    # 이벤트 크롤링
    with db_session() as session:
        logger.info("Events scraping started")
        events_list = await scrap_all_events_task(session)
        logger.info(f"Events scraping completed : {len(events_list)} events saved")

    # # 파이터 크롤링
    # with db_session() as session:
    #     logger.info("Fighters scraping started")
    #     fighter_list = await scrap_all_fighter_task(session)
    #     logger.info(f"Fighters scraping completed : {len(fighter_list)} fighters saved")

    # # 파이터 딕셔너리 생성
    # fighter_dict = {fighter.name: fighter.id for fighter in fighter_list}

    # # 이벤트 세부 정보 크롤링
    # with db_session() as session:
    #     logger.info("Event details scraping started")
    #     fighter_match_dict = await scrap_event_detail_task(session, events_list, fighter_dict)
    #     logger.info(f"Event details scraping completed : {len(fighter_match_dict)} event details saved")

    # # 매치 세부 정보 크롤링
    # with db_session() as session:
    #     logger.info("Match details scraping started")
    #     await scrap_match_detail_task(session, fighter_match_dict, fighter_dict)
    #     logger.info("Match details scraping completed")
    
    logger.info("UFC 통계 크롤링 완료")

if __name__ == "__main__":
    # 비동기 이벤트 루프에서 메인 함수 실행
    asyncio.run(run_ufc_stats_flow())