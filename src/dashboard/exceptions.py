"""
Dashboard 도메인 예외 클래스
"""
from typing import Optional


class DashboardException(Exception):
    """Dashboard 도메인의 기본 예외 클래스"""

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DashboardQueryError(DashboardException):
    """대시보드 쿼리 실행 오류"""

    def __init__(self, query_type: str, reason: str):
        message = f"Dashboard query '{query_type}' failed: {reason}"
        details = {"query_type": query_type, "reason": reason}
        super().__init__(message, details)
