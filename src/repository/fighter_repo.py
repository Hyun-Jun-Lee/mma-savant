from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.fighter_model import FighterModel, RankingModel, FighterSchema, RankingSchema

async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> Optional[FighterModel]:
    """
    fighter_id로 fighter 조회.
    """
    result = await session.execute(
        select(FighterModel).where(FighterModel.id == fighter_id)
    )
    return result.scalar_one_or_none()

async def get_fighter_by_name(session: AsyncSession, name: str) -> Optional[FighterModel]:
    """
    fighter_name로 fighter 조회.
    """
    result = await session.execute(
        select(FighterModel).where(FighterModel.name == name)
    )
    return result.scalar_one_or_none()

async def get_ranking_by_fighter_id(session: AsyncSession, fighter_id: int) -> Optional[RankingModel]:
    """
    fighter_id로 ranking 조회.
    """
    result = await session.execute(
        select(RankingModel).where(RankingModel.fighter_id == fighter_id)
    )
    return result.scalar_one_or_none()

async def get_fighters_by_weight_class_ranking(session: AsyncSession, weight_class_id: int) -> List[FighterModel]:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    result = await session.execute(
        select(FighterModel)
        .join(RankingModel, FighterModel.id == RankingModel.fighter_id)
        .where(RankingModel.weight_class_id == weight_class_id)
        .order_by(RankingModel.ranking)
    )
    return result.scalars().all()
    
