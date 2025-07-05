"""
Test Database Connection
Repository Layer 테스트를 위한 전용 DB 연결 관리
"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from config import get_database_url
import logging.config

# 테스트 데이터베이스 URL
TEST_DATABASE_URL = get_database_url(is_test=True)

# 테스트 전용 비동기 엔진 (연결 풀 설정 최적화)
test_async_engine = create_async_engine(
    TEST_DATABASE_URL, 
    pool_size=5,  
    max_overflow=10,
    echo=False,  
    pool_pre_ping=True,  
    pool_recycle=3600  
)

# 테스트 전용 세션 팩토리
TestAsyncSessionLocal = sessionmaker(
    test_async_engine, 
    class_=AsyncSession, 
    autocommit=False, 
    autoflush=False,
    # 테스트에서 commit 후에도 객체 사용 가능
    expire_on_commit=False  
)

@asynccontextmanager
async def test_db_session():
    """
    테스트 전용 데이터베이스 세션 컨텍스트 매니저
    각 테스트 후 자동으로 롤백하여 테스트 격리 보장
    """
    session = TestAsyncSessionLocal()
    try:
        yield session
        # 테스트 완료 후 자동 롤백 (테스트 격리)
        await session.rollback()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

@asynccontextmanager
async def test_db_session_with_commit():
    """
    커밋이 필요한 테스트용 세션 (일부 통합 테스트용)
    주의: 이 세션은 실제로 DB에 변경사항을 커밋합니다
    """
    session = TestAsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

async def cleanup_test_db():
    """
    테스트 데이터베이스 정리 함수
    모든 테이블의 데이터를 삭제하고 시퀀스 리셋
    """
    async with test_db_session_with_commit() as session:
        # 외래키 제약조건 때문에 순서대로 삭제
        tables_to_clean = [
            "match_statistics",
            "strike_detail", 
            "fighter_match",
            "ranking",
            "match",
            "event",
            "fighter"
            # weight_class는 유지 (기본 데이터)
        ]
        
        for table in tables_to_clean:
            await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        
        print("Test database cleaned successfully!")

async def reset_test_db_sequences():
    """
    테스트 데이터베이스 시퀀스 리셋
    AUTO_INCREMENT ID를 1부터 다시 시작
    """
    async with test_db_session_with_commit() as session:
        sequences_to_reset = [
            "fighter_id_seq",
            "event_id_seq", 
            "match_id_seq",
            "fighter_match_id_seq",
            "ranking_id_seq",
            "strike_detail_id_seq",
            "match_statistics_id_seq"
        ]
        
        for seq in sequences_to_reset:
            await session.execute(text(f"SELECT setval('{seq}', 1, false)"))
        
        print("Test database sequences reset successfully!")