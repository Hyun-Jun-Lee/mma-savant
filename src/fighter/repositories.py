from typing import List, Literal, Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fighter.models import FighterModel, RankingModel, FighterSchema, RankingSchema
from match.models import BasicMatchStatModel, FighterMatchModel, SigStrMatchStatModel

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

async def get_fighter_by_nickname(session: AsyncSession, nickname: str) -> Optional[FighterSchema]:
    """
    fighter_nickname로 fighter 조회.
    """
    result = await session.execute(
        select(FighterModel).where(FighterModel.nickname == nickname)
    )
    fighter = result.scalar_one_or_none()
    return fighter.to_schema() if fighter else None

async def get_ranking_by_fighter_id(session: AsyncSession, fighter_id: int) -> List[RankingSchema]:
    """
    fighter_id로 해당 선수의 모든 랭킹을 조회합니다.
    동일한 선수가 여러 체급에서 랭킹을 보유하고 있을 수 있습니다.
    """
    result = await session.execute(
        select(RankingModel).where(RankingModel.fighter_id == fighter_id)
    )
    rankings = result.scalars().all()
    return [ranking.to_schema() for ranking in rankings]

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

async def get_top_fighter_by_stat(session: AsyncSession, stat_model: Literal[BasicMatchStatModel, SigStrMatchStatModel], stat_name: str, limit:int = 10):
    """
    특정 스탯에서 상위 파이터들을 조회
    """

    stat_column = getattr(stat_model, stat_name)

    stmt = (
        select(
            FighterModel, 
            func.sum(stat_column).label("total_stat")
        )
        .join(FighterMatchModel, FighterModel.id == FighterMatchModel.fighter_id)
        .join(stat_model, stat_model.fighter_match_id == FighterMatchModel.id)
        .group_by(FighterModel.id)
        .order_by(desc("total_stat"))
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    rows = result.fetchall()
    return [{"fighter": fighter.to_schema(), "stat": total_stat} for fighter, total_stat in rows]