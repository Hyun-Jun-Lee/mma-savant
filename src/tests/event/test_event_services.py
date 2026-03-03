"""
Event Services 테스트
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from event import services as event_service
from event.dto import (
    EventListDTO, EventSearchDTO, EventSearchResultDTO,
    MonthlyCalendarDTO, YearlyCalendarDTO,
    EventDetailDTO, EventMatchDTO, EventFighterStatDTO, EventSummaryDTO,
)
from event.exceptions import (
    EventValidationError, EventDateError, EventQueryError, EventNotFoundError
)
from common.utils import utc_today

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

    current_year = utc_today().year
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
    future_year = utc_today().year + 5

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


# =============================================================================
# _parse_time_to_seconds 테스트
# =============================================================================

def test_parse_time_normal():
    """정상적인 M:SS 형식 파싱"""
    assert event_service._parse_time_to_seconds("2:45") == 165
    assert event_service._parse_time_to_seconds("5:00") == 300
    assert event_service._parse_time_to_seconds("0:30") == 30
    assert event_service._parse_time_to_seconds("15:00") == 900


def test_parse_time_edge_cases():
    """None, 빈 문자열, 잘못된 형식"""
    assert event_service._parse_time_to_seconds(None) == 0
    assert event_service._parse_time_to_seconds("") == 0
    assert event_service._parse_time_to_seconds("invalid") == 0
    assert event_service._parse_time_to_seconds("abc:def") == 0
    assert event_service._parse_time_to_seconds("   ") == 0


# =============================================================================
# _classify_method 테스트
# =============================================================================

def test_classify_method_ko_tko():
    """KO/TKO 분류"""
    assert event_service._classify_method("KO/TKO") == "ko_tko"
    assert event_service._classify_method("KO/TKO-Punch") == "ko_tko"
    assert event_service._classify_method("KO/TKO-Punches") == "ko_tko"
    assert event_service._classify_method("TKO") == "ko_tko"


def test_classify_method_submission():
    """서브미션 분류"""
    assert event_service._classify_method("Submission") == "submission"
    assert event_service._classify_method("SUB-Rear Naked Choke") == "submission"
    assert event_service._classify_method("SUB-Armbar") == "submission"
    assert event_service._classify_method("SUB-Guillotine") == "submission"


def test_classify_method_decision():
    """판정 분류"""
    assert event_service._classify_method("Decision - Unanimous") == "decision"
    assert event_service._classify_method("Decision - Split") == "decision"
    assert event_service._classify_method("Decision - Majority") == "decision"
    assert event_service._classify_method("U-DEC") == "decision"
    assert event_service._classify_method("S-DEC") == "decision"
    assert event_service._classify_method("M-DEC") == "decision"


def test_classify_method_other():
    """기타 종료 방법 분류"""
    assert event_service._classify_method("DQ") == "other"
    assert event_service._classify_method("Overturned") == "other"
    assert event_service._classify_method(None) == "other"
    assert event_service._classify_method("") == "other"


# =============================================================================
# _build_event_summary 테스트
# =============================================================================

def test_build_event_summary():
    """이벤트 요약 통계 생성"""
    # Mock match objects
    matches = []
    for method, rnd, time in [
        ("KO/TKO-Punch", 2, "3:45"),   # 525s
        ("SUB-RNC", 1, "4:30"),          # 270s
        ("Decision - Unanimous", 3, "5:00"),  # 900s
    ]:
        m = MagicMock()
        m.method = method
        m.result_round = rnd
        m.time = time
        matches.append(m)

    result = event_service._build_event_summary(matches)

    assert isinstance(result, EventSummaryDTO)
    assert result.total_bouts == 3
    assert result.ko_tko_count == 1
    assert result.submission_count == 1
    assert result.decision_count == 1
    assert result.other_count == 0
    # avg = (525 + 270 + 900) / 3 = 565.0
    assert result.avg_fight_duration_seconds == 565.0


def test_build_event_summary_empty():
    """매치가 없는 이벤트 요약"""
    result = event_service._build_event_summary([])

    assert result.total_bouts == 0
    assert result.ko_tko_count == 0
    assert result.avg_fight_duration_seconds == 0.0


def test_build_event_summary_null_time():
    """시간/라운드가 없는 매치 포함 시 평균 계산에서 제외"""
    matches = []
    # 유효한 매치
    m1 = MagicMock()
    m1.method = "KO/TKO"
    m1.result_round = 1
    m1.time = "2:00"
    matches.append(m1)

    # 시간이 없는 매치 (미래 이벤트 등)
    m2 = MagicMock()
    m2.method = None
    m2.result_round = None
    m2.time = None
    matches.append(m2)

    result = event_service._build_event_summary(matches)

    assert result.total_bouts == 2
    assert result.ko_tko_count == 1
    assert result.other_count == 1
    # m2는 duration 계산에서 제외, m1만: (0*300 + 120) = 120s
    assert result.avg_fight_duration_seconds == 120.0


# =============================================================================
# get_event_detail 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_event_detail_success(event_with_full_matches, clean_test_session):
    """이벤트 상세 정보 정상 조회"""
    data = event_with_full_matches
    event = data["event"]

    result = await event_service.get_event_detail(clean_test_session, event.id)

    assert isinstance(result, EventDetailDTO)
    assert result.event.id == event.id
    assert result.event.name == "UFC Test Detail Event"
    assert result.event.location == "Las Vegas, NV"
    assert result.event.event_date == date(2024, 6, 15)


@pytest.mark.asyncio
async def test_get_event_detail_matches_sorted_by_order_desc(event_with_full_matches, clean_test_session):
    """매치가 order 역순(메인이벤트 먼저)으로 정렬"""
    data = event_with_full_matches
    result = await event_service.get_event_detail(clean_test_session, data["event"].id)

    assert len(result.matches) == 3
    # order: 3(main), 2, 1
    assert result.matches[0].order == 3
    assert result.matches[0].is_main_event is True
    assert result.matches[1].order == 2
    assert result.matches[2].order == 1

    # 순서가 역순인지 검증
    for i in range(len(result.matches) - 1):
        assert result.matches[i].order >= result.matches[i + 1].order


@pytest.mark.asyncio
async def test_get_event_detail_match_fields(event_with_full_matches, clean_test_session):
    """매치 필드 값 검증"""
    data = event_with_full_matches
    result = await event_service.get_event_detail(clean_test_session, data["event"].id)

    main_event = result.matches[0]
    assert isinstance(main_event, EventMatchDTO)
    assert main_event.method == "KO/TKO-Punch"
    assert main_event.result_round == 2
    assert main_event.time == "3:45"
    assert main_event.weight_class == "lightweight"


@pytest.mark.asyncio
async def test_get_event_detail_fighters(event_with_full_matches, clean_test_session):
    """매치별 파이터 정보 검증"""
    data = event_with_full_matches
    result = await event_service.get_event_detail(clean_test_session, data["event"].id)

    main_event = result.matches[0]
    assert len(main_event.fighters) == 2

    names = {f.name for f in main_event.fighters}
    assert "Fighter Alpha" in names
    assert "Fighter Beta" in names

    for f in main_event.fighters:
        assert isinstance(f, EventFighterStatDTO)
        assert f.fighter_id > 0
        assert f.result in ("win", "loss")


@pytest.mark.asyncio
async def test_get_event_detail_fighter_stats_aggregated(event_with_full_matches, clean_test_session):
    """파이터 통계가 라운드별로 합산되어 반환"""
    data = event_with_full_matches
    result = await event_service.get_event_detail(clean_test_session, data["event"].id)

    main_event = result.matches[0]  # KO/TKO match, order=3
    alpha = next(f for f in main_event.fighters if f.name == "Fighter Alpha")

    # R1(sig=20/35, td=1/2, ctrl=60, kd=0) + R2(sig=15/20, td=0/1, ctrl=40, kd=1)
    assert alpha.stats is not None
    assert alpha.stats.knockdowns == 1
    assert alpha.stats.sig_str_landed == 35
    assert alpha.stats.sig_str_attempted == 55
    assert alpha.stats.td_landed == 1
    assert alpha.stats.td_attempted == 3
    assert alpha.stats.control_time_seconds == 100


@pytest.mark.asyncio
async def test_get_event_detail_summary(event_with_full_matches, clean_test_session):
    """이벤트 요약 통계 검증"""
    data = event_with_full_matches
    result = await event_service.get_event_detail(clean_test_session, data["event"].id)

    summary = result.summary
    assert isinstance(summary, EventSummaryDTO)
    assert summary.total_bouts == 3
    assert summary.ko_tko_count == 1
    assert summary.submission_count == 1
    assert summary.decision_count == 1
    assert summary.other_count == 0
    # (525 + 270 + 900) / 3 = 565.0
    assert summary.avg_fight_duration_seconds == 565.0


@pytest.mark.asyncio
async def test_get_event_detail_weight_class_names(event_with_full_matches, clean_test_session):
    """체급명이 올바르게 반환"""
    data = event_with_full_matches
    result = await event_service.get_event_detail(clean_test_session, data["event"].id)

    wc_set = {m.weight_class for m in result.matches}
    assert "lightweight" in wc_set
    assert "welterweight" in wc_set


@pytest.mark.asyncio
async def test_get_event_detail_not_found(clean_test_session):
    """존재하지 않는 이벤트 조회 시 EventNotFoundError"""
    with pytest.raises(EventNotFoundError, match="Event not found with id: 99999"):
        await event_service.get_event_detail(clean_test_session, 99999)


@pytest.mark.asyncio
async def test_get_event_detail_invalid_id(clean_test_session):
    """잘못된 이벤트 ID 검증"""
    with pytest.raises(EventValidationError, match="event_id must be a positive integer"):
        await event_service.get_event_detail(clean_test_session, 0)

    with pytest.raises(EventValidationError, match="event_id must be a positive integer"):
        await event_service.get_event_detail(clean_test_session, -1)


@pytest.mark.asyncio
async def test_get_event_detail_repository_error(clean_test_session):
    """Repository 에러 처리"""
    with patch('event.services.event_repo.get_event_with_matches', side_effect=Exception("DB error")):
        with pytest.raises(EventQueryError, match="Event query 'get_event_detail' failed"):
            await event_service.get_event_detail(clean_test_session, 1)
