from services.event_services import EventService
from services.match_services import MatchService
from exceptions.event_exception import EventNotFoundException

async def retrieve_event(event_service: EventService, match_service: MatchService, event_id: int):
    event = await event_service.get_event(event_id)

    if not event:
        raise EventNotFoundException(event_id)
    
    matches = await match_service.get_all_matches(event_id)
    return {
        "event": event.to_dict(),
        "matches": [match.to_dict() for match in matches]
    }