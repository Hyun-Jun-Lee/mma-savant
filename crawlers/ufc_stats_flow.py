from typing import List

from prefect import Flow, task

from repository import BaseRepository, FighterRepository, EventRepository

@task
def scrap_all_fighter():
    pass

@task
def scrap_all_events():
    pass

@task
def scrap_event_detail():
    pass

@task
def save_data(data : List[dict], repository: BaseRepository):
    pass

with Flow("ufc_stats_flow") as flow:
    # TODO
    session = None

    fighters_data = scrap_all_fighter()
    save_data(fighters_data, FighterRepository(session))

    # NOTE : query fighter id by dict[name, id]?
    events_data = scrap_all_events()
    save_data(events_data, EventRepository(session))

    # NOTE : query event id by dict[name, id]?
    event_detail_data = scrap_event_detail()
    save_data(event_detail_data, EventRepository(session))
    
