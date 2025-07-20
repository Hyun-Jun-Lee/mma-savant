"""
Database session dependency for FastAPI
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection.postgres_conn import AsyncSessionLocal


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to provide database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()