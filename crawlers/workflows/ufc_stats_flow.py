from prefect import Flow

from database.session import db_session
from workflows.tasks import scrap_all_fighter_task, scrap_all_events_task, scrap_event_detail_task, scrap_match_detail_task


def create_flow():
    with Flow("ufc_stats_flow") as flow:
        # NOTE : repository에 데이터 전달할 떄 어떤 형태로 전달할건지 결정 (pydantic schmea or dict or model)
        # scrape events
        with db_session() as session:
            events_dict = scrap_all_events_task(session)

        # scrape fighters
        with db_session() as session:
            fighter_dict = scrap_all_fighter_task(session)

        # scrape event details
        with db_session() as session:
            fight_detail_urls = scrap_event_detail_task(session, events_dict, fighter_dict)
        
        # scrape match details
        with db_session() as session:
            scrap_match_detail_task(session, fight_detail_urls, fighter_dict)

if __name__ == "__main__":
    logger.info("UFC 통계 크롤링 시작")
    flow = create_flow()
    flow.run()
    logger.info("UFC 통계 크롤링 완료")