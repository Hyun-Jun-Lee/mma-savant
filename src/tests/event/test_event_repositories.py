"""
Event Repositories 테스트
"""
import pytest
from datetime import date

from event import repositories as event_repo
from event.models import EventSchema
from common.utils import utc_today


# =============================================================================
# get_event_by_id 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_event_by_id_existing(sample_event, clean_test_session):
    """존재하는 이벤트 ID로 조회"""
    result = await event_repo.get_event_by_id(clean_test_session, sample_event.id)

    assert result is not None
    assert isinstance(result, EventSchema)
    assert result.id == sample_event.id
    assert result.name == sample_event.name


@pytest.mark.asyncio
async def test_get_event_by_id_nonexistent(clean_test_session):
    """존재하지 않는 이벤트 ID로 조회"""
    result = await event_repo.get_event_by_id(clean_test_session, 99999)

    assert result is None


# =============================================================================
# get_events 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_events_with_limit(multiple_events_different_dates, clean_test_session):
    """이벤트 목록 조회 제한"""
    result = await event_repo.get_events(clean_test_session, limit=2, order_by="desc")

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].event_date >= result[1].event_date


@pytest.mark.asyncio
async def test_get_events_ascending_order(multiple_events_different_dates, clean_test_session):
    """이벤트 목록 오름차순 조회"""
    result = await event_repo.get_events(clean_test_session, order_by="asc")

    assert isinstance(result, list)
    for i in range(len(result) - 1):
        assert result[i].event_date <= result[i + 1].event_date


# =============================================================================
# get_event_by_name 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_event_by_name_partial_match(sample_event, clean_test_session):
    """부분 이름 매칭으로 이벤트 조회"""
    result = await event_repo.get_event_by_name(clean_test_session, "UFC Test")

    assert result is not None
    assert isinstance(result, EventSchema)
    assert "UFC Test" in result.name


@pytest.mark.asyncio
async def test_get_event_by_name_case_insensitive(sample_event, clean_test_session):
    """대소문자 무시 이름 검색"""
    result = await event_repo.get_event_by_name(clean_test_session, "ufc test")

    assert result is not None
    assert result.id == sample_event.id


@pytest.mark.asyncio
async def test_get_event_by_name_no_match(clean_test_session):
    """일치하지 않는 이름으로 검색"""
    result = await event_repo.get_event_by_name(clean_test_session, "Nonexistent Event")

    assert result is None


# =============================================================================
# search_events_by_name 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_search_events_by_name(multiple_events_different_names, clean_test_session):
    """이벤트 이름 검색"""
    result = await event_repo.search_events_by_name(clean_test_session, "UFC", limit=5)

    assert isinstance(result, list)
    assert len(result) >= 1
    for event in result:
        assert "UFC" in event.name.upper()


@pytest.mark.asyncio
async def test_search_events_by_name_empty_string(clean_test_session):
    """빈 문자열로 검색"""
    result = await event_repo.search_events_by_name(clean_test_session, "", limit=5)

    assert isinstance(result, list)


# =============================================================================
# get_events_by_period 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_events_by_period_year_only(multiple_events_different_dates, clean_test_session):
    """연도별 이벤트 조회"""
    result = await event_repo.get_events_by_period(clean_test_session, 2024)

    assert isinstance(result, list)
    assert len(result) >= 1
    for event in result:
        assert event.event_date.year == 2024

    # 날짜 오름차순 정렬 확인
    for i in range(len(result) - 1):
        assert result[i].event_date <= result[i + 1].event_date


@pytest.mark.asyncio
async def test_get_events_by_period_year_month(multiple_events_different_dates, clean_test_session):
    """월별 이벤트 조회"""
    result = await event_repo.get_events_by_period(clean_test_session, 2024, 1)

    assert isinstance(result, list)
    for event in result:
        assert event.event_date.year == 2024
        assert event.event_date.month == 1


@pytest.mark.asyncio
async def test_get_events_by_period_exact_date(sample_event, clean_test_session):
    """특정 날짜의 이벤트 조회"""
    result = await event_repo.get_events_by_period(
        clean_test_session,
        sample_event.event_date.year,
        sample_event.event_date.month,
        sample_event.event_date.day,
        direction="on"
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    assert sample_event.id in [e.id for e in result]


@pytest.mark.asyncio
async def test_get_events_by_period_before(multiple_events_different_dates, clean_test_session):
    """특정 날짜 이전 이벤트 조회"""
    target_date = date(2024, 6, 1)
    result = await event_repo.get_events_by_period(
        clean_test_session, target_date.year, target_date.month, target_date.day, direction="before"
    )

    assert isinstance(result, list)
    for event in result:
        assert event.event_date < target_date


@pytest.mark.asyncio
async def test_get_events_by_period_after(multiple_events_different_dates, clean_test_session):
    """특정 날짜 이후 이벤트 조회"""
    target_date = date(2024, 1, 1)
    result = await event_repo.get_events_by_period(
        clean_test_session, target_date.year, target_date.month, target_date.day, direction="after"
    )

    assert isinstance(result, list)
    for event in result:
        assert event.event_date > target_date


@pytest.mark.asyncio
async def test_get_events_by_period_invalid_year(clean_test_session):
    """잘못된 연도로 조회"""
    result = await event_repo.get_events_by_period(clean_test_session, -1)

    assert isinstance(result, list)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_events_by_period_invalid_month(clean_test_session):
    """잘못된 월로 조회"""
    result = await event_repo.get_events_by_period(clean_test_session, 2024, 13)

    assert isinstance(result, list)
    assert len(result) == 0


# =============================================================================
# get_recent_events / get_upcoming_events 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_recent_events(events_past_and_future, clean_test_session):
    """최근 개최된 이벤트 조회"""
    result = await event_repo.get_recent_events(clean_test_session, limit=3)

    assert isinstance(result, list)
    assert len(result) <= 3
    for event in result:
        assert event.event_date <= utc_today()

    # 날짜 역순 정렬 확인
    for i in range(len(result) - 1):
        assert result[i].event_date >= result[i + 1].event_date


@pytest.mark.asyncio
async def test_get_upcoming_events(events_past_and_future, clean_test_session):
    """다가오는 이벤트 조회"""
    result = await event_repo.get_upcoming_events(clean_test_session, limit=3)

    assert isinstance(result, list)
    assert len(result) <= 3
    for event in result:
        assert event.event_date > utc_today()

    # 날짜 오름차순 정렬 확인
    for i in range(len(result) - 1):
        assert result[i].event_date <= result[i + 1].event_date


# =============================================================================
# get_events_by_location 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_events_by_location(events_different_locations, clean_test_session):
    """장소별 이벤트 조회"""
    result = await event_repo.get_events_by_location(clean_test_session, "Las Vegas")

    assert isinstance(result, list)
    assert len(result) >= 1
    for event in result:
        assert "Las Vegas" in event.location


# =============================================================================
# get_events_date_range 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_events_date_range(multiple_events_different_dates, clean_test_session):
    """날짜 범위별 이벤트 조회"""
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)

    result = await event_repo.get_events_date_range(clean_test_session, start_date, end_date)

    assert isinstance(result, list)
    for event in result:
        assert start_date <= event.event_date <= end_date

    # 날짜 오름차순 정렬 확인
    for i in range(len(result) - 1):
        assert result[i].event_date <= result[i + 1].event_date


@pytest.mark.asyncio
async def test_get_events_date_range_invalid_range(clean_test_session):
    """잘못된 날짜 범위로 조회"""
    start_date = date(2024, 12, 31)
    end_date = date(2024, 1, 1)

    result = await event_repo.get_events_date_range(clean_test_session, start_date, end_date)

    assert isinstance(result, list)
    assert len(result) == 0
