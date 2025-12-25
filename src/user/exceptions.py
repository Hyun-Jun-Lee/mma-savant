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


# Admin 관련 예외 클래스

class InsufficientPermissionError(UserException):
    """관리자 권한이 없을 때 발생하는 예외"""

    def __init__(self, user_id: int, required_permission: str = "admin"):
        message = f"User {user_id} does not have {required_permission} permission"
        details = {"user_id": user_id, "required_permission": required_permission}
        super().__init__(message, details)


class InvalidLimitValueError(UserException):
    """유효하지 않은 제한 값일 때 발생하는 예외"""

    def __init__(self, value: int, min_value: int = 0, max_value: int = 10000):
        message = f"Invalid limit value: {value}. Must be between {min_value} and {max_value}"
        details = {"value": value, "min_value": min_value, "max_value": max_value}
        super().__init__(message, details)


class SelfModificationError(UserException):
    """자기 자신의 권한/상태를 변경하려 할 때 발생하는 예외"""

    def __init__(self, user_id: int, operation: str):
        message = f"User {user_id} cannot {operation} their own account"
        details = {"user_id": user_id, "operation": operation}
        super().__init__(message, details)


# 하위 호환성을 위한 별칭
UserDomainError = UserException