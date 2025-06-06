from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from event.models import EventModel, EventSchema
from match.models import MatchModel, FighterMatchModel

async def get_upcoming_fighter_match(session: AsyncSession, fighter_id: int) -> Optional[EventSchema]:
    """
    주어진 파이터의 다가오는 경기를 포함한 Event를 반환합니다.
    없다면 None 반환.
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