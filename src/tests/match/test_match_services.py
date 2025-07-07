"""
Match Services 테스트
match/services.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch

from match import services as match_service
from match.dto import EventMatchesDTO, MatchWithFightersDTO, FighterBasicInfoDTO


class TestMatchServicesWithTestDB:
    """Test DB를 사용한 Match Services 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_matches_success(self, multiple_matches_for_event, clean_test_session):
        """이벤트 매치 조회 성공 테스트"""
        # Given: multiple_matches_for_event fixture 사용
        event, matches = multiple_matches_for_event
        
        # When: 이벤트 이름으로 매치 조회
        result = await match_service.get_event_matches(clean_test_session, event.name)
        
        # Then: 완전한 이벤트 정보 반환
        assert result is not None
        assert isinstance(result, EventMatchesDTO)
        
        # 이벤트 기본 정보 확인
        assert result.event_name == event.name
        assert result.event_date is not None
        assert isinstance(result.matches, list)
        assert len(result.matches) == 3
        
        # 매치들이 order 순으로 정렬되어 있는지 확인
        match_orders = [match_info.match.order for match_info in result.matches]
        assert match_orders == sorted(match_orders)
        
        # 각 매치 정보 구조 확인
        for match_info in result.matches:
            assert isinstance(match_info, MatchWithFightersDTO)
            assert match_info.match is not None
            # winner_fighter와 loser_fighter는 FighterMatch 관계가 없으면 None일 수 있음
    
    @pytest.mark.asyncio
    async def test_get_event_matches_with_winner_loser(self, match_with_fighters, clean_test_session):
        """승자/패자가 있는 매치 조회 테스트"""
        # Given: match_with_fighters fixture 사용 (승자와 패자가 있는 매치)
        match, fighters, fighter_matches = match_with_fighters
        
        # 이벤트를 통해 조회하기 위해 이벤트 정보 가져오기
        from event import repositories as event_repo
        event = await event_repo.get_event_by_id(clean_test_session, match.event_id)
        
        # When: 이벤트 이름으로 매치 조회
        result = await match_service.get_event_matches(clean_test_session, event.name)
        
        # Then: 승자와 패자 정보가 올바르게 포함됨
        assert result is not None
        assert len(result.matches) == 1
        
        match_info = result.matches[0]
        
        # 승자 정보 확인
        winner = match_info.winner_fighter
        assert winner is not None
        assert isinstance(winner, FighterBasicInfoDTO)
        assert winner.name == "Sample Fighter"  # sample_fighter fixture의 이름
        
        # 패자 정보 확인  
        loser = match_info.loser_fighter
        assert loser is not None
        assert isinstance(loser, FighterBasicInfoDTO)
        assert loser.name == "Opponent Fighter"  # match_with_fighters fixture에서 생성한 상대방
    
    @pytest.mark.asyncio
    async def test_get_event_matches_nonexistent_event(self, clean_test_session):
        """존재하지 않는 이벤트 조회 테스트"""
        # When: 존재하지 않는 이벤트 이름으로 조회
        result = await match_service.get_event_matches(clean_test_session, "Nonexistent Event")
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_event_matches_empty_matches(self, sample_event, clean_test_session):
        """매치가 없는 이벤트 조회 테스트"""
        # Given: 매치가 없는 이벤트 (sample_event fixture 사용)
        
        # When: 이벤트 이름으로 매치 조회
        result = await match_service.get_event_matches(clean_test_session, sample_event.name)
        
        # Then: 빈 매치 리스트 반환
        assert result is not None
        assert result.event_name == sample_event.name
        assert result.matches == []
    
    @pytest.mark.asyncio 
    async def test_get_event_matches_order_sorting(self, multiple_matches_for_event, clean_test_session):
        """매치 순서 정렬 테스트"""
        # Given: multiple_matches_for_event fixture 사용
        event, matches = multiple_matches_for_event
        
        # When: 이벤트 매치 조회
        result = await match_service.get_event_matches(clean_test_session, event.name)
        
        # Then: 매치들이 order 순으로 정렬됨
        assert result is not None
        assert len(result.matches) == 3
        
        # order 값들이 오름차순으로 정렬되어 있는지 확인
        orders = [match_info.match.order for match_info in result.matches]
        assert orders == [1, 2, 3]
        
        # 메인 이벤트가 마지막에 있는지 확인
        last_match = result.matches[-1].match
        assert last_match.is_main_event is True


class TestMatchServicesWithMocks:
    """Mock을 사용한 Match Services 단위 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_matches_with_draw_fighters(self, clean_test_session):
        """무승부 파이터들이 있는 매치 테스트"""
        # Given: Mock 데이터 설정
        mock_event = AsyncMock()
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.event_date = "2024-01-15"
        
        mock_match = AsyncMock()
        mock_match.id = 1
        mock_match.order = 1
        mock_match.event_id = 1
        mock_match.weight_class_id = None
        mock_match.method = "Decision"
        mock_match.result_round = 3
        mock_match.time = "5:00"
        mock_match.is_main_event = False
        mock_match.detail_url = None
        
        mock_fighter_matches = [
            AsyncMock(fighter_id=1, result="draw"),
            AsyncMock(fighter_id=2, result="draw")
        ]
        
        mock_fighter1 = AsyncMock()
        mock_fighter1.id = 1
        mock_fighter1.name = "Fighter 1"
        mock_fighter2 = AsyncMock()
        mock_fighter2.id = 2
        mock_fighter2.name = "Fighter 2"
        
        # When: Mock을 사용하여 service 함수 호출
        with patch('match.services.event_repo.get_event_by_name', return_value=mock_event), \
             patch('match.services.match_repo.get_matches_by_event_id', return_value=[mock_match]), \
             patch('match.services.match_repo.get_fighter_match_by_match_id', return_value=mock_fighter_matches), \
             patch('match.services.fighter_repo.get_fighter_by_id', side_effect=[mock_fighter1, mock_fighter2]):
            
            result = await match_service.get_event_matches(clean_test_session, "Test Event")
        
        # Then: 무승부 파이터들이 올바르게 처리됨
        assert result is not None
        assert len(result.matches) == 1
        
        match_info = result.matches[0]
        assert match_info.winner_fighter is None
        assert match_info.loser_fighter is None
        assert match_info.draw_fighters is not None
        assert len(match_info.draw_fighters) == 2
        
        # 무승부 파이터 정보 확인
        draw_fighters = match_info.draw_fighters
        assert any(f.id == 1 and f.name == "Fighter 1" for f in draw_fighters)
        assert any(f.id == 2 and f.name == "Fighter 2" for f in draw_fighters)
    
    @pytest.mark.asyncio
    async def test_get_event_matches_missing_fighter_handling(self, clean_test_session):
        """파이터 정보가 없는 경우 처리 테스트"""
        # Given: Mock 데이터 설정 (한 파이터가 None)
        mock_event = AsyncMock()
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.event_date = "2024-01-15"
        
        mock_match = AsyncMock()
        mock_match.id = 1
        mock_match.order = 1
        mock_match.event_id = 1
        mock_match.weight_class_id = None
        mock_match.method = "Decision"
        mock_match.result_round = 3
        mock_match.time = "5:00"
        mock_match.is_main_event = False
        mock_match.detail_url = None
        
        mock_fighter_matches = [
            AsyncMock(fighter_id=1, result="win"),
            AsyncMock(fighter_id=999, result="loss")  # 존재하지 않는 파이터
        ]
        
        mock_fighter1 = AsyncMock()
        mock_fighter1.id = 1
        mock_fighter1.name = "Fighter 1"
        
        # When: Mock을 사용하여 service 함수 호출 (한 파이터는 None 반환)
        with patch('match.services.event_repo.get_event_by_name', return_value=mock_event), \
             patch('match.services.match_repo.get_matches_by_event_id', return_value=[mock_match]), \
             patch('match.services.match_repo.get_fighter_match_by_match_id', return_value=mock_fighter_matches), \
             patch('match.services.fighter_repo.get_fighter_by_id', side_effect=[mock_fighter1, None]):
            
            result = await match_service.get_event_matches(clean_test_session, "Test Event")
        
        # Then: 존재하는 파이터만 결과에 포함됨
        assert result is not None
        assert len(result.matches) == 1
        
        match_info = result.matches[0]
        assert match_info.winner_fighter is not None
        assert match_info.winner_fighter.name == "Fighter 1"
        assert match_info.loser_fighter is None  # 존재하지 않는 파이터는 None
    
    @pytest.mark.asyncio
    async def test_get_event_matches_none_order_handling(self, clean_test_session):
        """order가 None인 매치 처리 테스트"""
        # Given: Mock 데이터 설정 (order가 None인 매치 포함)
        mock_event = AsyncMock()
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.event_date = "2024-01-15"
        
        def create_mock_match(match_id, order):
            mock = AsyncMock()
            mock.id = match_id
            mock.order = order
            mock.event_id = 1
            mock.weight_class_id = None
            mock.method = "Decision"
            mock.result_round = 3
            mock.time = "5:00"
            mock.is_main_event = False
            mock.detail_url = None
            return mock
            
        mock_matches = [
            create_mock_match(1, 1),
            create_mock_match(2, None),  # order가 None
            create_mock_match(3, 2)
        ]
        
        # When: Mock을 사용하여 service 함수 호출
        with patch('match.services.event_repo.get_event_by_name', return_value=mock_event), \
             patch('match.services.match_repo.get_matches_by_event_id', return_value=mock_matches), \
             patch('match.services.match_repo.get_fighter_match_by_match_id', return_value=[]), \
             patch('match.services.fighter_repo.get_fighter_by_id', return_value=None):
            
            result = await match_service.get_event_matches(clean_test_session, "Test Event")
        
        # Then: order가 None인 매치가 마지막에 위치
        assert result is not None
        assert len(result.matches) == 3
        
        # order 값 확인 (None은 999로 치환되어 마지막에 정렬됨)
        orders = [match_info.match.order for match_info in result.matches]
        assert orders == [1, 2, None]  # 실제로는 [1, 2, None] 순서로 정렬됨


class TestPlaceholderServiceFunctions:
    """아직 구현되지 않은 서비스 함수들 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_match_detail_placeholder(self, clean_test_session):
        """get_match_detail 함수 placeholder 테스트"""
        # When: placeholder 함수 호출
        result = await match_service.get_match_detail(clean_test_session, 1)
        
        # Then: None 반환 (아직 구현되지 않음)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_highest_stats_matches_placeholder(self, clean_test_session):
        """get_highest_stats_matches 함수 placeholder 테스트"""
        # When: placeholder 함수 호출
        result = await match_service.get_highest_stats_matches(clean_test_session, "knockdowns", 5)
        
        # Then: None 반환 (아직 구현되지 않음)
        assert result is None


class TestMatchServicesErrorHandling:
    """Match Services 에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_matches_repository_error_handling(self, clean_test_session):
        """Repository 에러 시 처리 테스트"""
        # Given: event_repo에서 예외 발생하도록 설정
        with patch('match.services.event_repo.get_event_by_name', side_effect=Exception("Database error")):
            
            # When & Then: 예외가 전파됨
            with pytest.raises(Exception, match="Database error"):
                await match_service.get_event_matches(clean_test_session, "Test Event")
    
    @pytest.mark.asyncio
    async def test_get_event_matches_partial_failure_handling(self, clean_test_session):
        """일부 repository 호출 실패 시 처리 테스트"""
        # Given: Mock 데이터 설정
        mock_event = AsyncMock()
        mock_event.id = 1
        mock_event.name = "Test Event"
        mock_event.event_date = "2024-01-15"
        
        mock_match = AsyncMock()
        mock_match.id = 1
        mock_match.order = 1
        
        # When: match_repo에서만 예외 발생
        with patch('match.services.event_repo.get_event_by_name', return_value=mock_event), \
             patch('match.services.match_repo.get_matches_by_event_id', side_effect=Exception("Match repo error")):
            
            # Then: 예외가 전파됨
            with pytest.raises(Exception, match="Match repo error"):
                await match_service.get_event_matches(clean_test_session, "Test Event")


if __name__ == "__main__":
    print("Match Services 테스트 실행...")
    print("✅ 비즈니스 로직 레이어 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/match/test_services.py -v")