"""
관리자 API 라우터
사용자 관리, 시스템 통계 등 관리자 전용 기능
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from api.auth.dependencies import get_current_admin_user
from user.models import (
    UserModel,
    UserAdminResponse,
    UserListResponse,
    UserLimitUpdate,
    UserAdminStatusUpdate,
    UserActiveStatusUpdate,
    AdminStatsResponse
)
from user import services as user_service
from user.exceptions import (
    UserNotFoundError,
    SelfModificationError,
    InvalidLimitValueError
)


router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=UserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="이름 또는 이메일 검색"),
    admin_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    전체 사용자 목록 조회 (페이지네이션, 검색)

    - 관리자 권한 필요
    - 이름 또는 이메일로 검색 가능
    """
    try:
        result = await user_service.get_all_users(
            session=db,
            page=page,
            page_size=page_size,
            search=search
        )
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user_detail(
    user_id: int,
    admin_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    특정 사용자 상세 정보 조회

    - 관리자 권한 필요
    """
    try:
        result = await user_service.get_user_admin_detail(db, user_id)
        return result

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )


@router.patch("/users/{user_id}/limit", response_model=UserAdminResponse)
async def update_user_daily_limit(
    user_id: int,
    limit_update: UserLimitUpdate,
    admin_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    사용자 일일 요청 제한 수정

    - 관리자 권한 필요
    - 제한 범위: 0 ~ 10000
    """
    try:
        result = await user_service.update_user_limit(
            session=db,
            user_id=user_id,
            limit=limit_update.daily_request_limit
        )
        return result

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    except InvalidLimitValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update limit: {str(e)}"
        )


@router.patch("/users/{user_id}/admin", response_model=UserAdminResponse)
async def update_user_admin_status(
    user_id: int,
    status_update: UserAdminStatusUpdate,
    admin_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    사용자 관리자 권한 변경

    - 관리자 권한 필요
    - 자기 자신의 권한은 변경 불가
    """
    try:
        result = await user_service.update_user_admin_status(
            session=db,
            user_id=user_id,
            is_admin=status_update.is_admin,
            current_user_id=admin_user.id
        )
        return result

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    except SelfModificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update admin status: {str(e)}"
        )


@router.patch("/users/{user_id}/active", response_model=UserAdminResponse)
async def update_user_active_status(
    user_id: int,
    status_update: UserActiveStatusUpdate,
    admin_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    사용자 활성화 상태 변경

    - 관리자 권한 필요
    - 자기 자신은 비활성화 불가
    """
    try:
        result = await user_service.update_user_active_status(
            session=db,
            user_id=user_id,
            is_active=status_update.is_active,
            current_user_id=admin_user.id
        )
        return result

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    except SelfModificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update active status: {str(e)}"
        )


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin_user: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    관리자 대시보드 통계 조회

    - 총 사용자 수
    - 활성 사용자 수
    - 관리자 수
    - 오늘 총 요청 수
    - 총 대화 세션 수
    """
    try:
        result = await user_service.get_admin_stats(db)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )
