"""
Match 도메인 예외 클래스
"""
from typing import Optional, Any, List


class MatchException(Exception):
    """Match 도메인의 기본 예외 클래스"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MatchNotFoundError(MatchException):
    """매치를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, match_identifier: Any, search_type: str = "id"):
        message = f"Match not found with {search_type}: {match_identifier}"
        details = {"match_identifier": match_identifier, "search_type": search_type}
        super().__init__(message, details)


class MatchValidationError(MatchException):
    """매치 데이터 검증 실패 시 발생하는 예외"""
    
    def __init__(self, field: str, value: Any, reason: str):
        message = f"Invalid match data for field '{field}': {reason}"
        details = {"field": field, "value": value, "reason": reason}
        super().__init__(message, details)


class MatchResultError(MatchException):
    """매치 결과 관련 오류 시 발생하는 예외"""
    
    def __init__(self, match_id: int, result_data: Any, reason: str):
        message = f"Invalid match result for match {match_id}: {reason}"
        details = {"match_id": match_id, "result_data": result_data, "reason": reason}
        super().__init__(message, details)


class MatchMethodError(MatchException):
    """매치 결승 방법 관련 오류 시 발생하는 예외"""
    
    def __init__(self, method: str, reason: str):
        message = f"Invalid match method '{method}': {reason}"
        details = {"method": method, "reason": reason}
        super().__init__(message, details)


class MatchRoundError(MatchException):
    """매치 라운드 관련 오류 시 발생하는 예외"""
    
    def __init__(self, round_number: Any, reason: str):
        message = f"Invalid match round '{round_number}': {reason}"
        details = {"round_number": round_number, "reason": reason}
        super().__init__(message, details)


class MatchTimeError(MatchException):
    """매치 시간 관련 오류 시 발생하는 예외"""
    
    def __init__(self, time_value: Any, reason: str):
        message = f"Invalid match time '{time_value}': {reason}"
        details = {"time_value": time_value, "reason": reason}
        super().__init__(message, details)


class MatchFighterError(MatchException):
    """매치 파이터 관련 오류 시 발생하는 예외"""
    
    def __init__(self, fighter_ids: List[int], reason: str):
        message = f"Invalid match fighters {fighter_ids}: {reason}"
        details = {"fighter_ids": fighter_ids, "reason": reason}
        super().__init__(message, details)


class MatchCreationError(MatchException):
    """매치 생성 실패 시 발생하는 예외"""
    
    def __init__(self, match_data: dict, reason: str):
        message = f"Failed to create match: {reason}"
        details = {"match_data": match_data, "reason": reason}
        super().__init__(message, details)


class MatchUpdateError(MatchException):
    """매치 업데이트 실패 시 발생하는 예외"""
    
    def __init__(self, match_id: int, update_data: dict, reason: str):
        message = f"Failed to update match {match_id}: {reason}"
        details = {"match_id": match_id, "update_data": update_data, "reason": reason}
        super().__init__(message, details)


class MatchDeleteError(MatchException):
    """매치 삭제 실패 시 발생하는 예외"""
    
    def __init__(self, match_id: int, reason: str):
        message = f"Failed to delete match {match_id}: {reason}"
        details = {"match_id": match_id, "reason": reason}
        super().__init__(message, details)


class MatchDuplicateError(MatchException):
    """중복된 매치 생성 시 발생하는 예외"""
    
    def __init__(self, event_id: int, fighter_ids: List[int]):
        message = f"Duplicate match: fighters {fighter_ids} already have a match in event {event_id}"
        details = {"event_id": event_id, "fighter_ids": fighter_ids}
        super().__init__(message, details)


class MatchStatisticsError(MatchException):
    """매치 통계 관련 오류 시 발생하는 예외"""
    
    def __init__(self, match_id: int, stat_type: str, reason: str):
        message = f"Invalid match statistics for match {match_id}, type '{stat_type}': {reason}"
        details = {"match_id": match_id, "stat_type": stat_type, "reason": reason}
        super().__init__(message, details)


class MatchWeightClassError(MatchException):
    """매치 체급 관련 오류 시 발생하는 예외"""
    
    def __init__(self, weight_class_id: int, reason: str):
        message = f"Invalid weight class {weight_class_id}: {reason}"
        details = {"weight_class_id": weight_class_id, "reason": reason}
        super().__init__(message, details)


class MatchQueryError(MatchException):
    """매치 쿼리 실행 오류 시 발생하는 예외"""
    
    def __init__(self, query_type: str, parameters: dict, reason: str):
        message = f"Match query '{query_type}' failed: {reason}"
        details = {"query_type": query_type, "parameters": parameters, "reason": reason}
        super().__init__(message, details)


class MatchParticipantError(MatchException):
    """매치 참가자 관련 오류 시 발생하는 예외"""
    
    def __init__(self, match_id: int, participant_issue: str):
        message = f"Match participant error for match {match_id}: {participant_issue}"
        details = {"match_id": match_id, "participant_issue": participant_issue}
        super().__init__(message, details)