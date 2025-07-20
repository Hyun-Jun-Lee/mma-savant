"""
FastAPI 인증 의존성
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .jwt_handler import jwt_handler, TokenData
from database.session import get_async_db
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
    NextAuth.js OAuth 사용자를 자동으로 DB에 저장
    """
    try:
        # 이메일로 사용자 조회 (OAuth 사용자는 이메일이 주요 식별자)
        if token_data.email:
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
            
            # UserSchema를 UserModel로 변환
            user = UserModel.from_schema(user_schema)
            
        else:
            # 이메일이 없는 경우 sub(provider ID)로 조회
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
        
        if token_data.email:
            user_schema = await user_repo.get_user_by_email(db, token_data.email)
            return UserModel.from_schema(user_schema) if user_schema else None
        else:
            user_schema = await user_repo.get_user_by_provider_id(db, token_data.sub)
            return UserModel.from_schema(user_schema) if user_schema else None
            
    except HTTPException:
        return None