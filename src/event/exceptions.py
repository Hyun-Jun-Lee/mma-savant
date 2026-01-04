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
    """이벤트 날짜 관련 예외"""

    def __init__(self, value: Any, reason: str):
        message = f"Invalid date value '{value}': {reason}"
        details = {"value": value, "reason": reason}
        super().__init__(message, details)


class EventQueryError(EventException):
    """이벤트 쿼리 실행 실패 시 발생하는 예외"""

    def __init__(self, query_name: str, params: dict, reason: str):
        message = f"Event query '{query_name}' failed: {reason}"
        details = {"query_name": query_name, "params": params, "reason": reason}
        super().__init__(message, details)