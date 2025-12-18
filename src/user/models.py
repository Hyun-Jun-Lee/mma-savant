from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from pydantic import ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from common.base_model import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class UserSchema(BaseSchema):
    # 기존 필드 (기본 사용자용)
    username: Optional[str] = None
    password_hash: Optional[str] = None

    # OAuth 사용자용 필드 (NextAuth.js 연동)
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    provider_id: Optional[str] = None  # OAuth provider의 고유 ID
    provider: Optional[str] = None  # google, github 등

    # 공통 필드
    total_requests: int = 0
    daily_requests: int = 0
    daily_request_limit: int = 100  # 일일 요청 제한
    last_request_date: Optional[datetime] = None
    is_active: bool = True
    is_admin: bool = False  # 관리자 여부

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseSchema):
    """API 응답용 사용자 프로필 스키마"""
    id: int
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    username: Optional[str] = None
    total_requests: int = 0
    daily_requests: int = 0
    daily_request_limit: int = 100  # 일일 요청 제한
    remaining_requests: int = 100  # daily_limit - daily_requests
    is_active: bool = True
    is_admin: bool = False  # 관리자 여부
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseSchema):
    """사용자 프로필 업데이트용 스키마"""
    name: Optional[str] = None
    picture: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


#############################
####### ADMIN SCHEMA ########
#############################

class UserAdminResponse(BaseSchema):
    """관리자용 사용자 상세 응답"""
    id: int
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    is_admin: bool
    total_requests: int
    daily_requests: int
    daily_request_limit: int
    last_request_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLimitUpdate(BaseSchema):
    """사용자 요청 제한 업데이트"""
    daily_request_limit: int = Field(ge=0, le=10000)

    model_config = ConfigDict(from_attributes=True)


class UserAdminStatusUpdate(BaseSchema):
    """사용자 관리자 권한 업데이트"""
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserActiveStatusUpdate(BaseSchema):
    """사용자 활성화 상태 업데이트"""
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseSchema):
    """사용자 목록 응답 (페이지네이션)"""
    users: List[UserAdminResponse]
    total_users: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class AdminStatsResponse(BaseSchema):
    """관리자 통계 응답"""
    total_users: int
    active_users: int
    admin_users: int
    total_requests_today: int
    total_conversations: int

    model_config = ConfigDict(from_attributes=True)


#############################
########## MODEL ###########
#############################

class UserModel(BaseModel):
    __tablename__ = "user"
    
    # 기존 필드 (기본 사용자용) - nullable로 변경
    username = Column(String, nullable=True, unique=True)
    password_hash = Column(String, nullable=True)
    
    # OAuth 사용자용 필드 (NextAuth.js 연동)
    email = Column(String, nullable=True, unique=True)
    name = Column(String, nullable=True)
    picture = Column(Text, nullable=True)  # URL이 길 수 있으므로 Text 사용
    provider_id = Column(String, nullable=True)  # OAuth provider의 고유 ID
    provider = Column(String, nullable=True)  # google, github 등
    
    # 공통 필드
    total_requests = Column(Integer, default=0, nullable=False)
    daily_requests = Column(Integer, default=0, nullable=False)
    daily_request_limit = Column(Integer, default=100, nullable=False)  # 일일 요청 제한
    last_request_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)  # 관리자 여부

    conversations = relationship("ConversationModel", back_populates="user")

    @classmethod
    def from_schema(cls, user: UserSchema):
        model = cls(
            username=user.username,
            password_hash=user.password_hash,
            email=user.email,
            name=user.name,
            picture=user.picture,
            provider_id=user.provider_id,
            provider=user.provider,
            total_requests=user.total_requests,
            daily_requests=user.daily_requests,
            daily_request_limit=user.daily_request_limit,
            last_request_date=user.last_request_date,
            is_active=user.is_active,
            is_admin=user.is_admin
        )
        # 스키마에 id가 있으면 설정 (DB에서 조회한 경우)
        if hasattr(user, 'id') and user.id:
            model.id = user.id
        # datetime 필드는 DB에서 자동 관리하므로 설정하지 않음
        return model

    def to_schema(self) -> UserSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return UserSchema(
            id=self.id,
            username=self.username,
            password_hash=self.password_hash,
            email=self.email,
            name=self.name,
            picture=self.picture,
            provider_id=self.provider_id,
            provider=self.provider,
            total_requests=self.total_requests,
            daily_requests=self.daily_requests,
            daily_request_limit=self.daily_request_limit,
            last_request_date=self.last_request_date,
            is_active=self.is_active,
            is_admin=self.is_admin,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
    
    def to_profile_response(self, daily_requests_override: Optional[int] = None) -> UserProfileResponse:
        """API 응답용 프로필 변환 (민감한 정보 제외)"""
        daily_requests = daily_requests_override if daily_requests_override is not None else self.daily_requests
        remaining_requests = max(0, self.daily_request_limit - daily_requests)

        return UserProfileResponse(
            id=self.id,
            email=self.email,
            name=self.name,
            picture=self.picture,
            username=self.username,
            total_requests=self.total_requests,
            daily_requests=daily_requests,
            daily_request_limit=self.daily_request_limit,
            remaining_requests=remaining_requests,
            is_active=self.is_active,
            is_admin=self.is_admin,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_admin_response(self) -> UserAdminResponse:
        """관리자용 사용자 응답 변환"""
        return UserAdminResponse(
            id=self.id,
            email=self.email,
            name=self.name,
            picture=self.picture,
            is_admin=self.is_admin,
            total_requests=self.total_requests,
            daily_requests=self.daily_requests,
            daily_request_limit=self.daily_request_limit,
            last_request_date=self.last_request_date,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )