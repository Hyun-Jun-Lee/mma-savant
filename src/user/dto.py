"""
User 도메인 DTO 클래스들
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreateDTO(BaseModel):
    """사용자 생성용 DTO"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명 (3-50자)")
    password: str = Field(..., min_length=6, max_length=100, description="비밀번호 (6-100자)")


class UserLoginDTO(BaseModel):
    """사용자 로그인용 DTO"""
    username: str = Field(..., description="사용자명")
    password: str = Field(..., description="비밀번호")


class UserProfileDTO(BaseModel):
    """사용자 프로필 DTO (비밀번호 제외)"""
    id: int
    username: str
    total_requests: int = Field(default=0, description="총 요청 수")
    daily_requests: int = Field(default=0, description="일일 요청 수")
    last_request_date: Optional[datetime] = Field(default=None, description="마지막 요청 날짜")
    is_active: bool = Field(default=True, description="활성 상태")
    created_at: datetime
    updated_at: datetime


class UserUsageDTO(BaseModel):
    """사용자 사용량 통계 DTO"""
    user_id: int
    username: str
    total_requests: int
    daily_requests: int
    last_request_date: Optional[datetime]
    daily_limit: int = Field(default=100, description="일일 요청 제한")
    remaining_requests: int = Field(description="남은 요청 수")


class UserAuthResponseDTO(BaseModel):
    """인증 응답 DTO"""
    success: bool
    message: str
    user: Optional[UserProfileDTO] = None
    token: Optional[str] = None  # 추후 JWT 토큰 등을 위해 예비


class UserUsageUpdateDTO(BaseModel):
    """사용량 업데이트용 DTO"""
    user_id: int
    increment_requests: int = Field(default=1, description="증가시킬 요청 수")


class UserStatsDTO(BaseModel):
    """사용자 통계 DTO"""
    total_users: int
    active_users: int
    total_requests_today: int
    average_requests_per_user: float