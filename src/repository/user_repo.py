from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_model import UserModel

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[UserModel]:
    """
    user_id로 사용자 조회.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    return result.scalar_one_or_none()
    
async def get_user_by_email(session: AsyncSession, email: str) -> Optional[UserModel]:
    """
    email로 사용자 조회.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.email == email)
    )
    return result.scalar_one_or_none()
    
async def create_user(session: AsyncSession, user: UserModel) -> UserModel:
    """
    새 사용자 생성.
    """
    session.add(user)
    await session.flush()
    return user
    