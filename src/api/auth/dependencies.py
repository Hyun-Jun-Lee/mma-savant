"""
FastAPI 인증 의존성
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .jwt_handler import jwt_handler, TokenData
from database.connection.postgres_conn import get_async_db
from user.models import UserModel
from user import repositories as user_repo
from user import services as user_service


# HTTP Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    JWT 토큰에서 사용자 정보 추출
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWT 토큰 검증 및 디코딩
    token_data = jwt_handler.decode_token(credentials.credentials)
    
    # 토큰 만료 확인
    if not jwt_handler.verify_token_expiry(token_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_async_db)
) -> UserModel:
    """
    토큰 정보를 기반으로 데이터베이스에서 사용자 조회/생성
    - 일반 로그인: user_id로 조회
    - OAuth 로그인: email로 조회/생성
    """
    try:
        user_schema = None

        # 1. 일반 로그인 (user_id가 있는 경우)
        if token_data.user_id:
            user_schema = await user_repo.get_user_by_id(db, token_data.user_id)

            if not user_schema:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

        # 2. OAuth 로그인 (이메일이 있는 경우)
        elif token_data.email:
            user_schema = await user_repo.get_user_by_email(db, token_data.email)

            if not user_schema:
                # OAuth 사용자가 처음 로그인하는 경우 자동 생성
                user_schema = await user_repo.create_oauth_user(
                    session=db,
                    email=token_data.email,
                    name=token_data.name,
                    picture=token_data.picture,
                    provider_id=token_data.sub
                )

        # 3. provider_id로 조회 (fallback)
        else:
            user_schema = await user_repo.get_user_by_provider_id(db, token_data.sub)

            if not user_schema:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )

        # UserSchema를 UserModel로 변환
        user = UserModel.from_schema(user_schema)

        # 사용자 활성 상태 확인
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[UserModel]:
    """
    선택적 인증 - 토큰이 있으면 사용자 정보 반환, 없으면 None
    """
    if not credentials:
        return None

    try:
        token_data = jwt_handler.decode_token(credentials.credentials)
        if not jwt_handler.verify_token_expiry(token_data):
            return None

        user_schema = None

        # 1. 일반 로그인 (user_id가 있는 경우)
        if token_data.user_id:
            user_schema = await user_repo.get_user_by_id(db, token_data.user_id)
        # 2. OAuth 로그인 (이메일이 있는 경우)
        elif token_data.email:
            user_schema = await user_repo.get_user_by_email(db, token_data.email)
        # 3. provider_id로 조회 (fallback)
        else:
            user_schema = await user_repo.get_user_by_provider_id(db, token_data.sub)

        return UserModel.from_schema(user_schema) if user_schema else None

    except HTTPException:
        return None


async def get_current_admin_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    관리자 권한 검증

    1. get_current_user로 인증된 사용자 확인
    2. is_admin == True 확인
    3. 관리자가 아니면 403 Forbidden
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )

    return current_user