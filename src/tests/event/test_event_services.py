"""
Event Services 테스트
event/services.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import date, timedelta

from event import services as event_service
from event.dto import (
    EventTimelineDTO, EventSummaryDTO, EventStatsDTO, EventSearchDTO, EventSearchResultDTO,
    MonthlyCalendarDTO, YearlyCalendarDTO, MonthlyBreakdownDTO, LocationStatisticsDTO,
    EventRecommendationsDTO, NextAndLastEventsDTO, EventTrendsDTO
)
from event.exceptions import (
    EventNotFoundError, EventValidationError, EventDateError, EventLocationError,
    EventQueryError
)


class TestEventServicesWithTestDB:
    """Test DB를 사용한 Event Services 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_timeline_monthly(self, multiple_events_different_dates, clean_test_session):
        """월별 이벤트 타임라인 조회 테스트"""
        # When: 월별 타임라인 조회
        result = await event_service.get_event_timeline(clean_test_session, period="month")
        
        # Then: 월별 타임라인 데이터 반환
        assert result is not None
        assert isinstance(result, EventTimelineDTO)
        assert result.period == "monthly"
        assert result.current_period is not None
        assert isinstance(result.previous_events, list)
        assert isinstance(result.current_events, list)
        assert isinstance(result.upcoming_events, list)
    
    @pytest.mark.asyncio
    async def test_get_event_timeline_yearly(self, multiple_events_different_dates, clean_test_session):
        """연도별 이벤트 타임라인 조회 테스트"""
        # When: 연도별 타임라인 조회
        result = await event_service.get_event_timeline(clean_test_session, period="year")
        
        # Then: 연도별 타임라인 데이터 반환
        assert result is not None
        assert isinstance(result, EventTimelineDTO)
        assert result.period == "yearly"
        assert result.current_period is not None
        assert isinstance(result.previous_events, list)
        assert isinstance(result.current_events, list)
        assert isinstance(result.upcoming_events, list)
    
    @pytest.mark.asyncio
    async def test_get_event_timeline_invalid_period(self, clean_test_session):
        """잘못된 기간으로 타임라인 조회 테스트"""
        # When & Then: 잘못된 기간으로 조회시 EventValidationError 발생
        with pytest.raises(EventValidationError, match="period must be 'month' or 'year'"):
            await event_service.get_event_timeline(clean_test_session, period="invalid")
    
    @pytest.mark.asyncio
    async def test_get_event_summary_existing_event(self, sample_event, clean_test_session):
        """존재하는 이벤트의 요약 정보 조회 테스트"""
        # When: 이벤트 요약 정보 조회
        result = await event_service.get_event_summary(clean_test_session, sample_event.id)
        
        # Then: 이벤트 요약 정보 반환
        assert result is not None
        assert isinstance(result, EventSummaryDTO)
        
        # 이벤트 정보 확인
        assert result.event.id == sample_event.id
        assert result.event.name == sample_event.name
        
        # 통계 정보 확인
        assert isinstance(result.stats, EventStatsDTO)
        assert isinstance(result.stats.total_matches, int)
        assert isinstance(result.stats.main_events, int)
        assert isinstance(result.stats.finish_methods, dict)
    
    @pytest.mark.asyncio
    async def test_get_event_summary_nonexistent_event(self, clean_test_session):
        """존재하지 않는 이벤트의 요약 정보 조회 테스트"""
        # When & Then: 존재하지 않는 이벤트로 조회시 EventNotFoundError 발생
        with pytest.raises(EventNotFoundError, match="Event not found with id: 99999"):
            await event_service.get_event_summary(clean_test_session, 99999)
    
    @pytest.mark.asyncio
    async def test_search_events_by_name(self, multiple_events_different_names, clean_test_session):
        """이름으로 이벤트 검색 테스트"""
        # When: "UFC"로 검색
        result = await event_service.search_events(
            clean_test_session, query="UFC", search_type="name", limit=5
        )
        
        # Then: 검색 결과 반환
        assert isinstance(result, EventSearchDTO)
        assert result.total >= 1
        assert len(result.results) >= 1
        assert result.query == "UFC"
        assert result.search_type == "name"
        
        for item in result.results:
            assert isinstance(item, EventSearchResultDTO)
            assert item.match_type == "name"
            assert 0 <= item.relevance <= 1.0
            assert "UFC" in item.event.name.upper()
    
    @pytest.mark.asyncio
    async def test_search_events_by_location(self, events_different_locations, clean_test_session):
        """장소로 이벤트 검색 테스트"""
        # When: "Las Vegas"로 장소 검색
        result = await event_service.search_events(
            clean_test_session, query="Las Vegas", search_type="location", limit=5
        )
        
        # Then: 검색 결과 반환
        assert isinstance(result, EventSearchDTO)
        assert result.total >= 1
        assert len(result.results) >= 1
        
        for item in result.results:
            assert isinstance(item, EventSearchResultDTO)
            assert item.match_type == "location"
            assert 0 <= item.relevance <= 1.0
            assert "Las Vegas" in item.event.location
    
    @pytest.mark.asyncio
    async def test_search_events_all_types(self, multiple_events_different_names, events_different_locations, clean_test_session):
        """통합 검색 테스트"""
        # When: "UFC"로 전체 검색 (이름과 장소 모두)
        result = await event_service.search_events(
            clean_test_session, query="Vegas", search_type="all", limit=10
        )
        
        # Then: 이름과 장소 검색 결과 모두 포함
        assert isinstance(result, EventSearchDTO)
        
        # 관련성으로 정렬되어 있는지 확인
        for i in range(len(result.results) - 1):
            assert result.results[i].relevance >= result.results[i + 1].relevance
    
    @pytest.mark.asyncio
    async def test_get_events_calendar_monthly(self, events_for_calendar_test, clean_test_session):
        """월별 이벤트 캘린더 조회 테스트"""
        # When: 2024년 8월 캘린더 조회
        result = await event_service.get_events_calendar(clean_test_session, year=2024, month=8)
        
        # Then: 월별 캘린더 데이터 반환
        assert result is not None
        assert isinstance(result, MonthlyCalendarDTO)
        assert result.type == "monthly"
        assert result.year == 2024
        assert result.month == 8
        assert isinstance(result.total_events, int)
        assert isinstance(result.calendar, dict)
        
        # 특정 날짜에 이벤트가 있는지 확인
        if "1" in result.calendar:
            assert isinstance(result.calendar["1"], list)
            assert len(result.calendar["1"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_events_calendar_yearly(self, multiple_events_different_dates, clean_test_session):
        """연도별 이벤트 캘린더 조회 테스트"""
        # When: 2024년 연도별 캘린더 조회
        result = await event_service.get_events_calendar(clean_test_session, year=2024)
        
        # Then: 연도별 캘린더 데이터 반환
        assert result is not None
        # Check result type based on context
        assert result.type == "yearly"
        assert result.year == 2024
        assert hasattr(result, 'total_events')
        assert hasattr(result, 'monthly_breakdown')
        
        # 월별 분석 데이터 확인
        monthly_breakdown = result.monthly_breakdown
        assert isinstance(monthly_breakdown, dict)
        
        for month_data in monthly_breakdown.values():
            assert hasattr(month_data, 'count')
            assert hasattr(month_data, 'events')
            assert isinstance(month_data.count, int)
            assert isinstance(month_data.events, list)
    
    @pytest.mark.asyncio
    async def test_get_location_statistics(self, events_different_locations, clean_test_session):
        """장소별 통계 조회 테스트"""
        # When: 장소별 통계 조회
        result = await event_service.get_location_statistics(clean_test_session)
        
        # Then: 장소별 통계 데이터 반환
        assert result is not None
        # Check result type based on context
        assert hasattr(result, 'location_breakdown')
        assert hasattr(result, 'total_major_locations')
        assert hasattr(result, 'total_events_this_year')
        assert hasattr(result, 'other_locations')
        
        # 각 필드 타입 확인
        assert isinstance(result.location_breakdown, dict)
        assert isinstance(result.total_major_locations, int)
        assert isinstance(result.total_events_this_year, int)
        assert isinstance(result.other_locations, int)
    
    @pytest.mark.asyncio
    async def test_get_event_recommendations_upcoming(self, events_past_and_future, clean_test_session):
        """다가오는 이벤트 추천 테스트"""
        # When: 다가오는 이벤트 추천 조회
        result = await event_service.get_event_recommendations(
            clean_test_session, recommendation_type="upcoming"
        )
        
        # Then: 추천 데이터 반환
        assert result is not None
        # Check result type based on context
        assert result.type == "upcoming"
        assert hasattr(result, 'title')
        assert hasattr(result, 'events')
        assert hasattr(result, 'description')
        
        # 이벤트 리스트 확인
        assert isinstance(result.events, list)
        assert len(result.events) <= 5
    
    @pytest.mark.asyncio
    async def test_get_event_recommendations_recent(self, events_past_and_future, clean_test_session):
        """최근 이벤트 추천 테스트"""
        # When: 최근 이벤트 추천 조회
        result = await event_service.get_event_recommendations(
            clean_test_session, recommendation_type="recent"
        )
        
        # Then: 추천 데이터 반환
        assert result is not None
        assert result.type == "recent"
        assert isinstance(result.events, list)
    
    @pytest.mark.asyncio
    async def test_get_event_recommendations_popular(self, events_past_and_future, clean_test_session):
        """인기 이벤트 추천 테스트"""
        # When: 인기 이벤트 추천 조회
        result = await event_service.get_event_recommendations(
            clean_test_session, recommendation_type="popular"
        )
        
        # Then: 추천 데이터 반환
        assert result is not None
        assert result.type == "popular"
        assert isinstance(result.events, list)
    
    @pytest.mark.asyncio
    async def test_get_event_recommendations_invalid_type(self, clean_test_session):
        """잘못된 추천 타입 테스트"""
        # When & Then: 잘못된 추천 타입으로 조회시 EventValidationError 발생
        with pytest.raises(EventValidationError, match="recommendation_type must be"):
            await event_service.get_event_recommendations(
                clean_test_session, recommendation_type="invalid"
            )
    
    @pytest.mark.asyncio
    async def test_get_next_and_last_events(self, events_past_and_future, clean_test_session):
        """다음/최근 이벤트 조회 테스트"""
        # When: 다음/최근 이벤트 조회
        result = await event_service.get_next_and_last_events(clean_test_session)
        
        # Then: 다음/최근 이벤트 데이터 반환
        assert result is not None
        # Check result type based on context
        assert hasattr(result, 'next_event')
        assert hasattr(result, 'last_event')
        
        # 일수 계산 필드들 확인
        if result.next_event:
            assert hasattr(result, 'days_until_next')
            assert isinstance(result.days_until_next, int)
        
        if result.last_event:
            assert hasattr(result, 'days_since_last')
            assert isinstance(result.days_since_last, int)
    
    @pytest.mark.asyncio
    async def test_get_event_trends_yearly(self, multiple_events_different_dates, clean_test_session):
        """연도별 이벤트 트렌드 조회 테스트"""
        # When: 연도별 트렌드 조회
        result = await event_service.get_event_trends(clean_test_session, period="yearly")
        
        # Then: 트렌드 데이터 반환
        assert result is not None
        # Check result type based on context
        assert result.period == "yearly"
        assert hasattr(result, 'trends')
        assert hasattr(result, 'total')
        assert hasattr(result, 'average')
        
        # 트렌드 데이터 확인
        trends = result.trends
        assert isinstance(trends, dict)
        assert len(trends) == 5  # 최근 5년
        
        # 통계 값 확인
        assert isinstance(result.total, int)
        assert isinstance(result.average, (int, float))
    
    @pytest.mark.asyncio
    async def test_get_event_trends_monthly(self, multiple_events_different_dates, clean_test_session):
        """월별 이벤트 트렌드 조회 테스트"""
        # When: 월별 트렌드 조회
        result = await event_service.get_event_trends(clean_test_session, period="monthly")
        
        # Then: 트렌드 데이터 반환
        assert result is not None
        assert result.period == "monthly"
        assert isinstance(result.trends, dict)
        assert len(result.trends) == 12  # 12개월


class TestEventServicesWithMocks:
    """Mock을 사용한 Event Services 단위 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_summary_with_matches(self, clean_test_session):
        """매치가 있는 이벤트 요약 테스트 (Mock 사용)"""
        # Given: Mock 데이터 설정
        mock_event = AsyncMock()
        mock_event.id = 1
        mock_event.name = "UFC Test Event"
        mock_event.location = "Las Vegas, NV"
        mock_event.url = "http://example.com"
        mock_event.event_date = date(2024, 8, 1)
        
        mock_matches = [
            AsyncMock(method="KO/TKO", is_main_event=True),
            AsyncMock(method="Decision - Unanimous", is_main_event=False),
            AsyncMock(method="Submission", is_main_event=False)
        ]
        
        # When: Mock을 사용하여 service 함수 호출
        with patch('event.services.event_repo.get_event_by_id', return_value=mock_event), \
             patch('match.repositories.get_matches_by_event_id', return_value=mock_matches):
            
            result = await event_service.get_event_summary(clean_test_session, 1)
        
        # Then: 매치 통계가 올바르게 계산됨
        assert result is not None
        assert result.stats.total_matches == 3
        assert result.stats.main_events == 1
        
        # 결승 방식 통계 확인
        finish_methods = result.stats.finish_methods
        assert finish_methods["KO/TKO"] == 1
        assert finish_methods["Decision - Unanimous"] == 1
        assert finish_methods["Submission"] == 1
    
    @pytest.mark.asyncio
    async def test_search_events_relevance_sorting(self, clean_test_session):
        """검색 결과 관련성 정렬 테스트 (Mock 사용)"""
        # Given: Mock 데이터 설정
        mock_name_event1 = AsyncMock()
        mock_name_event1.id = 1
        mock_name_event1.name = "UFC Vegas"
        mock_name_event1.location = "Las Vegas, NV"
        mock_name_event1.event_date = date(2024, 8, 1)
        mock_name_event1.url = "http://example.com"
        
        mock_name_event2 = AsyncMock()
        mock_name_event2.id = 2
        mock_name_event2.name = "UFC Fight Night"
        mock_name_event2.location = "New York, NY"
        mock_name_event2.event_date = date(2024, 8, 2)
        mock_name_event2.url = "http://example.com"
        
        mock_location_event = AsyncMock()
        mock_location_event.id = 3
        mock_location_event.name = "Bellator"
        mock_location_event.location = "Las Vegas, Nevada"
        mock_location_event.event_date = date(2024, 8, 3)
        mock_location_event.url = "http://example.com"
        
        mock_name_events = [mock_name_event1, mock_name_event2]
        mock_location_events = [mock_location_event]
        
        # When: Mock을 사용하여 service 함수 호출
        with patch('event.services.event_repo.search_events_by_name', return_value=mock_name_events), \
             patch('event.services.event_repo.get_events_by_location', return_value=mock_location_events):
            
            result = await event_service.search_events(
                clean_test_session, query="Vegas", search_type="all", limit=10
            )
        
        # Then: 관련성 순으로 정렬됨
        assert isinstance(result, EventSearchDTO)
        assert len(result.results) == 3
        
        # 관련성 순서 확인
        for i in range(len(result.results) - 1):
            assert result.results[i].relevance >= result.results[i + 1].relevance
        
        # 중복 제거 확인 (같은 이벤트 ID가 두 번 나오지 않음)
        event_ids = [item.event.id for item in result.results]
        assert len(event_ids) == len(set(event_ids))
    
    @pytest.mark.asyncio
    async def test_get_events_calendar_with_empty_days(self, clean_test_session):
        """빈 날짜가 있는 월별 캘린더 테스트 (Mock 사용)"""
        # Given: Mock 데이터 설정 (8월에 몇 개 이벤트만)
        mock_event1 = AsyncMock()
        mock_event1.event_date = date(2024, 8, 1)
        mock_event1.name = "Event 1"
        mock_event1.location = "Las Vegas"
        mock_event1.url = "http://example.com"
        
        mock_event2 = AsyncMock()
        mock_event2.event_date = date(2024, 8, 15)
        mock_event2.name = "Event 2"
        mock_event2.location = "New York"
        mock_event2.url = "http://example.com"
        
        mock_events = [mock_event1, mock_event2]
        
        # When: Mock을 사용하여 service 함수 호출
        with patch('event.services.event_repo.get_events_by_month', return_value=mock_events):
            result = await event_service.get_events_calendar(clean_test_session, year=2024, month=8)
        
        # Then: 이벤트가 있는 날짜만 캘린더에 포함됨
        assert result.type == "monthly"
        assert result.total_events == 2
        
        calendar_data = result.calendar
        assert "1" in calendar_data
        assert "15" in calendar_data
        assert "16" not in calendar_data  # 이벤트가 없는 날은 포함되지 않음
    
    @pytest.mark.asyncio
    async def test_get_location_statistics_calculation(self, clean_test_session):
        """장소별 통계 계산 테스트 (Mock 사용)"""
        # Given: Mock 데이터 설정
        location_counts = {
            "Las Vegas": 15,
            "New York": 8,
            "London": 5,
            "Other": 0
        }
        
        # Mock function to return different counts based on location
        async def mock_count_by_location(session, location):
            return location_counts.get(location, 0)
        
        # When: Mock을 사용하여 service 함수 호출
        with patch('event.services.event_repo.get_event_count_by_location', side_effect=mock_count_by_location), \
             patch('event.services.event_repo.get_event_count_by_year', return_value=30):
            
            result = await event_service.get_location_statistics(clean_test_session)
        
        # Then: 통계가 올바르게 계산됨
        assert result.location_breakdown["Las Vegas"] == 15
        assert result.location_breakdown["New York"] == 8
        assert result.location_breakdown["London"] == 5
        assert result.total_major_locations == 28  # 15 + 8 + 5
        assert result.total_events_this_year == 30
        assert result.other_locations == 2  # 30 - 28
    
    @pytest.mark.asyncio
    async def test_get_next_and_last_events_date_calculations(self, clean_test_session):
        """다음/최근 이벤트 날짜 계산 테스트 (Mock 사용)"""
        # Given: Mock 데이터 설정
        today = date.today()
        next_event_date = today + timedelta(days=10)
        last_event_date = today - timedelta(days=5)
        
        mock_next_event = AsyncMock()
        mock_next_event.id = 1
        mock_next_event.name = "UFC Next"
        mock_next_event.location = "Las Vegas"
        mock_next_event.event_date = next_event_date
        mock_next_event.url = "http://example.com"
        
        mock_last_event = AsyncMock()
        mock_last_event.id = 2
        mock_last_event.name = "UFC Last"
        mock_last_event.location = "New York"
        mock_last_event.event_date = last_event_date
        mock_last_event.url = "http://example.com"
        
        # When: Mock을 사용하여 service 함수 호출
        with patch('event.services.event_repo.get_next_event', return_value=mock_next_event), \
             patch('event.services.event_repo.get_last_event', return_value=mock_last_event):
            
            result = await event_service.get_next_and_last_events(clean_test_session)
        
        # Then: 날짜 계산이 올바름
        assert result.days_until_next == 10
        assert result.days_since_last == 5
        assert result.next_event.id == mock_next_event.id
        assert result.last_event.id == mock_last_event.id


class TestEventServicesErrorHandling:
    """Event Services 에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_summary_invalid_event_id(self, clean_test_session):
        """잘못된 이벤트 ID 처리 테스트"""
        # When & Then: 잘못된 이벤트 ID로 조회시 EventValidationError 발생
        with pytest.raises(EventValidationError, match="event_id must be a positive integer"):
            await event_service.get_event_summary(clean_test_session, -1)
        
        with pytest.raises(EventValidationError, match="event_id must be a positive integer"):
            await event_service.get_event_summary(clean_test_session, 0)
    
    @pytest.mark.asyncio
    async def test_get_event_summary_repository_error_handling(self, clean_test_session):
        """Repository 에러 시 처리 테스트"""
        # Given: event_repo에서 예외 발생하도록 설정
        with patch('event.services.event_repo.get_event_by_id', side_effect=Exception("Database error")):
            
            # When & Then: EventQueryError로 래핑되어 발생
            with pytest.raises(EventQueryError, match="Event query 'get_event_summary' failed"):
                await event_service.get_event_summary(clean_test_session, 1)
    
    @pytest.mark.asyncio
    async def test_search_events_empty_query_handling(self, clean_test_session):
        """빈 검색어 처리 테스트"""
        # When & Then: 빈 검색어로 조회시 EventValidationError 발생
        with pytest.raises(EventValidationError, match="Search query cannot be empty"):
            await event_service.search_events(clean_test_session, query="", search_type="all")
        
        with pytest.raises(EventValidationError, match="Search query cannot be empty"):
            await event_service.search_events(clean_test_session, query="   ", search_type="all")
    
    @pytest.mark.asyncio
    async def test_search_events_invalid_search_type(self, clean_test_session):
        """잘못된 검색 타입 처리 테스트"""
        # When & Then: 잘못된 검색 타입으로 조회시 EventValidationError 발생
        with pytest.raises(EventValidationError, match="search_type must be"):
            await event_service.search_events(clean_test_session, query="UFC", search_type="invalid")
    
    @pytest.mark.asyncio
    async def test_search_events_invalid_limit(self, clean_test_session):
        """잘못된 limit 값 처리 테스트"""
        # When & Then: 잘못된 limit 값으로 조회시 EventValidationError 발생
        with pytest.raises(EventValidationError, match="limit must be a positive integer"):
            await event_service.search_events(clean_test_session, query="UFC", search_type="name", limit=0)
        
        with pytest.raises(EventValidationError, match="limit must be a positive integer"):
            await event_service.search_events(clean_test_session, query="UFC", search_type="name", limit=-1)
    
    @pytest.mark.asyncio
    async def test_get_events_calendar_invalid_year(self, clean_test_session):
        """잘못된 연도로 캘린더 조회 테스트"""
        # When & Then: 잘못된 연도로 조회시 EventDateError 발생
        with pytest.raises(EventDateError, match="Year must be between 1993"):
            await event_service.get_events_calendar(clean_test_session, year=1990, month=1)
        
        current_year = date.today().year
        with pytest.raises(EventDateError, match="Year must be between 1993"):
            await event_service.get_events_calendar(clean_test_session, year=current_year + 20, month=1)
    
    @pytest.mark.asyncio
    async def test_get_events_calendar_invalid_month(self, clean_test_session):
        """잘못된 월로 캘린더 조회 테스트"""
        # When & Then: 잘못된 월로 조회시 EventDateError 발생
        with pytest.raises(EventDateError, match="Month must be between 1 and 12"):
            await event_service.get_events_calendar(clean_test_session, year=2024, month=0)
        
        with pytest.raises(EventDateError, match="Month must be between 1 and 12"):
            await event_service.get_events_calendar(clean_test_session, year=2024, month=13)
    
    @pytest.mark.asyncio
    async def test_get_events_calendar_future_date_handling(self, clean_test_session):
        """미래 날짜로 캘린더 조회 테스트"""
        # Given: 미래 날짜로 설정 (하지만 유효한 범위 내)
        future_year = date.today().year + 5
        
        with patch('event.services.event_repo.get_events_by_month', return_value=[]):
            # When: 미래 날짜로 캘린더 조회
            result = await event_service.get_events_calendar(
                clean_test_session, year=future_year, month=1
            )
        
        # Then: 빈 캘린더 반환
        assert result.type == "monthly"
        assert result.year == future_year
        assert result.total_events == 0
        assert result.calendar == {}
    
    @pytest.mark.asyncio
    async def test_get_event_timeline_repository_error(self, clean_test_session):
        """Timeline 조회 중 Repository 에러 처리 테스트"""
        # Given: event_repo에서 예외 발생하도록 설정
        with patch('event.services.event_repo.get_events_by_month', side_effect=Exception("Database connection error")):
            
            # When & Then: EventQueryError로 래핑되어 발생
            with pytest.raises(EventQueryError, match="Event query 'get_event_timeline' failed"):
                await event_service.get_event_timeline(clean_test_session, period="month")
    
    @pytest.mark.asyncio
    async def test_search_events_repository_error(self, clean_test_session):
        """Search 중 Repository 에러 처리 테스트"""
        # Given: event_repo에서 예외 발생하도록 설정
        with patch('event.services.event_repo.search_events_by_name', side_effect=Exception("Search index error")):
            
            # When & Then: EventQueryError로 래핑되어 발생
            with pytest.raises(EventQueryError, match="Event query 'search_events' failed"):
                await event_service.search_events(clean_test_session, query="UFC", search_type="name")
    
    @pytest.mark.asyncio
    async def test_get_events_calendar_repository_error(self, clean_test_session):
        """Calendar 조회 중 Repository 에러 처리 테스트"""
        # Given: event_repo에서 예외 발생하도록 설정
        with patch('event.services.event_repo.get_events_by_month', side_effect=Exception("Calendar query error")):
            
            # When & Then: EventQueryError로 래핑되어 발생
            with pytest.raises(EventQueryError, match="Event query 'get_events_calendar' failed"):
                await event_service.get_events_calendar(clean_test_session, year=2024, month=8)
    
    @pytest.mark.asyncio
    async def test_get_event_recommendations_repository_error(self, clean_test_session):
        """Recommendations 조회 중 Repository 에러 처리 테스트"""
        # Given: event_repo에서 예외 발생하도록 설정
        with patch('event.services.event_repo.get_upcoming_events', side_effect=Exception("Recommendation error")):
            
            # When & Then: EventQueryError로 래핑되어 발생
            with pytest.raises(EventQueryError, match="Event query 'get_event_recommendations' failed"):
                await event_service.get_event_recommendations(clean_test_session, recommendation_type="upcoming")


if __name__ == "__main__":
    print("Event Services 테스트 실행...")
    print("✅ 비즈니스 로직 레이어 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/event/test_services.py -v")