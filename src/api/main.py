"""
메인 API 라우터
모든 API 엔드포인트를 통합하여 관리
"""
from fastapi import APIRouter
from api.auth.routes import router as auth_router
from api.user.routes import router as user_router
from api.chat.routes import router as chat_router
from api.websocket.routes import router as websocket_router

# 메인 API 라우터
api_router = APIRouter()

# 인증 API 등록
api_router.include_router(auth_router)

# 사용자 관리 API 등록
api_router.include_router(user_router)

# 채팅 세션 관리 API 등록
api_router.include_router(chat_router)

# WebSocket API 등록
api_router.include_router(websocket_router)