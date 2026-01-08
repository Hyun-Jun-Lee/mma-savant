from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from user.models import UserModel, UserSchema, UserProfileUpdate
from common.utils import utc_now, utc_today

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[UserSchema]:
    """
    user_id로 사용자 조회.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user.to_schema() if user else None
    
async def get_user_by_username(session: AsyncSession, username: str) -> Optional[UserSchema]:
    """
    username으로 사용자 조회.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.username == username)
    )
    user = result.scalar_one_or_none()
    return user.to_schema() if user else None


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[UserSchema]:
    """
    email로 사용자 조회 (OAuth 사용자).
    """
    result = await session.execute(
        select(UserModel).where(UserModel.email == email)
    )
    user = result.scalar_one_or_none()
    return user.to_schema() if user else None


async def get_user_by_provider_id(session: AsyncSession, provider_id: str) -> Optional[UserSchema]:
    """
    OAuth provider ID로 사용자 조회.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.provider_id == provider_id)
    )
    user = result.scalar_one_or_none()
    return user.to_schema() if user else None
    
async def create_user(session: AsyncSession, user: UserSchema) -> UserSchema:
    """
    새 사용자 생성.
    """
    db_user = UserModel.from_schema(user)
    session.add(db_user)
    await session.flush()
    await session.refresh(db_user)
    return db_user.to_schema()


async def create_oauth_user(
    session: AsyncSession,
    email: str,
    name: Optional[str] = None,
    picture: Optional[str] = None,
    provider_id: Optional[str] = None,
    provider: str = "google"
) -> UserSchema:
    """
    OAuth 사용자 생성 (NextAuth.js 연동).
    """
    user_data = UserSchema(
        email=email,
        name=name,
        picture=picture,
        provider_id=provider_id,
        provider=provider,
        is_active=True,
        total_requests=0,
        daily_requests=0
    )

    db_user = UserModel.from_schema(user_data)
    session.add(db_user)
    await session.flush()
    await session.refresh(db_user)
    return db_user.to_schema()


async def update_user_profile(
    session: AsyncSession,
    user_id: int,
    profile_update: UserProfileUpdate
) -> Optional[UserSchema]:
    """
    사용자 프로필 업데이트.
    """
    update_data = {}
    if profile_update.name is not None:
        update_data["name"] = profile_update.name
    if profile_update.picture is not None:
        update_data["picture"] = profile_update.picture

    if not update_data:
        return await get_user_by_id(session, user_id)

    update_data["updated_at"] = utc_now()

    await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(**update_data)
    )
    await session.flush()

    return await get_user_by_id(session, user_id)


async def update_user_usage(session: AsyncSession, user_id: int, increment: int = 1) -> Optional[UserSchema]:
    """
    사용자의 사용량을 업데이트합니다.
    새로운 날짜라면 daily_requests를 리셋하고, 같은 날이라면 증가시킵니다.
    """
    today = utc_today()

    # 현재 사용자 정보 조회
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    # 날짜 체크 - 새로운 날이면 daily_requests 리셋
    daily_requests = user.daily_requests
    if user.last_request_date is None or user.last_request_date.date() < today:
        daily_requests = 0

    # 사용량 업데이트
    await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(
            total_requests=UserModel.total_requests + increment,
            daily_requests=daily_requests + increment,
            last_request_date=utc_now()
        )
    )
    
    await session.flush()
    await session.commit()
    
    # 업데이트된 사용자 정보 반환
    return await get_user_by_id(session, user_id)


async def get_user_usage_stats(session: AsyncSession, user_id: int) -> Optional[dict]:
    """
    사용자의 사용량 통계를 조회합니다.
    """
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    today = utc_today()
    daily_requests = user.daily_requests

    # 날짜가 바뀌었다면 daily_requests는 0으로 계산
    if user.last_request_date is None or user.last_request_date.date() < today:
        daily_requests = 0
    
    return {
        "user_id": user.id,
        "username": user.username,
        "total_requests": user.total_requests,
        "daily_requests": daily_requests,
        "daily_request_limit": user.daily_request_limit,
        "last_request_date": user.last_request_date
    }


async def get_active_users_count(session: AsyncSession) -> int:
    """
    활성 사용자 수를 조회합니다.
    """
    result = await session.execute(
        select(func.count(UserModel.id)).where(UserModel.is_active == True)
    )
    return result.scalar() or 0


async def get_total_users_count(session: AsyncSession) -> int:
    """
    전체 사용자 수를 조회합니다.
    """
    result = await session.execute(
        select(func.count(UserModel.id))
    )
    return result.scalar() or 0


async def get_today_total_requests(session: AsyncSession) -> int:
    """
    오늘 총 요청 수를 조회합니다.
    """
    today = utc_today()
    result = await session.execute(
        select(func.sum(UserModel.daily_requests))
        .where(
            UserModel.last_request_date >= datetime.combine(today, datetime.min.time())
        )
    )
    return result.scalar() or 0


async def deactivate_user(session: AsyncSession, user_id: int) -> bool:
    """
    사용자를 비활성화합니다.
    """
    result = await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(is_active=False)
    )
    await session.flush()
    await session.commit()
    return result.rowcount > 0


async def activate_user(session: AsyncSession, user_id: int) -> bool:
    """
    사용자를 활성화합니다.
    """
    result = await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(is_active=True)
    )
    await session.flush()
    await session.commit()
    return result.rowcount > 0


#############################
####### ADMIN FUNCTIONS #####
#############################

async def find_all_users(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None
) -> Tuple[List[UserModel], int]:
    """
    모든 사용자 목록 조회 (페이지네이션, 검색).
    """
    # 기본 쿼리
    query = select(UserModel)

    # 검색 조건
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                UserModel.name.ilike(search_pattern),
                UserModel.email.ilike(search_pattern)
            )
        )

    # 전체 개수 조회
    count_query = select(func.count()).select_from(query.subquery())
    total_count_result = await session.execute(count_query)
    total_count = total_count_result.scalar() or 0

    # 페이지네이션 적용
    offset = (page - 1) * page_size
    query = query.order_by(UserModel.created_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(query)
    users = list(result.scalars().all())

    return users, total_count


async def update_daily_limit(
    session: AsyncSession,
    user_id: int,
    limit: int
) -> Optional[UserModel]:
    """
    사용자 일일 요청 제한 업데이트.
    """
    await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(daily_request_limit=limit, updated_at=utc_now())
    )
    await session.flush()
    await session.commit()

    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    return result.scalar_one_or_none()


async def update_admin_status(
    session: AsyncSession,
    user_id: int,
    is_admin: bool
) -> Optional[UserModel]:
    """
    사용자 관리자 권한 업데이트.
    """
    await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(is_admin=is_admin, updated_at=utc_now())
    )
    await session.flush()
    await session.commit()

    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    return result.scalar_one_or_none()


async def update_active_status(
    session: AsyncSession,
    user_id: int,
    is_active: bool
) -> Optional[UserModel]:
    """
    사용자 활성화 상태 업데이트.
    """
    await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(is_active=is_active, updated_at=utc_now())
    )
    await session.flush()
    await session.commit()

    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_admin_users_count(session: AsyncSession) -> int:
    """
    관리자 사용자 수를 조회합니다.
    """
    result = await session.execute(
        select(func.count(UserModel.id)).where(UserModel.is_admin == True)
    )
    return result.scalar() or 0


async def get_user_model_by_id(session: AsyncSession, user_id: int) -> Optional[UserModel]:
    """
    user_id로 UserModel 조회 (스키마 변환 없이).
    """
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    return result.scalar_one_or_none()
    