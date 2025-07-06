from datetime import date
from typing import Optional, List
from typing_extensions import Literal

from sqlalchemy import select, extract, func
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

async def get_events_by_year(
    session: AsyncSession, year: int
) -> List[EventSchema]:
    """
    특정 연도에 개최된 모든 이벤트를 날짜순으로 조회합니다.
    """
    result = await session.execute(
        select(EventModel)
        .where(extract("year", EventModel.event_date) == year)
        .order_by(EventModel.event_date.asc())
    )
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def get_events_by_month(
    session: AsyncSession, year: int, month: int
) -> List[EventSchema]:
    """
    특정 연도와 월에 개최된 모든 이벤트를 날짜순으로 조회합니다.
    """
    result = await session.execute(
        select(EventModel)
        .where(
            extract("year", EventModel.event_date) == year,
            extract("month", EventModel.event_date) == month
        )
        .order_by(EventModel.event_date.asc())
    )
    events = result.scalars().all()
    return [event.to_schema() for event in events]

async def get_events_by_date(
    session: AsyncSession,
    date: date,
    direction: Literal["before", "after", "on"] = "on"
) -> List[EventSchema]:
    """
    특정 날짜를 기준으로 이벤트를 조회합니다.
    'on'은 해당 날짜의 이벤트, 'before'는 이전 이벤트, 'after'는 이후 이벤트를 반환합니다.
    """
    stmt = select(EventModel)

    if direction == "before":
        stmt = stmt.where(EventModel.event_date < date).order_by(EventModel.event_date.desc())
    elif direction == "after":
        stmt = stmt.where(EventModel.event_date > date).order_by(EventModel.event_date.asc())
    else:  # "on"
        stmt = stmt.where(EventModel.event_date == date)

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

async def get_event_by_exact_name(session: AsyncSession, name: str) -> Optional[EventSchema]:
    """
    정확한 이벤트 이름으로 조회합니다. (대소문자 무시)
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.name.ilike(name))
    )
    event = result.scalar_one_or_none()
    return event.to_schema() if event else None

async def get_next_event(session: AsyncSession) -> Optional[EventSchema]:
    """
    가장 가까운 다음 이벤트를 조회합니다.
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.event_date > date.today())
        .order_by(EventModel.event_date.asc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    return event.to_schema() if event else None

async def get_last_event(session: AsyncSession) -> Optional[EventSchema]:
    """
    가장 최근에 개최된 이벤트를 조회합니다.
    """
    result = await session.execute(
        select(EventModel)
        .where(EventModel.event_date <= date.today())
        .order_by(EventModel.event_date.desc())
        .limit(1)
    )
    event = result.scalar_one_or_none()
    return event.to_schema() if event else None

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

async def get_event_count_by_year(session: AsyncSession, year: int) -> int:
    """
    특정 연도에 개최된 이벤트 개수를 반환합니다.
    """
    result = await session.execute(
        select(func.count(EventModel.id))
        .where(extract("year", EventModel.event_date) == year)
    )
    return result.scalar() or 0

async def get_event_count_by_location(session: AsyncSession, location: str) -> int:
    """
    특정 장소에서 개최된 이벤트 개수를 반환합니다.
    """
    result = await session.execute(
        select(func.count(EventModel.id))
        .where(EventModel.location.ilike(f"%{location}%"))
    )
    return result.scalar() or 0

