"""
Event Repositories 테스트
event/repositories.py의 모든 repository 함수에 대한 포괄적인 테스트
"""
import pytest
from datetime import date, timedelta

from event import repositories as event_repo
from event.models import EventSchema


class TestBasicEventRepositoryWithTestDB:
    """Test DB를 사용한 기본 Event Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_by_id_existing(self, sample_event, clean_test_session):
        """존재하는 이벤트 ID로 조회 테스트"""
        # When: Repository 함수 호출
        result = await event_repo.get_event_by_id(clean_test_session, sample_event.id)
        
        # Then: 올바른 EventSchema 반환
        assert result is not None
        assert isinstance(result, EventSchema)
        assert result.id == sample_event.id
        assert result.name == sample_event.name
        assert result.location == sample_event.location
        assert result.event_date == sample_event.event_date
    
    @pytest.mark.asyncio
    async def test_get_event_by_id_nonexistent(self, clean_test_session):
        """존재하지 않는 이벤트 ID로 조회 테스트"""
        # When: 존재하지 않는 ID로 조회
        result = await event_repo.get_event_by_id(clean_test_session, 99999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_events_with_limit(self, multiple_events_different_dates, clean_test_session):
        """이벤트 목록 조회 제한 테스트"""
        # Given: multiple_events_different_dates fixture 사용
        events = multiple_events_different_dates
        
        # When: 최근 2개 이벤트만 조회
        result = await event_repo.get_events(clean_test_session, limit=2, order_by="desc")
        
        # Then: 2개의 이벤트가 날짜 역순으로 반환
        assert isinstance(result, list)
        assert len(result) == 2
        
        # 모든 결과가 EventSchema 타입인지 확인
        for event in result:
            assert isinstance(event, EventSchema)
        
        # 날짜 역순 정렬 확인
        assert result[0].event_date >= result[1].event_date
    
    @pytest.mark.asyncio
    async def test_get_events_ascending_order(self, multiple_events_different_dates, clean_test_session):
        """이벤트 목록 오름차순 조회 테스트"""
        # Given: multiple_events_different_dates fixture 사용
        events = multiple_events_different_dates
        
        # When: 날짜 오름차순으로 조회
        result = await event_repo.get_events(clean_test_session, order_by="asc")
        
        # Then: 날짜 오름차순으로 정렬됨
        assert isinstance(result, list)
        assert len(result) == len(events)
        
        # 날짜 오름차순 정렬 확인
        for i in range(len(result) - 1):
            assert result[i].event_date <= result[i + 1].event_date


class TestEventSearchRepositoryWithTestDB:
    """Test DB를 사용한 Event Search Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_by_name_partial_match(self, sample_event, clean_test_session):
        """부분 이름 매칭으로 이벤트 조회 테스트"""
        # When: 이벤트 이름의 일부로 검색
        result = await event_repo.get_event_by_name(clean_test_session, "UFC Test")
        
        # Then: 일치하는 이벤트 반환
        assert result is not None
        assert isinstance(result, EventSchema)
        assert result.id == sample_event.id
        assert "UFC Test" in result.name
    
    @pytest.mark.asyncio
    async def test_get_event_by_name_case_insensitive(self, sample_event, clean_test_session):
        """대소문자 무시 이름 검색 테스트"""
        # When: 소문자로 검색
        result = await event_repo.get_event_by_name(clean_test_session, "ufc test")
        
        # Then: 일치하는 이벤트 반환
        assert result is not None
        assert result.id == sample_event.id
    
    @pytest.mark.asyncio
    async def test_get_event_by_name_no_match(self, clean_test_session):
        """일치하지 않는 이름으로 검색 테스트"""
        # When: 존재하지 않는 이름으로 검색
        result = await event_repo.get_event_by_name(clean_test_session, "Nonexistent Event")
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_events_by_name(self, multiple_events_different_names, clean_test_session):
        """이벤트 이름 검색 테스트"""
        # Given: multiple_events_different_names fixture 사용
        events = multiple_events_different_names
        
        # When: "UFC"로 검색
        result = await event_repo.search_events_by_name(clean_test_session, "UFC", limit=5)
        
        # Then: UFC가 포함된 이벤트들 반환
        assert isinstance(result, list)
        assert len(result) >= 1
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert "UFC" in event.name.upper()
    
    @pytest.mark.asyncio
    async def test_get_event_by_exact_name(self, sample_event, clean_test_session):
        """정확한 이름으로 이벤트 조회 테스트"""
        # When: 정확한 이름으로 검색
        result = await event_repo.get_event_by_exact_name(clean_test_session, sample_event.name)
        
        # Then: 일치하는 이벤트 반환
        assert result is not None
        assert result.id == sample_event.id
        assert result.name == sample_event.name


class TestEventDateRepositoryWithTestDB:
    """Test DB를 사용한 Event Date Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_events_by_year(self, multiple_events_different_dates, clean_test_session):
        """연도별 이벤트 조회 테스트"""
        # When: 2024년 이벤트 조회
        result = await event_repo.get_events_by_year(clean_test_session, 2024)
        
        # Then: 2024년 이벤트들이 날짜순으로 반환
        assert isinstance(result, list)
        assert len(result) >= 1
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert event.event_date.year == 2024
        
        # 날짜 오름차순 정렬 확인
        for i in range(len(result) - 1):
            assert result[i].event_date <= result[i + 1].event_date
    
    @pytest.mark.asyncio
    async def test_get_events_by_month(self, multiple_events_different_dates, clean_test_session):
        """월별 이벤트 조회 테스트"""
        # When: 2024년 1월 이벤트 조회
        result = await event_repo.get_events_by_month(clean_test_session, 2024, 1)
        
        # Then: 2024년 1월 이벤트들 반환
        assert isinstance(result, list)
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert event.event_date.year == 2024
            assert event.event_date.month == 1
    
    @pytest.mark.asyncio
    async def test_get_events_by_date_on(self, sample_event, clean_test_session):
        """특정 날짜의 이벤트 조회 테스트"""
        # When: 샘플 이벤트 날짜로 조회
        result = await event_repo.get_events_by_date(
            clean_test_session, sample_event.event_date, direction="on"
        )
        
        # Then: 해당 날짜의 이벤트 반환
        assert isinstance(result, list)
        assert len(result) >= 1
        assert sample_event.id in [e.id for e in result]
    
    @pytest.mark.asyncio
    async def test_get_events_by_date_before(self, multiple_events_different_dates, clean_test_session):
        """특정 날짜 이전 이벤트 조회 테스트"""
        # Given: 기준 날짜 설정
        target_date = date(2024, 6, 1)
        
        # When: 2024년 6월 1일 이전 이벤트 조회
        result = await event_repo.get_events_by_date(
            clean_test_session, target_date, direction="before"
        )
        
        # Then: 기준 날짜 이전의 이벤트들이 최신순으로 반환
        assert isinstance(result, list)
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert event.event_date < target_date
    
    @pytest.mark.asyncio
    async def test_get_events_by_date_after(self, multiple_events_different_dates, clean_test_session):
        """특정 날짜 이후 이벤트 조회 테스트"""
        # Given: 기준 날짜 설정
        target_date = date(2024, 1, 1)
        
        # When: 2024년 1월 1일 이후 이벤트 조회
        result = await event_repo.get_events_by_date(
            clean_test_session, target_date, direction="after"
        )
        
        # Then: 기준 날짜 이후의 이벤트들이 날짜순으로 반환
        assert isinstance(result, list)
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert event.event_date > target_date


class TestMMASpecificEventRepositoryWithTestDB:
    """Test DB를 사용한 MMA 전용 Event Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_recent_events(self, events_past_and_future, clean_test_session):
        """최근 개최된 이벤트 조회 테스트"""
        # Given: events_past_and_future fixture 사용
        past_events, future_events = events_past_and_future
        
        # When: 최근 3개 이벤트 조회
        result = await event_repo.get_recent_events(clean_test_session, limit=3)
        
        # Then: 과거 이벤트들이 최신순으로 반환
        assert isinstance(result, list)
        assert len(result) <= 3
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert event.event_date <= date.today()
        
        # 날짜 역순 정렬 확인
        for i in range(len(result) - 1):
            assert result[i].event_date >= result[i + 1].event_date
    
    @pytest.mark.asyncio
    async def test_get_upcoming_events(self, events_past_and_future, clean_test_session):
        """다가오는 이벤트 조회 테스트"""
        # Given: events_past_and_future fixture 사용
        past_events, future_events = events_past_and_future
        
        # When: 다가오는 3개 이벤트 조회
        result = await event_repo.get_upcoming_events(clean_test_session, limit=3)
        
        # Then: 미래 이벤트들이 날짜순으로 반환
        assert isinstance(result, list)
        assert len(result) <= 3
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert event.event_date > date.today()
        
        # 날짜 오름차순 정렬 확인
        for i in range(len(result) - 1):
            assert result[i].event_date <= result[i + 1].event_date
    
    @pytest.mark.asyncio
    async def test_get_next_event(self, events_past_and_future, clean_test_session):
        """가장 가까운 다음 이벤트 조회 테스트"""
        # Given: events_past_and_future fixture 사용
        past_events, future_events = events_past_and_future
        
        # When: 가장 가까운 다음 이벤트 조회
        result = await event_repo.get_next_event(clean_test_session)
        
        # Then: 가장 가까운 미래 이벤트 반환
        if future_events:  # 미래 이벤트가 있는 경우
            assert result is not None
            assert isinstance(result, EventSchema)
            assert result.event_date > date.today()
            
            # 가장 가까운 이벤트인지 확인
            all_upcoming = await event_repo.get_upcoming_events(clean_test_session, limit=10)
            if all_upcoming:
                assert result.event_date == min(e.event_date for e in all_upcoming)
        else:
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_last_event(self, events_past_and_future, clean_test_session):
        """가장 최근 개최된 이벤트 조회 테스트"""
        # Given: events_past_and_future fixture 사용
        past_events, future_events = events_past_and_future
        
        # When: 가장 최근 이벤트 조회
        result = await event_repo.get_last_event(clean_test_session)
        
        # Then: 가장 최근 과거 이벤트 반환
        if past_events:  # 과거 이벤트가 있는 경우
            assert result is not None
            assert isinstance(result, EventSchema)
            assert result.event_date <= date.today()
            
            # 가장 최근 이벤트인지 확인
            all_recent = await event_repo.get_recent_events(clean_test_session, limit=10)
            if all_recent:
                assert result.event_date == max(e.event_date for e in all_recent)
        else:
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_events_by_location(self, events_different_locations, clean_test_session):
        """장소별 이벤트 조회 테스트"""
        # Given: events_different_locations fixture 사용
        events = events_different_locations
        
        # When: "Las Vegas"로 검색
        result = await event_repo.get_events_by_location(clean_test_session, "Las Vegas")
        
        # Then: Las Vegas가 포함된 이벤트들 반환
        assert isinstance(result, list)
        assert len(result) >= 1
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert "Las Vegas" in event.location
    
    @pytest.mark.asyncio
    async def test_get_events_date_range(self, multiple_events_different_dates, clean_test_session):
        """날짜 범위별 이벤트 조회 테스트"""
        # Given: 날짜 범위 설정
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # When: 2024년 전체 범위로 조회
        result = await event_repo.get_events_date_range(
            clean_test_session, start_date, end_date
        )
        
        # Then: 범위 내 이벤트들이 날짜순으로 반환
        assert isinstance(result, list)
        
        for event in result:
            assert isinstance(event, EventSchema)
            assert start_date <= event.event_date <= end_date
        
        # 날짜 오름차순 정렬 확인
        for i in range(len(result) - 1):
            assert result[i].event_date <= result[i + 1].event_date


class TestEventStatisticsRepositoryWithTestDB:
    """Test DB를 사용한 Event Statistics Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_count_by_year(self, multiple_events_different_dates, clean_test_session):
        """연도별 이벤트 개수 조회 테스트"""
        # When: 2024년 이벤트 개수 조회
        result = await event_repo.get_event_count_by_year(clean_test_session, 2024)
        
        # Then: 양의 정수 반환
        assert isinstance(result, int)
        assert result >= 0
        
        # 실제 2024년 이벤트 조회해서 개수 비교
        events_2024 = await event_repo.get_events_by_year(clean_test_session, 2024)
        assert result == len(events_2024)
    
    @pytest.mark.asyncio
    async def test_get_event_count_by_year_no_events(self, clean_test_session):
        """이벤트가 없는 연도의 개수 조회 테스트"""
        # When: 이벤트가 없는 연도로 조회
        result = await event_repo.get_event_count_by_year(clean_test_session, 1900)
        
        # Then: 0 반환
        assert result == 0
    
    @pytest.mark.asyncio
    async def test_get_event_count_by_location(self, events_different_locations, clean_test_session):
        """장소별 이벤트 개수 조회 테스트"""
        # When: "Las Vegas" 이벤트 개수 조회
        result = await event_repo.get_event_count_by_location(clean_test_session, "Las Vegas")
        
        # Then: 양의 정수 반환
        assert isinstance(result, int)
        assert result >= 0
        
        # 실제 Las Vegas 이벤트 조회해서 개수 비교
        events_vegas = await event_repo.get_events_by_location(clean_test_session, "Las Vegas")
        assert result == len(events_vegas)
    
    @pytest.mark.asyncio
    async def test_get_event_count_by_location_no_events(self, clean_test_session):
        """이벤트가 없는 장소의 개수 조회 테스트"""
        # When: 존재하지 않는 장소로 조회
        result = await event_repo.get_event_count_by_location(clean_test_session, "Nonexistent City")
        
        # Then: 0 반환
        assert result == 0


class TestRepositoryErrorHandlingWithTestDB:
    """Repository 에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_events_by_year_invalid_year(self, clean_test_session):
        """잘못된 연도로 조회 테스트"""
        # When: 음수 연도로 조회
        result = await event_repo.get_events_by_year(clean_test_session, -1)
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_events_by_month_invalid_month(self, clean_test_session):
        """잘못된 월로 조회 테스트"""
        # When: 잘못된 월로 조회
        result = await event_repo.get_events_by_month(clean_test_session, 2024, 13)
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_search_events_by_name_empty_string(self, clean_test_session):
        """빈 문자열로 검색 테스트"""
        # When: 빈 문자열로 검색
        result = await event_repo.search_events_by_name(clean_test_session, "", limit=5)
        
        # Then: 모든 이벤트 반환 (ILIKE '%''%'는 모든 문자열과 매칭)
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_get_events_date_range_invalid_range(self, clean_test_session):
        """잘못된 날짜 범위로 조회 테스트"""
        # Given: 시작 날짜가 종료 날짜보다 뒤인 경우
        start_date = date(2024, 12, 31)
        end_date = date(2024, 1, 1)
        
        # When: 잘못된 범위로 조회
        result = await event_repo.get_events_date_range(
            clean_test_session, start_date, end_date
        )
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0


if __name__ == "__main__":
    print("Event Repositories 테스트 실행...")
    print("✅ Test Database를 사용한 완전한 통합 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/event/test_repositories.py -v")