"""
User 서비스 레이어
사용자 인증, 회원가입, 로그인, 사용량 추적 등의 비즈니스 로직을 처리합니다.
"""
import re
import bcrypt
from typing import Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from user import repositories as user_repo
from user.dto import (
    UserCreateDTO, UserLoginDTO, UserProfileDTO, UserUsageDTO, 
    UserAuthResponseDTO, UserUsageUpdateDTO, UserStatsDTO
)
from user.models import UserSchema, UserProfileUpdate, UserProfileResponse
from user.exceptions import (
    UserNotFoundError, UserValidationError, UserAuthenticationError,
    UserDuplicateError, UserPasswordError, UserUsageLimitError, UserQueryError
)


# 기본 설정
DEFAULT_DAILY_LIMIT = 100


def _hash_password(password: str) -> str:
    """비밀번호를 bcrypt로 해시화합니다."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def _verify_password(password: str, hashed_password: str) -> bool:
    """비밀번호를 검증합니다."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def _validate_username(username: str) -> None:
    """사용자명 유효성 검사"""
    if not username or not username.strip():
        raise UserValidationError("username", username, "Username cannot be empty")
    
    if len(username.strip()) < 3:
        raise UserValidationError("username", username, "Username must be at least 3 characters")
    
    if len(username.strip()) > 50:
        raise UserValidationError("username", username, "Username must not exceed 50 characters")
    
    # 특수문자 체크 (영문, 숫자, 언더스코어만 허용)
    if not username.replace("_", "").isalnum():
        raise UserValidationError("username", username, "Username can only contain letters, numbers, and underscores")


def _validate_password(password: str) -> None:
    """
    비밀번호 유효성 검사
    - 최소 8자 이상
    - 대문자, 소문자, 숫자, 특수문자 중 3가지 이상 포함
    """
    if not password:
        raise UserValidationError("password", None, "Password cannot be empty")

    if len(password) < 8:
        raise UserValidationError("password", None, "Password must be at least 8 characters")

    if len(password) > 100:
        raise UserValidationError("password", None, "Password must not exceed 100 characters")

    # 비밀번호 복잡도 체크
    complexity_count = 0
    if re.search(r'[a-z]', password):  # 소문자
        complexity_count += 1
    if re.search(r'[A-Z]', password):  # 대문자
        complexity_count += 1
    if re.search(r'\d', password):  # 숫자
        complexity_count += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # 특수문자
        complexity_count += 1

    if complexity_count < 3:
        raise UserValidationError(
            "password", None,
            "Password must contain at least 3 of: lowercase, uppercase, number, special character"
        )


async def signup_user(session: AsyncSession, user_data: UserCreateDTO) -> UserAuthResponseDTO:
    """
    새 사용자를 등록합니다.
    """
    try:
        # 입력 검증
        _validate_username(user_data.username.strip())
        _validate_password(user_data.password)
        
        username = user_data.username.strip()
        
        # 기존 사용자 중복 체크
        existing_user = await user_repo.get_user_by_username(session, username)
        if existing_user:
            raise UserDuplicateError(username)
        
        # 비밀번호 해시화
        password_hash = _hash_password(user_data.password)
        
        # 새 사용자 스키마 생성
        new_user = UserSchema(
            username=username,
            password_hash=password_hash,
            total_requests=0,
            daily_requests=0,
            last_request_date=None,
            is_active=True
        )
        
        # 사용자 생성
        created_user = await user_repo.create_user(session, new_user)
        
        # 프로필 DTO 생성
        user_profile = UserProfileDTO(
            id=created_user.id,
            username=created_user.username,
            total_requests=created_user.total_requests,
            daily_requests=created_user.daily_requests,
            last_request_date=created_user.last_request_date,
            is_active=created_user.is_active,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at
        )
        
        return UserAuthResponseDTO(
            success=True,
            message=f"User '{username}' registered successfully",
            user=user_profile
        )
        
    except (UserValidationError, UserDuplicateError):
        raise
    except Exception as e:
        raise UserQueryError("signup_user", {"username": user_data.username}, str(e))


async def login_user(session: AsyncSession, login_data: UserLoginDTO) -> UserAuthResponseDTO:
    """
    사용자 로그인을 처리합니다.
    """
    try:
        # 입력 검증
        if not login_data.username or not login_data.username.strip():
            raise UserValidationError("username", login_data.username, "Username cannot be empty")
        
        if not login_data.password:
            raise UserValidationError("password", None, "Password cannot be empty")
        
        username = login_data.username.strip()
        
        # 사용자 조회
        user = await user_repo.get_user_by_username(session, username)
        if not user:
            raise UserAuthenticationError(username, "User not found")
        
        # 활성 상태 체크
        if not user.is_active:
            raise UserAuthenticationError(username, "User account is deactivated")
        
        # 비밀번호 검증
        if not _verify_password(login_data.password, user.password_hash):
            raise UserAuthenticationError(username, "Invalid password")
        
        # 프로필 DTO 생성
        user_profile = UserProfileDTO(
            id=user.id,
            username=user.username,
            total_requests=user.total_requests,
            daily_requests=user.daily_requests,
            last_request_date=user.last_request_date,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return UserAuthResponseDTO(
            success=True,
            message=f"User '{username}' logged in successfully",
            user=user_profile
        )
        
    except (UserValidationError, UserAuthenticationError):
        raise
    except Exception as e:
        raise UserQueryError("login_user", {"username": login_data.username}, str(e))


async def get_user_profile(session: AsyncSession, user_id: int) -> UserProfileDTO:
    """
    사용자 프로필을 조회합니다.
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserValidationError("user_id", user_id, "user_id must be a positive integer")
        
        user = await user_repo.get_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")
        
        return UserProfileDTO(
            id=user.id,
            username=user.username,
            total_requests=user.total_requests,
            daily_requests=user.daily_requests,
            last_request_date=user.last_request_date,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except (UserValidationError, UserNotFoundError):
        raise
    except Exception as e:
        raise UserQueryError("get_user_profile", {"user_id": user_id}, str(e))


async def get_user_usage(session: AsyncSession, user_id: int) -> UserUsageDTO:
    """
    사용자의 사용량 정보를 조회합니다.
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserValidationError("user_id", user_id, "user_id must be a positive integer")
        
        usage_stats = await user_repo.get_user_usage_stats(session, user_id)
        if not usage_stats:
            raise UserNotFoundError(user_id, "id")

        # 사용자별 일일 제한 사용 (설정되지 않은 경우 기본값 사용)
        daily_limit = usage_stats.get("daily_request_limit") or DEFAULT_DAILY_LIMIT
        remaining_requests = max(0, daily_limit - usage_stats["daily_requests"])

        return UserUsageDTO(
            user_id=usage_stats["user_id"],
            username=usage_stats["username"],
            total_requests=usage_stats["total_requests"],
            daily_requests=usage_stats["daily_requests"],
            last_request_date=usage_stats["last_request_date"],
            daily_limit=daily_limit,
            remaining_requests=remaining_requests
        )
        
    except (UserValidationError, UserNotFoundError):
        raise
    except Exception as e:
        raise UserQueryError("get_user_usage", {"user_id": user_id}, str(e))


async def update_user_usage(session: AsyncSession, usage_data: UserUsageUpdateDTO) -> UserUsageDTO:
    """
    사용자의 사용량을 업데이트합니다.
    일일 제한을 초과하면 예외를 발생시킵니다.
    """
    try:
        if not isinstance(usage_data.user_id, int) or usage_data.user_id <= 0:
            raise UserValidationError("user_id", usage_data.user_id, "user_id must be a positive integer")
        
        if not isinstance(usage_data.increment_requests, int) or usage_data.increment_requests < 0:
            raise UserValidationError("increment_requests", usage_data.increment_requests, "increment_requests must be a non-negative integer")
        
        # 현재 사용량 조회
        current_usage = await get_user_usage(session, usage_data.user_id)
        
        # 일일 제한 체크
        new_daily_requests = current_usage.daily_requests + usage_data.increment_requests
        if new_daily_requests > current_usage.daily_limit:
            raise UserUsageLimitError(
                current_usage.username or f"user_{usage_data.user_id}",
                new_daily_requests,
                current_usage.daily_limit
            )
        
        # 사용량 업데이트
        updated_user = await user_repo.update_user_usage(session, usage_data.user_id, usage_data.increment_requests)
        if not updated_user:
            raise UserNotFoundError(usage_data.user_id, "id")
        
        # 업데이트된 사용량 반환
        return await get_user_usage(session, usage_data.user_id)
        
    except (UserValidationError, UserNotFoundError, UserUsageLimitError):
        raise
    except Exception as e:
        raise UserQueryError("update_user_usage", {"user_id": usage_data.user_id}, str(e))


async def check_usage_limit(session: AsyncSession, user_id: int) -> bool:
    """
    사용자가 일일 제한 내에 있는지 확인합니다.
    True: 사용 가능, False: 제한 초과
    """
    try:
        usage = await get_user_usage(session, user_id)
        return usage.remaining_requests > 0
        
    except (UserValidationError, UserNotFoundError):
        raise
    except Exception as e:
        raise UserQueryError("check_usage_limit", {"user_id": user_id}, str(e))


async def get_user_stats(session: AsyncSession) -> UserStatsDTO:
    """
    전체 사용자 통계를 조회합니다.
    """
    try:
        total_users = await user_repo.get_total_users_count(session)
        active_users = await user_repo.get_active_users_count(session)
        total_requests_today = await user_repo.get_today_total_requests(session)
        
        average_requests_per_user = 0.0
        if active_users > 0:
            average_requests_per_user = total_requests_today / active_users
        
        return UserStatsDTO(
            total_users=total_users,
            active_users=active_users,
            total_requests_today=total_requests_today,
            average_requests_per_user=round(average_requests_per_user, 2)
        )
        
    except Exception as e:
        raise UserQueryError("get_user_stats", {}, str(e))


async def deactivate_user(session: AsyncSession, user_id: int) -> bool:
    """
    사용자 계정을 비활성화합니다.
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserValidationError("user_id", user_id, "user_id must be a positive integer")
        
        # 사용자 존재 확인
        user = await user_repo.get_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")
        
        return await user_repo.deactivate_user(session, user_id)
        
    except (UserValidationError, UserNotFoundError):
        raise
    except Exception as e:
        raise UserQueryError("deactivate_user", {"user_id": user_id}, str(e))


async def activate_user(session: AsyncSession, user_id: int) -> bool:
    """
    사용자 계정을 활성화합니다.
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserValidationError("user_id", user_id, "user_id must be a positive integer")
        
        # 사용자 존재 확인
        user = await user_repo.get_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")
        
        return await user_repo.activate_user(session, user_id)
        
    except (UserValidationError, UserNotFoundError):
        raise
    except Exception as e:
        raise UserQueryError("activate_user", {"user_id": user_id}, str(e))


# OAuth 사용자 지원 함수들 (NextAuth.js 연동)

async def get_or_create_oauth_user(
    session: AsyncSession,
    email: str,
    name: Optional[str] = None,
    picture: Optional[str] = None,
    provider_id: Optional[str] = None,
    provider: str = "google"
) -> UserProfileResponse:
    """
    OAuth 사용자 조회 또는 생성 (NextAuth.js 연동).
    존재하면 조회, 없으면 자동 생성.
    """
    try:
        # 이메일로 기존 사용자 조회
        existing_user = await user_repo.get_user_by_email(session, email)
        
        if existing_user:
            # 기존 사용자 정보 업데이트 (이름, 프로필 이미지 등)
            update_needed = False
            if name and existing_user.name != name:
                update_needed = True
            if picture and existing_user.picture != picture:
                update_needed = True
            
            if update_needed:
                profile_update = UserProfileUpdate(name=name, picture=picture)
                updated_user = await user_repo.update_user_profile(
                    session, existing_user.id, profile_update
                )
                return UserProfileResponse(
                    id=updated_user.id,
                    email=updated_user.email,
                    name=updated_user.name,
                    picture=updated_user.picture,
                    username=updated_user.username,
                    total_requests=updated_user.total_requests,
                    is_active=updated_user.is_active,
                    created_at=updated_user.created_at
                )
            else:
                return UserProfileResponse(
                    id=existing_user.id,
                    email=existing_user.email,
                    name=existing_user.name,
                    picture=existing_user.picture,
                    username=existing_user.username,
                    total_requests=existing_user.total_requests,
                    is_active=existing_user.is_active,
                    created_at=existing_user.created_at
                )
        
        else:
            # 새 OAuth 사용자 생성
            new_user = await user_repo.create_oauth_user(
                session=session,
                email=email,
                name=name,
                picture=picture,
                provider_id=provider_id,
                provider=provider
            )
            
            return UserProfileResponse(
                id=new_user.id,
                email=new_user.email,
                name=new_user.name,
                picture=new_user.picture,
                username=new_user.username,
                total_requests=new_user.total_requests,
                is_active=new_user.is_active,
                created_at=new_user.created_at
            )
    
    except Exception as e:
        raise UserQueryError("get_or_create_oauth_user", {"email": email}, str(e))


async def update_oauth_user_profile(
    session: AsyncSession,
    user_id: int,
    profile_update: UserProfileUpdate
) -> UserProfileResponse:
    """
    OAuth 사용자 프로필 업데이트.
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserValidationError("user_id", user_id, "user_id must be a positive integer")
        
        # 사용자 존재 확인
        user = await user_repo.get_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")
        
        # 프로필 업데이트
        updated_user = await user_repo.update_user_profile(session, user_id, profile_update)
        if not updated_user:
            raise UserNotFoundError(user_id, "id")
        
        return UserProfileResponse(
            id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            picture=updated_user.picture,
            username=updated_user.username,
            total_requests=updated_user.total_requests,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at
        )
        
    except (UserValidationError, UserNotFoundError):
        raise
    except Exception as e:
        raise UserQueryError("update_oauth_user_profile", {"user_id": user_id}, str(e))


async def get_oauth_user_profile(session: AsyncSession, user_id: int) -> UserProfileResponse:
    """
    OAuth 사용자 프로필 조회 (API 응답용).
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise UserValidationError("user_id", user_id, "user_id must be a positive integer")

        user = await user_repo.get_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")

        # 일일 사용량 계산 (날짜가 바뀌었으면 0으로 리셋)
        from datetime import date
        daily_requests = user.daily_requests
        if user.last_request_date is None or user.last_request_date.date() < date.today():
            daily_requests = 0

        remaining_requests = max(0, user.daily_request_limit - daily_requests)

        return UserProfileResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            username=user.username,
            total_requests=user.total_requests,
            daily_requests=daily_requests,
            daily_request_limit=user.daily_request_limit,
            remaining_requests=remaining_requests,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    except (UserValidationError, UserNotFoundError):
        raise
    except Exception as e:
        raise UserQueryError("get_oauth_user_profile", {"user_id": user_id}, str(e))


#############################
####### ADMIN SERVICES ######
#############################

from user.models import (
    UserAdminResponse, UserLimitUpdate, UserAdminStatusUpdate,
    UserActiveStatusUpdate, UserListResponse, AdminStatsResponse
)
from user.exceptions import (
    InsufficientPermissionError, InvalidLimitValueError, SelfModificationError
)
from conversation import repositories as conversation_repo
import math


async def get_all_users(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None
) -> UserListResponse:
    """
    모든 사용자 목록 조회 (관리자용).
    """
    try:
        # 페이지 크기 제한
        page_size = min(max(1, page_size), 100)
        page = max(1, page)

        users, total_count = await user_repo.find_all_users(
            session, page, page_size, search
        )

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return UserListResponse(
            users=[user.to_admin_response() for user in users],
            total_users=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        raise UserQueryError("get_all_users", {"page": page, "page_size": page_size}, str(e))


async def get_user_admin_detail(
    session: AsyncSession,
    user_id: int
) -> UserAdminResponse:
    """
    특정 사용자 상세 조회 (관리자용).
    """
    try:
        user = await user_repo.get_user_model_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")

        return user.to_admin_response()

    except UserNotFoundError:
        raise
    except Exception as e:
        raise UserQueryError("get_user_admin_detail", {"user_id": user_id}, str(e))


async def update_user_limit(
    session: AsyncSession,
    user_id: int,
    limit: int
) -> UserAdminResponse:
    """
    사용자 일일 요청 제한 수정.
    """
    try:
        # 제한 값 검증
        if limit < 0 or limit > 10000:
            raise InvalidLimitValueError(limit)

        # 사용자 존재 확인
        user = await user_repo.get_user_model_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")

        # 업데이트
        updated_user = await user_repo.update_daily_limit(session, user_id, limit)
        return updated_user.to_admin_response()

    except (UserNotFoundError, InvalidLimitValueError):
        raise
    except Exception as e:
        raise UserQueryError("update_user_limit", {"user_id": user_id, "limit": limit}, str(e))


async def update_user_admin_status(
    session: AsyncSession,
    user_id: int,
    is_admin: bool,
    current_user_id: int
) -> UserAdminResponse:
    """
    사용자 관리자 권한 수정.
    """
    try:
        # 자기 자신 수정 불가
        if user_id == current_user_id:
            raise SelfModificationError("admin status")

        # 사용자 존재 확인
        user = await user_repo.get_user_model_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")

        # 업데이트
        updated_user = await user_repo.update_admin_status(session, user_id, is_admin)
        return updated_user.to_admin_response()

    except (UserNotFoundError, SelfModificationError):
        raise
    except Exception as e:
        raise UserQueryError("update_user_admin_status", {"user_id": user_id}, str(e))


async def update_user_active_status(
    session: AsyncSession,
    user_id: int,
    is_active: bool,
    current_user_id: int
) -> UserAdminResponse:
    """
    사용자 활성화 상태 수정.
    """
    try:
        # 자기 자신 비활성화 불가
        if user_id == current_user_id and not is_active:
            raise SelfModificationError("active status")

        # 사용자 존재 확인
        user = await user_repo.get_user_model_by_id(session, user_id)
        if not user:
            raise UserNotFoundError(user_id, "id")

        # 업데이트
        updated_user = await user_repo.update_active_status(session, user_id, is_active)
        return updated_user.to_admin_response()

    except (UserNotFoundError, SelfModificationError):
        raise
    except Exception as e:
        raise UserQueryError("update_user_active_status", {"user_id": user_id}, str(e))


async def get_admin_stats(session: AsyncSession) -> AdminStatsResponse:
    """
    관리자 통계 조회.
    """
    try:
        total_users = await user_repo.get_total_users_count(session)
        active_users = await user_repo.get_active_users_count(session)
        admin_users = await user_repo.get_admin_users_count(session)
        total_requests_today = await user_repo.get_today_total_requests(session)
        total_conversations = await conversation_repo.get_total_conversations_count(session)

        return AdminStatsResponse(
            total_users=total_users,
            active_users=active_users,
            admin_users=admin_users,
            total_requests_today=total_requests_today,
            total_conversations=total_conversations
        )

    except Exception as e:
        raise UserQueryError("get_admin_stats", {}, str(e))