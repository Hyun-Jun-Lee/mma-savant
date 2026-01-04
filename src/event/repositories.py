from datetime import date
from typing import Optional, List
from typing_extensions import Literal

from sqlalchemy import select, extract
from sqlalchemy.ext.asyncio import AsyncSession

from event.models import EventModel, EventSchema

async def get_event_by_id(session: AsyncSession, event_id: int) -> Optional[EventSchema]:
    result = await session.execute(
        select(EventModel)
        .where(EventModel.id == event_id)
    )
    event = result.scalar_one_or_none()
    return event.to_schema() if event else None

async def get_events(
    session: AsyncSession, 
    limit: int = None, 
    order_by: Literal["asc", "desc"] = "desc",
    sort_by: Literal["event_date"] = "event_date"
) -> List[EventSchema]:
    """
    이벤트 목록을 조회합니다. 정렬 순서와 제한 수를 지정할 수 있습니다.
    """
    stmt = select(EventModel)
    if sort_by == "event_date":
        if order_by == "asc":
            stmt = stmt.order_by(EventModel.event_date.asc())
        else:
            stmt = stmt.order_by(EventModel.event_date.desc())
    
    if limit:
        stmt = stmt.limit(limit)
    
    result = await session.execute(stmt)
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def get_event_by_name(session: AsyncSession, name: str) -> Optional[EventSchema]:
    """
    이름에 특정 문자열이 포함된 이벤트를 검색합니다. 대소문자를 구분하지 않습니다.
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.name.ilike(f"%{name}%"))
    )
    event = result.scalar_one_or_none()
    return event.to_schema() if event else None

async def get_events_by_period(
    session: AsyncSession,
    year: int,
    month: Optional[int] = None,
    day: Optional[int] = None,
    direction: Literal["before", "after", "on"] = "on"
) -> List[EventSchema]:
    """
    기간별 이벤트 조회.
    - year만: 해당 연도 전체 이벤트
    - year + month: 해당 월 이벤트
    - year + month + day: 특정 날짜 기준 (direction으로 before/after/on 선택)
    """
    stmt = select(EventModel)

    if day is not None and month is not None:
        target_date = date(year, month, day)
        if direction == "before":
            stmt = stmt.where(EventModel.event_date < target_date).order_by(EventModel.event_date.desc())
        elif direction == "after":
            stmt = stmt.where(EventModel.event_date > target_date).order_by(EventModel.event_date.asc())
        else:  # "on"
            stmt = stmt.where(EventModel.event_date == target_date).order_by(EventModel.event_date.asc())
    elif month is not None:
        stmt = stmt.where(
            extract("year", EventModel.event_date) == year,
            extract("month", EventModel.event_date) == month
        ).order_by(EventModel.event_date.asc())
    else:
        stmt = stmt.where(
            extract("year", EventModel.event_date) == year
        ).order_by(EventModel.event_date.asc())

    result = await session.execute(stmt)
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def get_recent_events(session: AsyncSession, limit: int = 5) -> List[EventSchema]:
    """
    최근 개최된 이벤트들을 조회합니다. (과거 이벤트)
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.event_date <= date.today())
        .order_by(EventModel.event_date.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def get_upcoming_events(session: AsyncSession, limit: int = 5) -> List[EventSchema]:
    """
    다가오는 이벤트들을 조회합니다. (미래 이벤트)
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.event_date > date.today())
        .order_by(EventModel.event_date.asc())
        .limit(limit)
    )
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def get_events_by_location(session: AsyncSession, location: str) -> List[EventSchema]:
    """
    특정 장소에서 개최된 이벤트들을 조회합니다. (부분 매칭)
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.location.ilike(f"%{location}%"))
        .order_by(EventModel.event_date.desc())
    )
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def search_events_by_name(session: AsyncSession, search_term: str, limit: int = 10) -> List[EventSchema]:
    """
    이벤트 이름으로 검색합니다. (부분 매칭, 대소문자 무시)
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.name.ilike(f"%{search_term}%"))
        .order_by(EventModel.event_date.desc())
        .limit(limit)
    )
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def get_events_date_range(
    session: AsyncSession, 
    start_date: date, 
    end_date: date
) -> List[EventSchema]:
    """
    특정 날짜 범위에 개최된 이벤트들을 조회합니다.
    """
    result = await session.execute(
        select(EventModel)
        .where(
            EventModel.event_date >= start_date,
            EventModel.event_date <= end_date
        )
        .order_by(EventModel.event_date.asc())
    )
    events = result.scalars().all()
    return [event.to_schema() for event in events]