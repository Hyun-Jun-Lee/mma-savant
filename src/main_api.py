"""
MMA Savant FastAPI 애플리케이션
백엔드 API 서버 메인 엔트리포인트
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.main import api_router
from config import Config

# 환경변수 로딩
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작시 실행
    print("🚀 MMA Savant API starting...")
    
    yield
    
    # 종료시 실행
    print("🛑 MMA Savant API shutting down...")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="MMA Savant API",
    description="종합격투기(MMA) 전문 AI 어시스턴트 백엔드 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
frontend_url = os.getenv("FRONTEND_URL", Config.CORS_ORIGINS[0])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url] + Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router)

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "MMA Savant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "websocket": "/ws/chat"
    }

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "mma-savant-api",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_api:app",
        host=Config.SERVER_HOST,
        port=Config.SERVER_PORT,
        reload=True,
        log_level="info"
    )