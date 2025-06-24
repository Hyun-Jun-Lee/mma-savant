from typing import List, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc

from fighter.models import FighterModel, FighterSchema
from match.models import BasicMatchStatModel, FighterMatchModel, SigStrMatchStatModel

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