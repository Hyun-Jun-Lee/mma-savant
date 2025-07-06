from typing import List, Literal, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc
from datetime import date

from fighter.models import FighterModel, FighterSchema
from event.models import EventModel, EventSchema
from match.models import BasicMatchStatModel, FighterMatchModel, MatchModel, SigStrMatchStatModel

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

async def get_upcoming_fighter_match(session: AsyncSession, fighter_id: int) -> Optional[EventSchema]:
    """
    특정 파이터의 다가오는 경기(오늘 이후)가 포함된 가장 가까운 이벤트를 조회합니다.
    """
    result = await session.execute(
        select(EventModel)
        .join(EventModel.matches)
        .join(MatchModel.fighter_matches)
        .where(
            FighterMatchModel.fighter_id == fighter_id,
            EventModel.event_date > date.today()
        )
        .order_by(EventModel.event_date.asc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    return event.to_schema() if event else None