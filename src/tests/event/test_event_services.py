"""
Event Services 테스트
"""
import pytest
from unittest.mock import patch
from datetime import date

from event import services as event_service
from event.dto import (
    EventListDTO, EventSearchDTO, EventSearchResultDTO,
    MonthlyCalendarDTO, YearlyCalendarDTO
)
from event.exceptions import EventValidationError, EventDateError, EventQueryError


# =============================================================================
# get_events 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_events_default_pagination(multiple_events_different_dates, clean_test_session):
    """기본 페이지네이션으로 이벤트 목록 조회"""
    result = await event_service.get_events(clean_test_session)

    assert isinstance(result, EventListDTO)
    assert result.page == 1
    assert result.limit == 10
    assert isinstance(result.events, list)
    assert isinstance(result.total, int)
    assert result.year is None
    assert result.month is None


@pytest.mark.asyncio
async def test_get_events_with_pagination(multiple_events_different_dates, clean_test_session):
    """페이지네이션 파라미터로 조회"""
    result = await event_service.get_events(clean_test_session, page=1, limit=2)

    assert result.page == 1
    assert result.limit == 2
    assert len(result.events) <= 2


@pytest.mark.asyncio
async def test_get_events_by_year(multiple_events_different_dates, clean_test_session):
    """연도별 이벤트 조회"""
    result = await event_service.get_events(clean_test_session, year=2024)

    assert result.year == 2024
    assert result.month is None
    for event in result.events:
        assert event.event_date.year == 2024


@pytest.mark.asyncio
async def test_get_events_by_year_and_month(multiple_events_different_dates, clean_test_session):
    """연도와 월로 이벤트 조회"""
    result = await event_service.get_events(clean_test_session, year=2024, month=1)

    assert result.year == 2024
    assert result.month == 1
    for event in result.events:
        assert event.event_date.year == 2024
        assert event.event_date.month == 1


@pytest.mark.asyncio
async def test_get_events_invalid_page(clean_test_session):
    """잘못된 페이지 번호"""
    with pytest.raises(EventValidationError, match="page must be a positive integer"):
        await event_service.get_events(clean_test_session, page=0)

    with pytest.raises(EventValidationError, match="page must be a positive integer"):
        await event_service.get_events(clean_test_session, page=-1)


@pytest.mark.asyncio
async def test_get_events_invalid_limit(clean_test_session):
    """잘못된 limit 값"""
    with pytest.raises(EventValidationError, match="limit must be between 1 and 100"):
        await event_service.get_events(clean_test_session, limit=0)

    with pytest.raises(EventValidationError, match="limit must be between 1 and 100"):
        await event_service.get_events(clean_test_session, limit=101)


@pytest.mark.asyncio
async def test_get_events_invalid_year(clean_test_session):
    """잘못된 연도"""
    with pytest.raises(EventDateError, match="Year must be between 1993"):
        await event_service.get_events(clean_test_session, year=1990)


@pytest.mark.asyncio
async def test_get_events_invalid_month(clean_test_session):
    """잘못된 월"""
    with pytest.raises(EventDateError, match="Month must be between 1 and 12"):
        await event_service.get_events(clean_test_session, year=2024, month=13)


@pytest.mark.asyncio
async def test_get_events_repository_error(clean_test_session):
    """Repository 에러 처리"""
    with patch('event.services.event_repo.get_events', side_effect=Exception("Database error")):
        with pytest.raises(EventQueryError, match="Event query 'get_events' failed"):
            await event_service.get_events(clean_test_session)


# =============================================================================
# search_events 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_search_events_by_name(multiple_events_different_names, clean_test_session):
    """이름으로 이벤트 검색"""
    result = await event_service.search_events(
        clean_test_session, query="UFC", search_type="name", limit=5
    )

    assert isinstance(result, EventSearchDTO)
    assert result.query == "UFC"
    assert result.search_type == "name"
    for item in result.results:
        assert isinstance(item, EventSearchResultDTO)
        assert item.match_type == "name"
        assert "UFC" in item.event.name.upper()


@pytest.mark.asyncio
async def test_search_events_by_location(events_different_locations, clean_test_session):
    """장소로 이벤트 검색"""
    result = await event_service.search_events(
        clean_test_session, query="Las Vegas", search_type="location", limit=5
    )

    assert isinstance(result, EventSearchDTO)
    for item in result.results:
        assert item.match_type == "location"
        assert "Las Vegas" in item.event.location


@pytest.mark.asyncio
async def test_search_events_all_types(multiple_events_different_names, events_different_locations, clean_test_session):
    """통합 검색"""
    result = await event_service.search_events(
        clean_test_session, query="Vegas", search_type="all", limit=10
    )

    assert isinstance(result, EventSearchDTO)
    # 관련성으로 정렬 확인
    for i in range(len(result.results) - 1):
        assert result.results[i].relevance >= result.results[i + 1].relevance


@pytest.mark.asyncio
async def test_search_events_empty_query(clean_test_session):
    """빈 검색어 처리"""
    with pytest.raises(EventValidationError, match="Search query cannot be empty"):
        await event_service.search_events(clean_test_session, query="", search_type="all")

    with pytest.raises(EventValidationError, match="Search query cannot be empty"):
        await event_service.search_events(clean_test_session, query="   ", search_type="all")


@pytest.mark.asyncio
async def test_search_events_invalid_search_type(clean_test_session):
    """잘못된 검색 타입"""
    with pytest.raises(EventValidationError, match="search_type must be"):
        await event_service.search_events(clean_test_session, query="UFC", search_type="invalid")


@pytest.mark.asyncio
async def test_search_events_invalid_limit(clean_test_session):
    """잘못된 limit 값"""
    with pytest.raises(EventValidationError, match="limit must be a positive integer"):
        await event_service.search_events(clean_test_session, query="UFC", search_type="name", limit=0)


@pytest.mark.asyncio
async def test_search_events_repository_error(clean_test_session):
    """Repository 에러 처리"""
    with patch('event.services.event_repo.search_events_by_name', side_effect=Exception("Search error")):
        with pytest.raises(EventQueryError, match="Event query 'search_events' failed"):
            await event_service.search_events(clean_test_session, query="UFC", search_type="name")


# =============================================================================
# get_events_calendar 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_events_calendar_monthly(events_for_calendar_test, clean_test_session):
    """월별 캘린더 조회"""
    result = await event_service.get_events_calendar(clean_test_session, year=2024, month=8)

    assert isinstance(result, MonthlyCalendarDTO)
    assert result.type == "monthly"
    assert result.year == 2024
    assert result.month == 8
    assert isinstance(result.total_events, int)
    assert isinstance(result.calendar, dict)


@pytest.mark.asyncio
async def test_get_events_calendar_yearly(multiple_events_different_dates, clean_test_session):
    """연도별 캘린더 조회"""
    result = await event_service.get_events_calendar(clean_test_session, year=2024)

    assert isinstance(result, YearlyCalendarDTO)
    assert result.type == "yearly"
    assert result.year == 2024
    assert isinstance(result.monthly_breakdown, dict)


@pytest.mark.asyncio
async def test_get_events_calendar_invalid_year(clean_test_session):
    """잘못된 연도로 캘린더 조회"""
    with pytest.raises(EventDateError, match="Year must be between 1993"):
        await event_service.get_events_calendar(clean_test_session, year=1990, month=1)

    current_year = date.today().year
    with pytest.raises(EventDateError, match="Year must be between 1993"):
        await event_service.get_events_calendar(clean_test_session, year=current_year + 20, month=1)


@pytest.mark.asyncio
async def test_get_events_calendar_invalid_month(clean_test_session):
    """잘못된 월로 캘린더 조회"""
    with pytest.raises(EventDateError, match="Month must be between 1 and 12"):
        await event_service.get_events_calendar(clean_test_session, year=2024, month=0)

    with pytest.raises(EventDateError, match="Month must be between 1 and 12"):
        await event_service.get_events_calendar(clean_test_session, year=2024, month=13)


@pytest.mark.asyncio
async def test_get_events_calendar_future_date(clean_test_session):
    """미래 날짜로 캘린더 조회"""
    future_year = date.today().year + 5

    with patch('event.services.event_repo.get_events_by_period', return_value=[]):
        result = await event_service.get_events_calendar(
            clean_test_session, year=future_year, month=1
        )

    assert result.type == "monthly"
    assert result.year == future_year
    assert result.total_events == 0
    assert result.calendar == {}


@pytest.mark.asyncio
async def test_get_events_calendar_repository_error(clean_test_session):
    """Repository 에러 처리"""
    with patch('event.services.event_repo.get_events_by_period', side_effect=Exception("Calendar error")):
        with pytest.raises(EventQueryError, match="Event query 'get_events_calendar' failed"):
            await event_service.get_events_calendar(clean_test_session, year=2024, month=8)
