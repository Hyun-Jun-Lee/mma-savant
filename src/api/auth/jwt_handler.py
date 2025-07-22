"""
JWT 토큰 처리 및 NextAuth.js 연동
"""
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from pydantic import BaseModel

from config import Config


class TokenData(BaseModel):
    """JWT 토큰에서 추출한 사용자 정보"""
    sub: str  # user id or email
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    iat: Optional[int] = None
    exp: Optional[int] = None


class JWTHandler:
    """JWT 토큰 처리 클래스"""
    
    def __init__(self):
        # NextAuth.js와 동일한 SECRET 사용
        self.secret_key = Config.NEXTAUTH_SECRET
        if not self.secret_key:
            raise ValueError("NEXTAUTH_SECRET environment variable not set")
        
        
        self.algorithm = Config.TOKEN_ALGORITHM
        self.access_token_expire_minutes = Config.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def decode_token(self, token: str) -> TokenData:
        """
        JWT 토큰을 디코딩하여 사용자 정보 추출
        NextAuth.js에서 생성된 토큰과 호환
        """
        try:
            # Bearer 접두사 제거
            if token.startswith("Bearer "):
                token = token[7:]
            
            # JWT 토큰 디코딩
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # NextAuth.js 토큰 구조에 맞춰 데이터 추출
            token_data = TokenData(
                sub=payload.get("sub"),
                email=payload.get("email"),
                name=payload.get("name"), 
                picture=payload.get("picture"),
                iat=payload.get("iat"),
                exp=payload.get("exp")
            )
            
            return token_data
            
        except jwt.ExpiredSignatureError as e:
            print(f"❌ Token expired: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError as e:
            print(f"❌ JWT validation error: {e}")
            print(f"❌ Token that failed: {token[:50]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        액세스 토큰 생성 (필요시 사용)
        NextAuth.js가 주로 토큰을 생성하므로 백업용
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token_expiry(self, token_data: TokenData) -> bool:
        """토큰 만료 시간 확인"""
        if not token_data.exp:
            return False
        
        current_time = datetime.now(timezone.utc).timestamp()
        return current_time < token_data.exp


# 글로벌 JWT 핸들러 인스턴스
jwt_handler = JWTHandler()