from exceptions.base_exception import BaseException

class EventNotFoundException(BaseException):
    status_code = 404

    def __init__(self, event_id: int):
        super().__init__(f"Event with id {event_id} not found")
