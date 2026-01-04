"""
Test Database Connection
Repository Layer 테스트를 위한 전용 DB 연결 관리
"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from config import get_database_url

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
async def db_session_for_test():
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
    async with db_session_for_test() as session:
        # 외래키 제약조건 때문에 순서대로 삭제 (의존성 역순)
        tables_to_clean = [
            "message",           # conversation에 의존
            "conversation",      # user에 의존
            "match_statistics",
            "strike_detail",
            "fighter_match",
            "ranking",
            "match",
            "event",
            "fighter",
            '"user"'             # PostgreSQL 예약어이므로 따옴표 필요
            # weight_class는 유지 (기본 데이터)
        ]

        for table in tables_to_clean:
            try:
                await session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            except Exception:
                # 테이블이 없으면 무시 (아직 생성되지 않은 경우)
                pass

        print("Test database cleaned successfully!")

async def reset_test_db_sequences():
    """
    테스트 데이터베이스 시퀀스 리셋
    AUTO_INCREMENT ID를 1부터 다시 시작
    """
    async with db_session_for_test() as session:
        sequences_to_reset = [
            "fighter_id_seq",
            "event_id_seq",
            "match_id_seq",
            "fighter_match_id_seq",
            "ranking_id_seq",
            "strike_detail_id_seq",
            "match_statistics_id_seq",
            "user_id_seq",
            "conversation_id_seq",
            "message_id_seq"
        ]

        for seq in sequences_to_reset:
            try:
                await session.execute(text(f"SELECT setval('{seq}', 1, false)"))
            except Exception:
                # 시퀀스가 없으면 무시
                pass

        print("Test database sequences reset successfully!")


