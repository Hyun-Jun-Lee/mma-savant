"""
Match Services 테스트
match/services.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch

from match import services as match_service
from match.exceptions import (
    MatchNotFoundError, MatchValidationError, MatchQueryError
)


class TestPlaceholderServiceFunctions:
    """아직 구현되지 않은 서비스 함수들 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_match_detail_placeholder(self, clean_test_session):
        """get_match_detail 함수 placeholder 테스트"""
        # When & Then: 존재하지 않는 매치 ID로 조회시 MatchNotFoundError 발생
        with pytest.raises(MatchNotFoundError, match="Match not found with id"):
            await match_service.get_match_detail(clean_test_session, 99999)
    
    @pytest.mark.asyncio
    async def test_get_highest_stats_matches_placeholder(self, clean_test_session):
        """get_highest_stats_matches 함수 placeholder 테스트"""
        # When: placeholder 함수 호출
        result = await match_service.get_highest_stats_matches(clean_test_session, "knockdowns", 5)
        
        # Then: 빈 리스트 반환 (아직 구현되지 않음)
        assert result == []


class TestMatchServicesErrorHandling:
    """Match Services 에러 처리 테스트"""
    
    
    
    
    @pytest.mark.asyncio
    async def test_get_match_detail_invalid_match_id(self, clean_test_session):
        """잘못된 매치 ID 처리 테스트"""
        # When & Then: 잘못된 매치 ID로 조회시 MatchValidationError 발생
        with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
            await match_service.get_match_detail(clean_test_session, -1)
        
        with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
            await match_service.get_match_detail(clean_test_session, 0)
        
        with pytest.raises(MatchValidationError, match="match_id must be a positive integer"):
            await match_service.get_match_detail(clean_test_session, "invalid")
    
    @pytest.mark.asyncio
    async def test_get_match_detail_repository_error(self, clean_test_session):
        """get_match_detail Repository 에러 처리 테스트"""
        # Given: match_repo에서 예외 발생하도록 설정
        with patch('match.services.match_repo.get_match_by_id', side_effect=Exception("Database connection error")):
            
            # When & Then: MatchQueryError로 래핑되어 발생
            with pytest.raises(MatchQueryError, match="Match query 'get_match_detail' failed"):
                await match_service.get_match_detail(clean_test_session, 1)
    
    @pytest.mark.asyncio
    async def test_get_highest_stats_matches_empty_stat_name(self, clean_test_session):
        """빈 스탯 이름 처리 테스트"""
        # When & Then: 빈 스탯 이름으로 조회시 MatchValidationError 발생
        with pytest.raises(MatchValidationError, match="Stat name cannot be empty"):
            await match_service.get_highest_stats_matches(clean_test_session, "", 10)
        
        with pytest.raises(MatchValidationError, match="Stat name cannot be empty"):
            await match_service.get_highest_stats_matches(clean_test_session, "   ", 10)
    
    @pytest.mark.asyncio
    async def test_get_highest_stats_matches_success(self, clean_test_session):
        """스탯 기준 매치 조회 성공 테스트"""
        # Given: Mock 데이터 설정
        mock_matches = [AsyncMock(id=1), AsyncMock(id=2)]
        
        with patch('match.services.match_repo.get_matches_with_high_activity', return_value=mock_matches):
            # When: total_strikes 스탯으로 조회
            result = await match_service.get_highest_stats_matches(clean_test_session, "total_strikes", 10)
        
        # Then: 매치 리스트 반환
        assert result == mock_matches
    
    @pytest.mark.asyncio
    async def test_get_highest_stats_matches_invalid_limit(self, clean_test_session):
        """잘못된 limit 값 처리 테스트"""
        # When & Then: 잘못된 limit 값으로 조회시 MatchValidationError 발생
        with pytest.raises(MatchValidationError, match="limit must be a positive integer"):
            await match_service.get_highest_stats_matches(clean_test_session, "total_strikes", 0)
        
        with pytest.raises(MatchValidationError, match="limit must be a positive integer"):
            await match_service.get_highest_stats_matches(clean_test_session, "total_strikes", -1)
        
        with pytest.raises(MatchValidationError, match="limit must be a positive integer"):
            await match_service.get_highest_stats_matches(clean_test_session, "total_strikes", "invalid")
    
    @pytest.mark.asyncio
    async def test_get_highest_stats_matches_repository_error(self, clean_test_session):
        """get_highest_stats_matches Repository 에러 처리 테스트"""
        # Given: match_repo에서 예외 발생하도록 설정
        with patch('match.services.match_repo.get_matches_with_high_activity', side_effect=Exception("Repository error")):
            
            # When & Then: MatchQueryError로 래핑되어 발생
            with pytest.raises(MatchQueryError, match="Match query 'get_highest_stats_matches' failed"):
                await match_service.get_highest_stats_matches(clean_test_session, "total_strikes", 5)
    
    @pytest.mark.asyncio
    async def test_get_matches_by_finish_method_success(self, clean_test_session):
        """피니시 방법별 매치 조회 성공 테스트"""
        # Given: Mock 데이터 설정
        mock_matches = [
            AsyncMock(id=1, method="KO/TKO"),
            AsyncMock(id=2, method="KO")
        ]
        
        with patch('match.services.match_repo.get_matches_by_finish_method', return_value=mock_matches):
            # When: KO로 끝난 매치들 조회
            result = await match_service.get_matches_by_finish_method(clean_test_session, "KO", 10)
        
        # Then: 매치 리스트 반환
        assert result == mock_matches
    
    @pytest.mark.asyncio
    async def test_get_matches_by_finish_method_invalid_method(self, clean_test_session):
        """잘못된 피니시 방법 처리 테스트"""
        # When & Then: 빈 방법으로 조회시 MatchValidationError 발생
        with pytest.raises(MatchValidationError, match="Finish method cannot be empty"):
            await match_service.get_matches_by_finish_method(clean_test_session, "", 10)
        
        with pytest.raises(MatchValidationError, match="Finish method cannot be empty"):
            await match_service.get_matches_by_finish_method(clean_test_session, "   ", 10)
    
    @pytest.mark.asyncio
    async def test_get_matches_by_duration_success(self, clean_test_session):
        """지속시간별 매치 조회 성공 테스트"""
        # Given: Mock 데이터 설정
        mock_matches = [
            AsyncMock(id=1, result_round=3),
            AsyncMock(id=2, result_round=5)
        ]
        
        with patch('match.services.match_repo.get_matches_by_duration', return_value=mock_matches):
            # When: 3라운드 이상 매치들 조회
            result = await match_service.get_matches_by_duration(clean_test_session, min_rounds=3, limit=10)
        
        # Then: 매치 리스트 반환
        assert result == mock_matches
    
    @pytest.mark.asyncio
    async def test_get_matches_by_duration_invalid_rounds(self, clean_test_session):
        """잘못된 라운드 수 처리 테스트"""
        # When & Then: 잘못된 라운드 수로 조회시 MatchValidationError 발생
        with pytest.raises(MatchValidationError, match="min_rounds must be a positive integer or None"):
            await match_service.get_matches_by_duration(clean_test_session, min_rounds=-1)
        
        with pytest.raises(MatchValidationError, match="max_rounds must be a positive integer or None"):
            await match_service.get_matches_by_duration(clean_test_session, max_rounds=0)
        
        with pytest.raises(MatchValidationError, match="min_rounds cannot be greater than max_rounds"):
            await match_service.get_matches_by_duration(clean_test_session, min_rounds=5, max_rounds=3)
    
    @pytest.mark.asyncio
    async def test_get_match_with_winner_loser_success(self, clean_test_session):
        """승자/패자 정보 조회 성공 테스트"""
        # Given: Mock 데이터 설정
        mock_result = {
            "match": AsyncMock(id=1),
            "winner": {"fighter": AsyncMock(name="Fighter A"), "result": "win"},
            "loser": {"fighter": AsyncMock(name="Fighter B"), "result": "loss"}
        }
        
        with patch('match.services.match_repo.get_match_with_winner_loser', return_value=mock_result):
            # When: 매치 승부 결과 조회
            result = await match_service.get_match_with_winner_loser(clean_test_session, 1)
        
        # Then: 승부 결과 반환
        assert result == mock_result
        assert "winner" in result
        assert "loser" in result
    
    @pytest.mark.asyncio
    async def test_get_match_with_winner_loser_not_found(self, clean_test_session):
        """존재하지 않는 매치 승부 결과 조회 테스트"""
        # Given: Repository에서 None 반환
        with patch('match.services.match_repo.get_match_with_winner_loser', return_value=None):
            
            # When & Then: MatchNotFoundError 발생
            with pytest.raises(MatchNotFoundError, match="Match not found with id"):
                await match_service.get_match_with_winner_loser(clean_test_session, 99999)
    
    @pytest.mark.asyncio
    async def test_get_matches_between_fighters_success(self, clean_test_session):
        """파이터 간 대결 조회 성공 테스트"""
        # Given: Mock 데이터 설정
        mock_matches = [
            AsyncMock(id=1, event_id=1),
            AsyncMock(id=2, event_id=2)
        ]
        
        with patch('match.services.match_repo.get_matches_between_fighters', return_value=mock_matches):
            # When: 두 파이터 간 대결 조회
            result = await match_service.get_matches_between_fighters(clean_test_session, 1, 2)
        
        # Then: 매치 리스트 반환
        assert result == mock_matches
    
    @pytest.mark.asyncio
    async def test_get_matches_between_fighters_invalid_ids(self, clean_test_session):
        """잘못된 파이터 ID 처리 테스트"""
        # When & Then: 잘못된 파이터 ID로 조회시 MatchValidationError 발생
        with pytest.raises(MatchValidationError, match="fighter_id_1 must be a positive integer"):
            await match_service.get_matches_between_fighters(clean_test_session, -1, 2)
        
        with pytest.raises(MatchValidationError, match="fighter_id_2 must be a positive integer"):
            await match_service.get_matches_between_fighters(clean_test_session, 1, 0)
        
        with pytest.raises(MatchValidationError, match="fighter_id_1 and fighter_id_2 cannot be the same"):
            await match_service.get_matches_between_fighters(clean_test_session, 1, 1)


if __name__ == "__main__":
    print("Match Services 테스트 실행...")
    print("✅ 비즈니스 로직 레이어 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/match/test_services.py -v")