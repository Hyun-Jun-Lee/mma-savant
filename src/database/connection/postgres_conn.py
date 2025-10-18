from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

from config import get_database_url, Config

DATABASE_URL = get_database_url()

# 비동기 엔진
async_engine = create_async_engine(
    DATABASE_URL, pool_size=20, max_overflow=40
)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, autocommit=False, autoflush=False
)

# 동기 엔진 (LangChain Tools용)
# asyncpg URL을 psycopg2 URL로 변환
sync_database_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
sync_engine = create_engine(
    sync_database_url, pool_size=20, max_overflow=40
)
SyncSessionLocal = sessionmaker(
    sync_engine, class_=Session, autocommit=False, autoflush=False
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI routes
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session context manager for direct usage in tools
    """
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

def get_sync_db() -> Generator[Session, None, None]:
    """
    Database session dependency for synchronous usage
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

@contextmanager
def get_sync_db_context() -> Generator[Session, None, None]:
    """
    Database session context manager for synchronous tools (LangChain compatible)
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# ===== 읽기 전용 데이터베이스 연결 =====
def get_readonly_database_url():
    """
    읽기 전용 데이터베이스 URL 생성
    Two-Phase System의 Phase 1에서 안전한 쿼리 실행용
    """
    # Config에서 환경변수 가져오기 - 하드코딩 제거
    readonly_user = Config.DB_READONLY_USER
    readonly_password = Config.DB_READONLY_PASSWORD

    # DB_READONLY_PASSWORD가 설정되지 않은 경우 경고 후 기본값 사용
    if not readonly_password:
        import warnings
        warnings.warn(
            "DB_READONLY_PASSWORD is not set in environment variables. "
            "Please set it for production use. Using temporary default.",
            UserWarning
        )
        # 개발 환경용 임시 값 (프로덕션에서는 반드시 환경변수 설정 필요)
        readonly_password = "temp_readonly_pass"

    host = Config.DB_HOST
    port = Config.DB_PORT
    db_name = Config.DB_NAME

    return f"postgresql://{readonly_user}:{readonly_password}@{host}:{port}/{db_name}"

# 읽기 전용 동기 엔진
readonly_engine = create_engine(
    get_readonly_database_url(),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # 연결 상태 자동 체크
)

ReadonlySessionLocal = sessionmaker(
    readonly_engine,
    class_=Session,
    autocommit=False,
    autoflush=False
)

@contextmanager
def get_readonly_db_context() -> Generator[Session, None, None]:
    """
    읽기 전용 데이터베이스 세션 (SELECT만 가능)
    Two-Phase System Phase 1의 안전한 SQL 실행용
    """
    session = ReadonlySessionLocal()
    try:
        yield session
        # 읽기 전용이므로 commit 불필요
    except Exception as e:
        # 읽기 작업이므로 rollback도 실질적으로 불필요하지만 안전을 위해 유지
        session.rollback()
        raise e
    finally:
        session.close()