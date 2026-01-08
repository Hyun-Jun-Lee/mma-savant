from datetime import date
from typing import Optional, List
from calendar import monthrange

from sqlalchemy.ext.asyncio import AsyncSession

from event import repositories as event_repo
from event.dto import (
    EventListDTO, EventSearchDTO, EventSearchResultDTO,
    MonthlyCalendarDTO, YearlyCalendarDTO, MonthlyBreakdownDTO
)
from event.exceptions import (
    EventValidationError, EventDateError, EventQueryError
)
from common.utils import utc_today


async def get_events(
    session: AsyncSession,
    page: int = 1,
    limit: int = 10,
    year: Optional[int] = None,
    month: Optional[int] = None
    ) -> EventListDTO:
    """
    이벤트 목록을 조회합니다. 페이지네이션과 연도/월 필터링을 지원합니다.
    """
    if page < 1:
        raise EventValidationError("page", page, "page must be a positive integer")
    if limit < 1 or limit > 100:
        raise EventValidationError("limit", limit, "limit must be between 1 and 100")

    current_year = utc_today().year
    if year is not None and (year < 1993 or year > current_year + 10):
        raise EventDateError(year, f"Year must be between 1993 and {current_year + 10}")
    if month is not None and (month < 1 or month > 12):
        raise EventDateError(month, "Month must be between 1 and 12")

    try:
        if year is not None:
            all_events = await event_repo.get_events_by_period(session, year, month)
        else:
            all_events = await event_repo.get_events(session, order_by="desc")

        total = len(all_events)
        start = (page - 1) * limit
        end = start + limit
        paginated_events = all_events[start:end]

        return EventListDTO(
            events=paginated_events,
            total=total,
            page=page,
            limit=limit,
            year=year,
            month=month
        )

    except (EventValidationError, EventDateError):
        raise
    except Exception as e:
        raise EventQueryError("get_events", {"page": page, "limit": limit, "year": year, "month": month}, str(e))


async def search_events(
        session: AsyncSession, 
        query: str, 
        search_type: str = "name",
        limit: int = 10
    ) -> EventSearchDTO:
    """
    다양한 기준으로 이벤트를 검색합니다.
    search_type: 'name', 'location', 'all'
    """
    # 입력 검증
    if not query or not query.strip():
        raise EventValidationError("query", query, "Search query cannot be empty")
    
    if search_type not in ["name", "location", "all"]:
        raise EventValidationError("search_type", search_type, "search_type must be 'name', 'location', or 'all'")
    
    if not isinstance(limit, int) or limit <= 0:
        raise EventValidationError("limit", limit, "limit must be a positive integer")
    
    try:
        results = []
        
        if search_type in ["name", "all"]:
            name_results = await event_repo.search_events_by_name(session, query, limit)
            for event in name_results:
                results.append(EventSearchResultDTO(
                    event=event,
                    match_type="name",
                    relevance=1.0 if query.lower() in event.name.lower() else 0.5
                ))
        
        if search_type in ["location", "all"]:
            location_results = await event_repo.get_events_by_location(session, query)
            for event in location_results:
                if not any(r.event.id == event.id for r in results):  # 중복 제거
                    results.append(EventSearchResultDTO(
                        event=event,
                        match_type="location",
                        relevance=1.0 if query.lower() in event.location.lower() else 0.5
                    ))
        
        # 관련성으로 정렬
        results.sort(key=lambda x: x.relevance, reverse=True)
        final_results = results[:limit]
        
        return EventSearchDTO(
            results=final_results,
            total=len(final_results),
            query=query,
            search_type=search_type
        )
    
    except EventValidationError:
        raise
    except Exception as e:
        raise EventQueryError("search_events", {"query": query, "search_type": search_type, "limit": limit}, str(e))


async def get_events_calendar(
        session: AsyncSession, 
        year: int, 
        month: Optional[int] = None
    ) -> MonthlyCalendarDTO | YearlyCalendarDTO:
    """
    특정 연도/월의 이벤트 캘린더를 생성합니다.
    """
    # 연도 검증
    current_year = utc_today().year
    if not isinstance(year, int) or year < 1993 or year > current_year + 10:  # UFC는 1993년 시작
        raise EventDateError(year, f"Year must be between 1993 and {current_year + 10}")
    
    # 월 검증 (제공된 경우)
    if month is not None and (not isinstance(month, int) or month < 1 or month > 12):
        raise EventDateError(month, "Month must be between 1 and 12")
    
    try:
        if month is not None:
            events = await event_repo.get_events_by_period(session, year, month)
            
            # 월별 캘린더 생성
            _, days_in_month = monthrange(year, month)
            calendar_data = {}
            
            for day in range(1, days_in_month + 1):
                day_date = date(year, month, day)
                day_events = [e for e in events if e.event_date == day_date]
                if day_events:
                    calendar_data[str(day)] = day_events
            
            return MonthlyCalendarDTO(
                type="monthly",
                year=year,
                month=month,
                total_events=len(events),
                calendar=calendar_data
            )
        else:
            events = await event_repo.get_events_by_period(session, year)
            
            # 연도별 월단위 그룹화
            monthly_data = {}
            for event in events:
                if event.event_date:
                    month_key = event.event_date.strftime("%m")
                    if month_key not in monthly_data:
                        monthly_data[month_key] = []
                    monthly_data[month_key].append(event)
            
            return YearlyCalendarDTO(
                type="yearly",
                year=year,
                total_events=len(events),
                monthly_breakdown={
                    month_key: MonthlyBreakdownDTO(
                        count=len(month_events),
                        events=month_events
                    ) for month_key, month_events in monthly_data.items()
                }
            )
    
    except EventDateError:
        raise
    except Exception as e:
        raise EventQueryError("get_events_calendar", {"year": year, "month": month}, str(e))