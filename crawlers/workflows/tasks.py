from typing import List, Dict

from prefect import task

from repository import BaseRepository, FighterRepository, EventRepository
from scrapers import scrap_fighters, scrap_all_events, scrap_event_detail, scrap_match_detail_total, scrap_match_detail_sig

def save_data(data : List[dict], repository: BaseRepository) -> Dict[str, int]:
    # NOTE : return dict[name, id]
    data_dict = repository.bulk_upsert(data)
    return data_dict

@task(max_retries=3, retry_delay=30)
def scrap_all_fighter_task(session)-> Dict[str, int]:
    fighter_data = {}
    for char in 'abcdefghijklmnopqrstuvwxyz':
        fighters_url = f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        fighters_data = scrap_fighters(fighters_url)
        fighter_dict = save_data(fighters_data, FighterRepository(session))
        fighter_data.update(fighter_dict)
    return fighter_data


@task(max_retries=3, retry_delay=30)
def scrap_all_events_task(session) -> Dict[str, int]:
    all_events_url = "http://ufcstats.com/statistics/events/completed?page=all"
    events_data = scrap_all_events(all_events_url)
    event_dict = save_data(events_data, EventRepository(session))
    return event_dict

@task(max_retries=3, retry_delay=30)
def scrap_event_detail_task(session, events_data, fighter_data) -> List[str]:
    fight_detail_urls = []
    for event in events_data:
        event_url = event['url']
        event_id = event['id']
        event_detail = scrap_event_detail(event_url, event_id, fighter_data)
        fight_detail_urls.extend(save_data(event_detail, EventRepository(session)))
    return fight_detail_urls

@task(max_retries=3, retry_delay=30)
def scrap_match_detail_task(session, fight_detail_urls, fighter_data)-> None:
    for fight_detail_url in fight_detail_urls:
        match_detail_total = scrap_match_detail_total(fight_detail_url, fighter_data)
        save_data(match_detail_total, EventRepository(session))

        match_detail_sig = scrap_match_detail_sig(fight_detail_url, fighter_data)
        save_data(match_detail_sig, EventRepository(session))
