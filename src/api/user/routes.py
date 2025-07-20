"""
사용자 관리 API 라우터
NextAuth.js OAuth 사용자 지원
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_async_db
from api.auth.dependencies import get_current_user_token, get_current_user
from api.auth.jwt_handler import TokenData
from user.models import UserModel, UserProfileResponse, UserProfileUpdate
from user import services as user_service
from user.exceptions import (
    UserNotFoundError, UserValidationError, UserQueryError
)


router = APIRouter(prefix="/api/user", tags=["User Management"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    현재 로그인한 사용자의 프로필 조회
    """
    try:
        user_profile = await user_service.get_oauth_user_profile(db, current_user.id)
        return user_profile
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {e.message}"
        )
    except UserQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e.message}"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    현재 로그인한 사용자의 프로필 업데이트
    """
    try:
        updated_profile = await user_service.update_oauth_user_profile(
            db, current_user.id, profile_update
        )
        return updated_profile
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {e.message}"
        )
    except UserValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except UserQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e.message}"
        )


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile_by_id(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    특정 사용자 프로필 조회 (관리자용 또는 자신의 프로필)
    """
    try:
        # 자신의 프로필이거나 관리자만 접근 가능하도록 제한할 수 있음
        # 현재는 모든 로그인 사용자가 접근 가능
        
        user_profile = await user_service.get_oauth_user_profile(db, user_id)
        return user_profile
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {e.message}"
        )
    except UserValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e.message}"
        )
    except UserQueryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e.message}"
        )


@router.post("/increment-usage")
async def increment_user_usage(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    사용자 요청 횟수 증가 (API 호출 시 자동 증가)
    """
    try:
        # 사용량 증가
        from user.dto import UserUsageUpdateDTO
        usage_update = UserUsageUpdateDTO(
            user_id=current_user.id,
            increment_requests=1
        )
        
        updated_usage = await user_service.update_user_usage(db, usage_update)
        
        return {
            "success": True,
            "message": "Usage updated successfully",
            "usage": {
                "total_requests": updated_usage.total_requests,
                "daily_requests": updated_usage.daily_requests,
                "remaining_requests": updated_usage.remaining_requests
            }
        }
        
    except Exception as e:
        # 사용량 업데이트 실패해도 API 요청 자체는 성공으로 처리
        return {
            "success": False,
            "message": f"Usage update failed: {str(e)}"
        }


@router.get("/check-auth")
async def check_authentication(
    token_data: TokenData = Depends(get_current_user_token),
    current_user: UserModel = Depends(get_current_user)
):
    """
    인증 상태 확인 (토큰 검증)
    """
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "token_valid": True
    }


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    현재 사용자 정보 조회 (간단한 별칭)
    """
    return await get_user_profile(current_user, db)