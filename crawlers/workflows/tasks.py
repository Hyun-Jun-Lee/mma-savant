from typing import List, Dict

from prefect import task

from repository import BaseRepository, FighterRepository, EventRepository, MatchRepository, FighterMatchRepository, BasicMatchStatRepository, SigStrMatchStatRepository
from schemas import BaseSchema, Event, Fighter, Match, FighterMatch
from scrapers import scrap_fighters, scrap_all_events, scrap_event_detail, scrape_match_basic_statistics, scrape_match_significant_strikes

def save_data(data : List[BaseSchema], repository: BaseRepository) -> List[BaseSchema]:
    return repository.bulk_upsert(data)

@task(retries=3)
def scrap_all_fighter_task(session)-> List[Fighter]:
    fighter_data = []
    for char in 'abcdefghijklmnopqrstuvwxyz':
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        fighter_schema_list = scrap_fighters(fighters_url)
        saved_fighter_list = save_data(fighter_schema_list, FighterRepository(session))
        fighter_data.extend(saved_fighter_list)
    return fighter_data


@task(retries=3)
def scrap_all_events_task(session) -> List[Event]:
    all_events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    event_schema_list = scrap_all_events(all_events_url)
    saved_event_list = save_data(event_schema_list, EventRepository(session))
    return saved_event_list

@task(retries=3)
def scrap_event_detail_task(session, events_list: List[Event], fighter_dict: Dict[str, int]) -> Dict[str, Dict[int, FighterMatch]]:
    result_dict = {}
    for event in events_list:
        event_url = event.url
        event_id = event.id
        matches_data = scrap_event_detail(event_url, event_id, fighter_dict)

        for match_data in matches_data:
            match = match_data["match"]
            saved_match = save_data([match], MatchRepository(session))
            match_id = saved_match[0].id
            detail_url = saved_match[0].detail_url if saved_match[0].detail_url else None
            if not detail_url:
                continue

            if detail_url not in result_dict:
                result_dict[detail_url] = {}

            for fighter_info in match_data["fighters"]:
                fighter_id = fighter_info["fighter_id"]
                result = fighter_info["result"]
                fighter_match = FighterMatch(fighter_id=fighter_id, match_id=match_id, result=result)
                saved_fighter_match = save_data([fighter_match], FighterMatchRepository(session))
                result_dict[detail_url][fighter_id] = saved_fighter_match
    return result_dict

@task(retries=3)
def scrap_match_detail_task(session, fighter_match_dict: Dict[str, Dict[int, FighterMatch]], fighter_dict: Dict[str, int])-> None:
    """
    매치 상세 정보를 스크랩하는 태스크
    
    Args:
        session: 데이터베이스 세션
        fighter_match_dict: {detail_url: {fighter_id: fighter_match}} 형태의 딕셔너리
        fighter_dict: {fighter_name: fighter_id} 형태의 딕셔너리
    """
    for detail_url, fighter_matches in fighter_match_dict.items():
        if not detail_url:
            continue
            
        # 매치 기본 통계 정보 스크랩 및 저장
        match_statistics_list = scrape_match_basic_statistics(detail_url, fighter_dict, fighter_matches)
        save_data(match_statistics_list, BasicMatchStatRepository(session))
        
        # 매치 스트라이크 상세 정보 스크랩 및 저장
        strike_details_list = scrape_match_significant_strikes(detail_url, fighter_dict, fighter_matches)
        save_data(strike_details_list, SigStrMatchStatRepository(session))
