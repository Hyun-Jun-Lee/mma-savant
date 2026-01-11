"""
인증 관련 API 라우터
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
import jwt
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from config import Config
from user.dto import UserCreateDTO, UserLoginDTO
from user import services as user_service
from user.exceptions import (
    UserValidationError, UserDuplicateError, UserNotFoundError,
    UserAuthenticationError, UserPasswordError
)

router = APIRouter(prefix="/api/user", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    """Google OAuth 토큰 요청"""
    google_token: str
    email: str
    name: str
    picture: Optional[str] = None


class JWTTokenResponse(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SignupRequest(BaseModel):
    """회원가입 요청"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명 (3-50자, 영문/숫자/언더스코어)")
    email: Optional[EmailStr] = Field(None, description="이메일 (선택)")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호 (8-100자)")


class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str = Field(..., description="사용자명")
    password: str = Field(..., description="비밀번호")


class AuthResponse(BaseModel):
    """인증 응답"""
    success: bool
    message: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: Optional[dict] = None


@router.post("/google-token", response_model=JWTTokenResponse)
async def exchange_google_token(request: GoogleTokenRequest):
    """
    Google OAuth 토큰을 FastAPI용 JWT 토큰으로 교환
    """
    try:
        secret_key = os.getenv("NEXTAUTH_SECRET")
        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT secret not configured"
            )
        
        # JWT 페이로드 생성
        now = datetime.now(timezone.utc)
        payload = {
            "sub": request.email,  # 이메일을 사용자 ID로 사용
            "email": request.email,
            "name": request.name,
            "picture": request.picture,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
        }
        
        # JWT 토큰 생성
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        
        return JWTTokenResponse(
            access_token=token,
            expires_in=24 * 60 * 60  # 24시간
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create JWT token: {str(e)}"
        )


def _create_jwt_token(user_id: int, username: str, email: Optional[str] = None) -> tuple[str, int]:
    """JWT 토큰 생성 헬퍼 함수"""
    secret_key = Config.NEXTAUTH_SECRET
    if not secret_key:
        raise ValueError("JWT secret not configured")

    now = datetime.now(timezone.utc)
    expires_in = Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 분 → 초 변환

    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "username": username,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token, expires_in


@router.post("/signup", response_model=AuthResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    일반 회원가입

    - 사용자명: 3-50자, 영문/숫자/언더스코어만 허용
    - 비밀번호: 8-100자, 대소문자/숫자/특수문자 중 3가지 이상 조합
    """
    try:
        # DTO 변환
        user_data = UserCreateDTO(
            username=request.username,
            password=request.password
        )

        # 회원가입 처리
        result = await user_service.signup_user(db, user_data)

        if not result.success or not result.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )

        # JWT 토큰 생성
        token, expires_in = _create_jwt_token(
            user_id=result.user.id,
            username=result.user.username,
            email=request.email
        )

        return AuthResponse(
            success=True,
            message="회원가입이 완료되었습니다.",
            access_token=token,
            expires_in=expires_in,
            user={
                "id": result.user.id,
                "username": result.user.username,
                "email": request.email
            }
        )

    except UserValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except UserDuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    일반 로그인

    - 사용자명과 비밀번호로 인증
    - 성공 시 JWT 토큰 발급
    """
    try:
        # DTO 변환
        login_data = UserLoginDTO(
            username=request.username,
            password=request.password
        )

        # 로그인 처리
        result = await user_service.login_user(db, login_data)

        if not result.success or not result.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )

        # JWT 토큰 생성
        token, expires_in = _create_jwt_token(
            user_id=result.user.id,
            username=result.user.username
        )

        return AuthResponse(
            success=True,
            message="로그인 성공",
            access_token=token,
            expires_in=expires_in,
            user={
                "id": result.user.id,
                "username": result.user.username
            }
        )

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다."
        )
    except (UserAuthenticationError, UserPasswordError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 처리 중 오류가 발생했습니다: {str(e)}"
        )