from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import get_database_url

DATABASE_URL = get_database_url()

# 비동기 엔진
async_engine = create_async_engine(
    DATABASE_URL, pool_size=20, max_overflow=40
)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, autocommit=False, autoflush=False
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
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()