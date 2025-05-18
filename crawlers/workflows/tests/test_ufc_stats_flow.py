import asyncio
import time
from typing import List, Dict

from database.session import db_session
from workflows.tasks import (
    scrap_all_events_task,
    scrap_all_fighter_task,
    scrap_event_detail_task,
    scrap_match_detail_task,
)


async def run_ufc_stats_flow():
    print("UFC 통계 크롤링 시작")
    start_time = time.time()
    
    # 파이터 크롤링
    with db_session() as session:
        print("Fighters scraping started")
        fighter_list = await scrap_all_fighter_task(session)
        print(f"Fighters scraping completed : {len(fighter_list)} fighters saved")

    # # 이벤트 크롤링
    # with db_session() as session:
    #     print("Events scraping started")
    #     events_list = await scrap_all_events_task(session)
    #     print(f"Events scraping completed : {len(events_list)} events saved")


    # # 이벤트 세부 정보 크롤링
    # with db_session() as session:
    #     print("Event details scraping started")
    #     fighter_match_dict = await scrap_event_detail_task(session)
    #     print(f"Event details scraping completed ")

    # # 매치 세부 정보 크롤링
    # with db_session() as session:
    #     print("Match details scraping started")
    #     await scrap_match_detail_task(session)
    #     print("Match details scraping completed")
    
    # print("UFC 통계 크롤링 완료")
    # end_time = time.time()
    # print(f"Total time taken: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    # 비동기 이벤트 루프에서 메인 함수 실행
    asyncio.run(run_ufc_stats_flow())