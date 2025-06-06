from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user.models import UserModel, UserSchema

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[UserSchema]:
    """
    user_id로 사용자 조회.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()
    return user.to_schema() if user else None
    
async def get_user_by_email(session: AsyncSession, email: str) -> Optional[UserSchema]:
    """
    email로 사용자 조회.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.email == email)
    )
    user = result.scalar_one_or_none()
    return user.to_schema() if user else None
    
async def create_user(session: AsyncSession, user: UserSchema) -> UserSchema:
    """
    새 사용자 생성.
    """
    db_user = UserModel.from_schema(user)
    session.add(db_user)
    await session.flush()
    return db_user.to_schema()
    