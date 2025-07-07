from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from calendar import monthrange

from sqlalchemy.ext.asyncio import AsyncSession

from event import repositories as event_repo
from event.dto import (
    EventTimelineDTO, EventSummaryDTO, EventStatsDTO, EventSearchDTO, EventSearchResultDTO,
    MonthlyCalendarDTO, YearlyCalendarDTO, MonthlyBreakdownDTO, LocationStatisticsDTO,
    EventRecommendationsDTO, NextAndLastEventsDTO, EventTrendsDTO
)


async def get_event_timeline(session: AsyncSession, period: str = "month") -> EventTimelineDTO:
    """
    이벤트 타임라인을 생성합니다. (지난달, 이번달, 다음달 또는 지난해, 올해, 내년)
    """
    today = date.today()
    
    if period == "month":
        # 이번 달
        current_events = await event_repo.get_events_by_month(session, today.year, today.month)
        
        # 지난 달
        if today.month == 1:
            last_month_events = await event_repo.get_events_by_month(session, today.year - 1, 12)
        else:
            last_month_events = await event_repo.get_events_by_month(session, today.year, today.month - 1)
        
        # 다음 달
        if today.month == 12:
            next_month_events = await event_repo.get_events_by_month(session, today.year + 1, 1)
        else:
            next_month_events = await event_repo.get_events_by_month(session, today.year, today.month + 1)
        
        return EventTimelineDTO(
            period="monthly",
            current_period=f"{today.year}-{today.month:02d}",
            previous_events=last_month_events,
            current_events=current_events,
            upcoming_events=next_month_events
        )
    
    elif period == "year":
        # 올해
        current_events = await event_repo.get_events_by_year(session, today.year)
        
        # 작년
        last_year_events = await event_repo.get_events_by_year(session, today.year - 1)
        
        # 내년
        next_year_events = await event_repo.get_events_by_year(session, today.year + 1)
        
        return EventTimelineDTO(
            period="yearly",
            current_period=str(today.year),
            previous_events=last_year_events,
            current_events=current_events,
            upcoming_events=next_year_events
        )
    
    else:
        raise ValueError("period must be 'month' or 'year'")


async def get_event_summary(session: AsyncSession, event_id: int) -> Optional[EventSummaryDTO]:
    """
    이벤트의 기본 정보와 매치 수, 참여 파이터 수 등의 요약 정보를 제공합니다.
    """
    from match import repositories as match_repo
    from composition import repositories as comp_repo
    
    # 이벤트 기본 정보 조회
    event = await event_repo.get_event_by_id(session, event_id)
    if not event:
        return None
    
    # 해당 이벤트의 매치들 조회
    matches = await match_repo.get_matches_by_event_id(session, event_id)
    
    # 매치 통계 계산
    total_matches = len(matches)
    main_events = [m for m in matches if m.is_main_event]
    
    # 결승 방식 통계
    finish_methods = {}
    for match in matches:
        method = match.method
        if method:
            finish_methods[method] = finish_methods.get(method, 0) + 1
    
    return EventSummaryDTO(
        event=event,
        stats=EventStatsDTO(
            total_matches=total_matches,
            main_events=len(main_events),
            finish_methods=finish_methods
        )
    )


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


async def get_events_calendar(
    session: AsyncSession, 
    year: int, 
    month: Optional[int] = None
) -> MonthlyCalendarDTO | YearlyCalendarDTO:
    """
    특정 연도/월의 이벤트 캘린더를 생성합니다.
    """
    if month is not None:
        events = await event_repo.get_events_by_month(session, year, month)
        
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
        events = await event_repo.get_events_by_year(session, year)
        
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
                month: MonthlyBreakdownDTO(
                    count=len(events),
                    events=events
                ) for month, events in monthly_data.items()
            }
        )


async def get_location_statistics(session: AsyncSession) -> LocationStatisticsDTO:
    """
    장소별 이벤트 개최 통계를 제공합니다.
    """
    # 주요 MMA 개최지들
    major_locations = [
        "Las Vegas", "New York", "London", "Paris", "Abu Dhabi", 
        "Miami", "Chicago", "Boston", "Los Angeles", "Toronto"
    ]
    
    location_stats = {}
    total_counted = 0
    
    for location in major_locations:
        count = await event_repo.get_event_count_by_location(session, location)
        if count > 0:
            location_stats[location] = count
            total_counted += count
    
    # 전체 이벤트 수 계산 (올해 기준)
    current_year = date.today().year
    total_this_year = await event_repo.get_event_count_by_year(session, current_year)
    
    return LocationStatisticsDTO(
        location_breakdown=location_stats,
        total_major_locations=total_counted,
        total_events_this_year=total_this_year,
        other_locations=max(0, total_this_year - total_counted)
    )


async def get_event_recommendations(
    session: AsyncSession, 
    recommendation_type: str = "upcoming"
) -> EventRecommendationsDTO:
    """
    사용자에게 이벤트 추천을 제공합니다.
    recommendation_type: 'upcoming', 'recent', 'popular'
    """
    if recommendation_type == "upcoming":
        events = await event_repo.get_upcoming_events(session, limit=5)
        return EventRecommendationsDTO(
            type="upcoming",
            title="다가오는 추천 이벤트",
            events=events,
            description="곧 개최될 흥미진진한 MMA 이벤트들"
        )
    
    elif recommendation_type == "recent":
        events = await event_repo.get_recent_events(session, limit=5)
        return EventRecommendationsDTO(
            type="recent",
            title="최근 개최된 이벤트",
            events=events,
            description="놓치셨을 수도 있는 최근 이벤트들"
        )
    
    elif recommendation_type == "popular":
        # 인기 이벤트는 메인 이벤트가 많은 이벤트로 정의
        # 이 부분은 composition에서 처리하는 것이 맞을 수 있음
        events = await event_repo.get_recent_events(session, limit=10)
        return EventRecommendationsDTO(
            type="popular",
            title="인기 이벤트",
            events=events[:5],  # 임시로 최근 이벤트 중 일부
            description="팬들이 주목하는 인기 이벤트들"
        )
    
    else:
        raise ValueError("recommendation_type must be 'upcoming', 'recent', or 'popular'")


async def get_next_and_last_events(session: AsyncSession) -> NextAndLastEventsDTO:
    """
    가장 가까운 다음 이벤트와 가장 최근 이벤트를 함께 조회합니다.
    """
    next_event = await event_repo.get_next_event(session)
    last_event = await event_repo.get_last_event(session)
    
    days_until_next = None
    days_since_last = None
    
    # 다음 이벤트까지 남은 일수 계산
    if next_event and next_event.event_date:
        days_until_next = (next_event.event_date - date.today()).days
    
    # 마지막 이벤트로부터 경과 일수 계산  
    if last_event and last_event.event_date:
        days_since_last = (date.today() - last_event.event_date).days
    
    return NextAndLastEventsDTO(
        next_event=next_event,
        last_event=last_event,
        days_until_next=days_until_next,
        days_since_last=days_since_last
    )


async def get_event_trends(session: AsyncSession, period: str = "yearly") -> EventTrendsDTO:
    """
    이벤트 개최 트렌드를 분석합니다.
    """
    current_year = date.today().year
    trends = {}
    
    if period == "yearly":
        # 최근 5년간 연도별 이벤트 수
        for year in range(current_year - 4, current_year + 1):
            count = await event_repo.get_event_count_by_year(session, year)
            trends[str(year)] = count
    
    elif period == "monthly":
        # 올해 월별 이벤트 수
        for month in range(1, 13):
            events = await event_repo.get_events_by_month(session, current_year, month)
            trends[f"{current_year}-{month:02d}"] = len(events)
    
    return EventTrendsDTO(
        period=period,
        trends=trends,
        total=sum(trends.values()),
        average=sum(trends.values()) / len(trends) if trends else 0
    )