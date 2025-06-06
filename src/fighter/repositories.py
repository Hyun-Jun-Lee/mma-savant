from typing import List, Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fighter.models import FighterModel, RankingModel, FighterSchema, RankingSchema
from match.models import FighterMatchModel

async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> Optional[FighterSchema]:
    """
    fighter_id로 fighter 조회.
    """
    result = await session.execute(
        select(FighterModel).where(FighterModel.id == fighter_id)
    )
    fighter = result.scalar_one_or_none()
    return fighter.to_schema() if fighter else None

async def get_fighter_by_name(session: AsyncSession, name: str) -> Optional[FighterSchema]:
    """
    fighter_name로 fighter 조회.
    """
    result = await session.execute(
        select(FighterModel).where(FighterModel.name == name)
    )
    fighter = result.scalar_one_or_none()
    return fighter.to_schema() if fighter else None

async def get_ranking_by_fighter_id(session: AsyncSession, fighter_id: int) -> Optional[RankingSchema]:
    """
    fighter_id로 ranking 조회.
    """
    result = await session.execute(
        select(RankingModel).where(RankingModel.fighter_id == fighter_id)
    )
    ranking = result.scalar_one_or_none()
    return ranking.to_schema() if ranking else None

async def get_fighters_by_weight_class_ranking(session: AsyncSession, weight_class_id: int) -> List[Dict[int,FighterSchema]]:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    result = await session.execute(
        select(FighterModel, RankingModel.ranking)
        .join(RankingModel, FighterModel.id == RankingModel.fighter_id)
        .where(RankingModel.weight_class_id == weight_class_id)
        .order_by(RankingModel.ranking)
    )
    rows = result.all()
    ranking_dict = [{ranking: fighter.to_schema()} for fighter, ranking in rows]
    return ranking_dict

async def get_all_opponents(session: AsyncSession, fighter_id: int) -> List[FighterSchema]:
    subq = (
        select(FighterMatchModel.match_id)
        .where(FighterMatchModel.fighter_id == fighter_id)
        .subquery()
    )

    result = await session.execute(
        select(FighterModel)
        .join(FighterMatchModel)
        .where(
            FighterMatchModel.match_id.in_(subq),
            FighterModel.id != fighter_id
        )
    )

    fighters = result.scalars().all()
    return [fighter.to_schema() for fighter in fighters]