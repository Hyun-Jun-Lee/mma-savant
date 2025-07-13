"""
Event 도메인 예외 클래스
"""
from typing import Optional, Any


class EventException(Exception):
    """Event 도메인의 기본 예외 클래스"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class EventNotFoundError(EventException):
    """이벤트를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, event_identifier: Any, search_type: str = "id"):
        message = f"Event not found with {search_type}: {event_identifier}"
        details = {"event_identifier": event_identifier, "search_type": search_type}
        super().__init__(message, details)


class EventValidationError(EventException):
    """이벤트 데이터 검증 실패 시 발생하는 예외"""
    
    def __init__(self, field: str, value: Any, reason: str):
        message = f"Invalid event data for field '{field}': {reason}"
        details = {"field": field, "value": value, "reason": reason}
        super().__init__(message, details)


class EventDateError(EventException):
    """이벤트 날짜 관련 오류 시 발생하는 예외"""
    
    def __init__(self, date_value: Any, reason: str):
        message = f"Invalid event date: {reason}"
        details = {"date_value": date_value, "reason": reason}
        super().__init__(message, details)


class EventLocationError(EventException):
    """이벤트 장소 관련 오류 시 발생하는 예외"""
    
    def __init__(self, location: str, reason: str):
        message = f"Invalid event location '{location}': {reason}"
        details = {"location": location, "reason": reason}
        super().__init__(message, details)


class EventCreationError(EventException):
    """이벤트 생성 실패 시 발생하는 예외"""
    
    def __init__(self, event_data: dict, reason: str):
        message = f"Failed to create event: {reason}"
        details = {"event_data": event_data, "reason": reason}
        super().__init__(message, details)


class EventUpdateError(EventException):
    """이벤트 업데이트 실패 시 발생하는 예외"""
    
    def __init__(self, event_id: int, update_data: dict, reason: str):
        message = f"Failed to update event {event_id}: {reason}"
        details = {"event_id": event_id, "update_data": update_data, "reason": reason}
        super().__init__(message, details)


class EventDeleteError(EventException):
    """이벤트 삭제 실패 시 발생하는 예외"""
    
    def __init__(self, event_id: int, reason: str):
        message = f"Failed to delete event {event_id}: {reason}"
        details = {"event_id": event_id, "reason": reason}
        super().__init__(message, details)


class EventDuplicateError(EventException):
    """중복된 이벤트 생성 시 발생하는 예외"""
    
    def __init__(self, event_name: str, event_date: str):
        message = f"Duplicate event: '{event_name}' on {event_date} already exists"
        details = {"event_name": event_name, "event_date": event_date}
        super().__init__(message, details)


class EventMatchesNotFoundError(EventException):
    """이벤트에 연결된 매치가 없을 때 발생하는 예외"""
    
    def __init__(self, event_id: int):
        message = f"No matches found for event {event_id}"
        details = {"event_id": event_id}
        super().__init__(message, details)


class EventQueryError(EventException):
    """이벤트 쿼리 실행 오류 시 발생하는 예외"""
    
    def __init__(self, query_type: str, parameters: dict, reason: str):
        message = f"Event query '{query_type}' failed: {reason}"
        details = {"query_type": query_type, "parameters": parameters, "reason": reason}
        super().__init__(message, details)