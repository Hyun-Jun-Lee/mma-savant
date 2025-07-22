"""
인증 관련 API 라우터
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


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