"""
User 도메인 예외 클래스
"""
from typing import Optional, Any


class UserException(Exception):
    """User 도메인의 기본 예외 클래스"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class UserNotFoundError(UserException):
    """사용자를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, user_identifier: Any, search_type: str = "id"):
        message = f"User not found with {search_type}: {user_identifier}"
        details = {"user_identifier": user_identifier, "search_type": search_type}
        super().__init__(message, details)


class UserValidationError(UserException):
    """사용자 데이터 검증 실패 시 발생하는 예외"""
    
    def __init__(self, field: str, value: Any, reason: str):
        message = f"Invalid user data for field '{field}': {reason}"
        details = {"field": field, "value": value, "reason": reason}
        super().__init__(message, details)


class UserAuthenticationError(UserException):
    """사용자 인증 실패 시 발생하는 예외"""
    
    def __init__(self, username: str, reason: str = "Invalid credentials"):
        message = f"Authentication failed for user '{username}': {reason}"
        details = {"username": username, "reason": reason}
        super().__init__(message, details)


class UserDuplicateError(UserException):
    """중복된 사용자 생성 시 발생하는 예외"""
    
    def __init__(self, username: str):
        message = f"User '{username}' already exists"
        details = {"username": username}
        super().__init__(message, details)


class UserPasswordError(UserException):
    """비밀번호 관련 오류 시 발생하는 예외"""
    
    def __init__(self, username: str, reason: str):
        message = f"Password error for user '{username}': {reason}"
        details = {"username": username, "reason": reason}
        super().__init__(message, details)


class UserUsageLimitError(UserException):
    """사용량 제한 초과 시 발생하는 예외"""
    
    def __init__(self, username: str, current_usage: int, limit: int):
        message = f"Usage limit exceeded for user '{username}': {current_usage}/{limit}"
        details = {"username": username, "current_usage": current_usage, "limit": limit}
        super().__init__(message, details)


class UserQueryError(UserException):
    """사용자 쿼리 실행 오류 시 발생하는 예외"""
    
    def __init__(self, query_type: str, parameters: dict, reason: str):
        message = f"User query '{query_type}' failed: {reason}"
        details = {"query_type": query_type, "parameters": parameters, "reason": reason}
        super().__init__(message, details)


class UserSessionError(UserException):
    """사용자 세션 관련 오류 시 발생하는 예외"""
    
    def __init__(self, username: str, reason: str):
        message = f"Session error for user '{username}': {reason}"
        details = {"username": username, "reason": reason}
        super().__init__(message, details)


# 하위 호환성을 위한 별칭
UserDomainError = UserException