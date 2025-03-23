from typing import List, Dict

from prefect import task

from crawlers.schemas.fighter import FighterMatch
from repository import BaseRepository, FighterRepository, EventRepository, MatchRepository, FighterMatchRepository
from schemas import BaseSchema, Event, Fighter, Match
from scrapers import scrap_fighters, scrap_all_events, scrap_event_detail, scrap_match_detail_total, scrap_match_detail_sig

def save_data(data : List[BaseSchema], repository: BaseRepository) -> List[BaseSchema]:
    return repository.bulk_upsert(data)

@task(max_retries=3, retry_delay=30)
def scrap_all_fighter_task(session)-> List[Fighter]:
    fighter_data = []
    for char in 'abcdefghijklmnopqrstuvwxyz':
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        fighter_schema_list = scrap_fighters(fighters_url)
        saved_fighter_list = save_data(fighter_schema_list, FighterRepository(session))
        fighter_data.extend(saved_fighter_list)
    return fighter_data


@task(max_retries=3, retry_delay=30)
def scrap_all_events_task(session) -> List[Event]:
    all_events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    event_schema_list = scrap_all_events(all_events_url)
    saved_event_list = save_data(event_schema_list, EventRepository(session))
    return saved_event_list

@task(max_retries=3, retry_delay=30)
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

@task(max_retries=3, retry_delay=30)
def scrap_match_detail_task(session, fighter_match_dict: Dict[str, Dict[int, FighterMatch]], fighter_dict: Dict[str, int])-> None:
    for detail_url, fighter_match_dict in fighter_match_dict.items():
        match_detail_total = scrap_match_detail_total(detail_url, fighter_dict, fighter_match_dict)
        save_data(match_detail_total, EventRepository(session))

        match_detail_sig = scrap_match_detail_sig(detail_url, fighter_dict, fighter_match_dict)
        save_data(match_detail_sig, EventRepository(session))
