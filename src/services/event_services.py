from domain.event import Event

class EventService:
    def __init__(self, event_repo):
        self.event_repo = event_repo

    async def get_event(self, event_id: int) -> Event:
        return await self.event_repo.get_by_id(event_id)
    
    async def get_all_events(self, page: int, limit: int, order_by: str = "id", order: str = "asc") -> list[Event]:
        return await self.event_repo.get_all(page, limit, order_by, order)