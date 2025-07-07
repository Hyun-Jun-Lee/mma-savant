"""
Match Repositories 테스트
match/repositories.py의 모든 repository 함수에 대한 포괄적인 테스트
"""
import pytest

from match import repositories as match_repo
from match.models import MatchSchema, FighterMatchSchema, BasicMatchStatSchema, SigStrMatchStatSchema


class TestMatchRepositoryWithTestDB:
    """Test DB를 사용한 Match Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_match_by_id_existing(self, sample_match, clean_test_session):
        """존재하는 매치 ID로 조회 테스트"""
        # When: Repository 함수 호출
        result = await match_repo.get_match_by_id(clean_test_session, sample_match.id)
        
        # Then: 올바른 MatchSchema 반환
        assert result is not None
        assert isinstance(result, MatchSchema)
        assert result.id == sample_match.id
        assert result.event_id == sample_match.event_id
        assert result.weight_class_id == sample_match.weight_class_id
        assert result.method == "Decision - Unanimous"
        assert result.result_round == 3
        assert result.time == "15:00"
        assert result.order == 1
        assert result.is_main_event is False
    
    @pytest.mark.asyncio
    async def test_get_match_by_id_nonexistent(self, clean_test_session):
        """존재하지 않는 매치 ID로 조회 테스트"""
        # When: 존재하지 않는 ID로 조회
        result = await match_repo.get_match_by_id(clean_test_session, 99999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_matches_by_event_id(self, multiple_matches_for_event, clean_test_session):
        """이벤트 ID로 매치들 조회 테스트"""
        # Given: multiple_matches_for_event fixture 사용
        event, matches = multiple_matches_for_event
        
        # When: 이벤트 ID로 매치들 조회
        result = await match_repo.get_matches_by_event_id(clean_test_session, event.id)
        
        # Then: 모든 매치가 order 순으로 반환
        assert isinstance(result, list)
        assert len(result) == 3
        
        # order 순서대로 정렬되어 있는지 확인
        assert result[0].order == 1
        assert result[1].order == 2
        assert result[2].order == 3
        
        # 메인 이벤트가 마지막에 있는지 확인
        assert result[2].is_main_event is True
        assert result[0].is_main_event is False
        assert result[1].is_main_event is False
        
        # 모든 결과가 MatchSchema 타입인지 확인
        for match in result:
            assert isinstance(match, MatchSchema)
            assert match.event_id == event.id
    
    @pytest.mark.asyncio
    async def test_get_matches_between_fighters(self, fighters_with_multiple_matches, clean_test_session):
        """두 파이터 간의 모든 매치 조회 테스트"""
        # Given: fighters_with_multiple_matches fixture 사용
        fighters, matches, fighter_matches = fighters_with_multiple_matches
        
        # When: 두 파이터 간 매치 조회
        result = await match_repo.get_matches_between_fighters(
            clean_test_session, fighters[0].id, fighters[1].id
        )
        
        # Then: 모든 매치가 반환
        assert isinstance(result, list)
        assert len(result) == 3
        
        # 모든 결과가 MatchSchema 타입인지 확인
        for match in result:
            assert isinstance(match, MatchSchema)
        
        # 매치 방법들이 올바른지 확인
        methods = [match.method for match in result]
        assert "Decision" in methods
        assert "KO/TKO" in methods
        assert "Submission" in methods


class TestMatchStatisticsRepositoryWithTestDB:
    """Test DB를 사용한 매치 통계 Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_basic_match_stats(self, match_with_statistics, clean_test_session):
        """기본 매치 통계 조회 테스트"""
        # Given: match_with_statistics fixture 사용
        match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics
        
        # When: 첫 번째 파이터의 기본 통계 조회
        result = await match_repo.get_basic_match_stats(
            clean_test_session, fighters[0].id, match.id
        )
        
        # Then: 올바른 기본 통계 반환
        assert result is not None
        assert isinstance(result, BasicMatchStatSchema)
        assert result.fighter_match_id == fighter_matches[0].id
        assert result.knockdowns == 1
        assert result.control_time_seconds == 240
        assert result.submission_attempts == 2
        assert result.sig_str_landed == 45
        assert result.sig_str_attempted == 75
        assert result.td_landed == 3
        assert result.td_attempted == 6
        assert result.round == 3
    
    @pytest.mark.asyncio
    async def test_get_sig_str_match_stats(self, match_with_statistics, clean_test_session):
        """스트라이크 상세 통계 조회 테스트"""
        # Given: match_with_statistics fixture 사용
        match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics
        
        # When: 첫 번째 파이터의 스트라이크 통계 조회
        result = await match_repo.get_sig_str_match_stats(
            clean_test_session, fighters[0].id, match.id
        )
        
        # Then: 올바른 스트라이크 통계 반환
        assert result is not None
        assert isinstance(result, SigStrMatchStatSchema)
        assert result.fighter_match_id == fighter_matches[0].id
        assert result.head_strikes_landed == 25
        assert result.head_strikes_attempts == 40
        assert result.body_strikes_landed == 15
        assert result.body_strikes_attempts == 25
        assert result.leg_strikes_landed == 5
        assert result.leg_strikes_attempts == 10
        assert result.takedowns_landed == 3
        assert result.takedowns_attempts == 6
        assert result.round == 3
    
    @pytest.mark.asyncio
    async def test_get_basic_match_stats_nonexistent(self, clean_test_session):
        """존재하지 않는 파이터/매치 조합 기본 통계 조회 테스트"""
        # When: 존재하지 않는 조합으로 조회
        result = await match_repo.get_basic_match_stats(clean_test_session, 99999, 99999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_sig_str_match_stats_nonexistent(self, clean_test_session):
        """존재하지 않는 파이터/매치 조합 스트라이크 통계 조회 테스트"""
        # When: 존재하지 않는 조합으로 조회
        result = await match_repo.get_sig_str_match_stats(clean_test_session, 99999, 99999)
        
        # Then: None 반환
        assert result is None


class TestFighterMatchRepositoryWithTestDB:
    """Test DB를 사용한 FighterMatch Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighters_matches(self, fighters_with_multiple_matches, clean_test_session):
        """파이터의 모든 매치 조회 테스트"""
        # Given: fighters_with_multiple_matches fixture 사용
        fighters, matches, fighter_matches = fighters_with_multiple_matches
        
        # When: 첫 번째 파이터의 모든 매치 조회
        result = await match_repo.get_fighters_matches(clean_test_session, fighters[0].id)
        
        # Then: 모든 파이터 매치가 반환
        assert isinstance(result, list)
        assert len(result) == 3
        
        # 모든 결과가 FighterMatchSchema 타입인지 확인
        for fighter_match in result:
            assert isinstance(fighter_match, FighterMatchSchema)
            assert fighter_match.fighter_id == fighters[0].id
        
        # 결과 확인 - 첫 번째 파이터가 모든 경기에서 승리
        results = [fm.result for fm in result]
        assert all(r == "win" for r in results)
    
    @pytest.mark.asyncio
    async def test_get_fighters_matches_with_limit(self, fighters_with_multiple_matches, clean_test_session):
        """파이터의 매치 조회 제한 테스트"""
        # Given: fighters_with_multiple_matches fixture 사용
        fighters, matches, fighter_matches = fighters_with_multiple_matches
        
        # When: 첫 번째 파이터의 최근 2개 매치만 조회
        result = await match_repo.get_fighters_matches(clean_test_session, fighters[0].id, limit=2)
        
        # Then: 2개의 파이터 매치만 반환
        assert isinstance(result, list)
        assert len(result) == 2
        
        # 모든 결과가 FighterMatchSchema 타입인지 확인
        for fighter_match in result:
            assert isinstance(fighter_match, FighterMatchSchema)
            assert fighter_match.fighter_id == fighters[0].id
    
    @pytest.mark.asyncio
    async def test_get_fighter_match_by_match_id(self, match_with_fighters, clean_test_session):
        """매치 ID로 파이터 매치 관계 조회 테스트"""
        # Given: match_with_fighters fixture 사용
        match, fighters, fighter_matches = match_with_fighters
        
        # When: 매치 ID로 파이터 매치 관계 조회
        result = await match_repo.get_fighter_match_by_match_id(clean_test_session, match.id)
        
        # Then: 두 파이터의 매치 관계가 반환
        assert isinstance(result, list)
        assert len(result) == 2
        
        # 모든 결과가 FighterMatchSchema 타입인지 확인
        for fighter_match in result:
            assert isinstance(fighter_match, FighterMatchSchema)
            assert fighter_match.match_id == match.id
        
        # 결과 확인 (winner와 loser)
        results = [fm.result for fm in result]
        assert "win" in results
        assert "loss" in results
    
    @pytest.mark.asyncio
    async def test_get_match_fighter_mapping(self, match_with_fighters, clean_test_session):
        """매치 파이터 매핑 조회 테스트"""
        # Given: match_with_fighters fixture 사용
        match, fighters, fighter_matches = match_with_fighters
        
        # When: 매치 파이터 매핑 조회 (매개변수 없음)
        result = await match_repo.get_match_fighter_mapping(clean_test_session)
        
        # Then: detail_url을 키로 하는 매핑 반환
        assert isinstance(result, dict)
        
        # match.detail_url이 키로 있는지 확인
        if match.detail_url:
            assert match.detail_url in result
            match_mapping = result[match.detail_url]
            assert isinstance(match_mapping, dict)
            
            # 파이터 ID와 FighterMatchSchema 매핑 확인
            for fighter_id, fighter_match_schema in match_mapping.items():
                assert isinstance(fighter_id, int)
                assert isinstance(fighter_match_schema, FighterMatchSchema)
                assert fighter_match_schema.fighter_id == fighter_id
                assert fighter_match_schema.match_id == match.id


class TestAggregateStatisticsRepositoryWithTestDB:
    """Test DB를 사용한 집계 통계 Repository 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_basic_stats_aggregate(self, match_with_statistics, clean_test_session):
        """파이터 기본 통계 집계 테스트"""
        # Given: match_with_statistics fixture 사용 (추가 매치 데이터 필요하면 생성)
        match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics
        
        # When: 첫 번째 파이터의 기본 통계 집계 조회
        result = await match_repo.get_fighter_basic_stats_aggregate(clean_test_session, fighters[0].id)
        
        # Then: 집계된 통계 반환
        assert result is not None
        assert isinstance(result, dict)
        
        # 기본 집계 필드들 확인 (실제 repository에서 반환하는 필드명 사용)
        expected_fields = [
            'match_count', 'knockdowns', 'control_time_seconds',
            'submission_attempts', 'sig_str_landed', 'sig_str_attempted',
            'total_str_landed', 'total_str_attempted', 'td_landed', 'td_attempted'
        ]
        
        for field in expected_fields:
            assert field in result
            assert isinstance(result[field], (int, type(None)))
        
        # 실제 값 확인 (현재 1개 매치)
        assert result['match_count'] == 1
        assert result['knockdowns'] == 1
        assert result['control_time_seconds'] == 240
        assert result['submission_attempts'] == 2
    
    @pytest.mark.asyncio
    async def test_get_fighter_sig_str_stats_aggregate(self, match_with_statistics, clean_test_session):
        """파이터 스트라이크 통계 집계 테스트"""
        # Given: match_with_statistics fixture 사용
        match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics
        
        # When: 첫 번째 파이터의 스트라이크 통계 집계 조회
        result = await match_repo.get_fighter_sig_str_stats_aggregate(clean_test_session, fighters[0].id)
        
        # Then: 집계된 스트라이크 통계 반환
        assert result is not None
        assert isinstance(result, dict)
        
        # 스트라이크 집계 필드들 확인 (실제 repository에서 반환하는 필드명 사용)
        expected_fields = [
            'match_count', 'head_strikes_landed', 'head_strikes_attempts',
            'body_strikes_landed', 'body_strikes_attempts',
            'leg_strikes_landed', 'leg_strikes_attempts',
            'takedowns_landed', 'takedowns_attempts',
            'clinch_strikes_landed', 'clinch_strikes_attempts',
            'ground_strikes_landed', 'ground_strikes_attempts'
        ]
        
        for field in expected_fields:
            assert field in result
            assert isinstance(result[field], (int, type(None)))
        
        # 실제 값 확인 (현재 1개 매치)
        assert result['match_count'] == 1
        assert result['head_strikes_landed'] == 25
        assert result['head_strikes_attempts'] == 40
        assert result['body_strikes_landed'] == 15
        assert result['takedowns_landed'] == 3
    
    @pytest.mark.asyncio
    async def test_get_fighter_basic_stats_aggregate_no_matches(self, sample_fighter, clean_test_session):
        """매치가 없는 파이터 기본 통계 집계 테스트"""
        # When: 매치가 없는 파이터의 기본 통계 집계 조회
        result = await match_repo.get_fighter_basic_stats_aggregate(clean_test_session, sample_fighter.id)
        
        # Then: 모든 값이 0 또는 None
        assert result is not None
        assert result['match_count'] == 0 or result['match_count'] is None
        
        # 다른 모든 통계도 0 또는 None이어야 함
        for key, value in result.items():
            assert value == 0 or value is None
    
    @pytest.mark.asyncio 
    async def test_get_fighter_sig_str_stats_aggregate_no_matches(self, sample_fighter, clean_test_session):
        """매치가 없는 파이터 스트라이크 통계 집계 테스트"""
        # When: 매치가 없는 파이터의 스트라이크 통계 집계 조회
        result = await match_repo.get_fighter_sig_str_stats_aggregate(clean_test_session, sample_fighter.id)
        
        # Then: 모든 값이 0 또는 None
        assert result is not None
        assert result['match_count'] == 0 or result['match_count'] is None
        
        # 다른 모든 통계도 0 또는 None이어야 함
        for key, value in result.items():
            assert value == 0 or value is None


class TestRepositoryErrorHandlingWithTestDB:
    """Repository 에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_matches_by_nonexistent_event(self, clean_test_session):
        """존재하지 않는 이벤트 ID로 매치 조회 테스트"""
        # When: 존재하지 않는 이벤트 ID로 조회
        result = await match_repo.get_matches_by_event_id(clean_test_session, 99999)
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_fighters_matches_nonexistent_fighter(self, clean_test_session):
        """존재하지 않는 파이터 ID로 매치 조회 테스트"""
        # When: 존재하지 않는 파이터 ID로 조회
        result = await match_repo.get_fighters_matches(clean_test_session, 99999)
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_match_fighter_mapping_no_matches(self, clean_test_session):
        """매치가 없을 때 매치 파이터 매핑 조회 테스트"""
        # When: 매치가 없는 상태에서 조회
        result = await match_repo.get_match_fighter_mapping(clean_test_session)
        
        # Then: 빈 딕셔너리 반환
        assert isinstance(result, dict)
        assert len(result) == 0


class TestNewMatchRepositoryWithTestDB:
    """새로 추가된 Match Repository 함수들의 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_match_with_winner_loser(self, match_with_fighters, clean_test_session):
        """매치의 승자/패자 정보 조회 테스트"""
        # Given: match_with_fighters fixture 사용
        match, fighters, fighter_matches = match_with_fighters
        
        # When: 매치의 승자/패자 정보 조회
        result = await match_repo.get_match_with_winner_loser(clean_test_session, match.id)
        
        # Then: 매치 정보와 승자/패자 정보가 반환
        assert result is not None
        assert isinstance(result, dict)
        assert "match" in result
        assert "fighters" in result
        assert "winner" in result
        assert "loser" in result
        
        # 매치 정보 확인
        assert isinstance(result["match"], MatchSchema)
        assert result["match"].id == match.id
        
        # 파이터 정보 확인 (2명)
        assert isinstance(result["fighters"], list)
        assert len(result["fighters"]) == 2
        
        # 승자 정보 확인
        winner = result["winner"]
        assert winner is not None
        assert winner["result"].lower() == "win"
        assert "fighter" in winner
        
        # 패자 정보 확인
        loser = result["loser"]
        assert loser is not None
        assert loser["result"].lower() == "loss"
        assert "fighter" in loser
        
        # 승자와 패자가 다른 파이터인지 확인
        assert winner["fighter"].id != loser["fighter"].id
    
    @pytest.mark.asyncio
    async def test_get_match_with_winner_loser_nonexistent(self, clean_test_session):
        """존재하지 않는 매치의 승자/패자 정보 조회 테스트"""
        # When: 존재하지 않는 매치 ID로 조회
        result = await match_repo.get_match_with_winner_loser(clean_test_session, 99999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_match_with_participants(self, match_with_fighters, clean_test_session):
        """매치 참여자 정보 조회 테스트"""
        # Given: match_with_fighters fixture 사용
        match, fighters, fighter_matches = match_with_fighters
        
        # When: 매치 참여자 정보 조회
        result = await match_repo.get_match_with_participants(clean_test_session, match.id)
        
        # Then: 매치 정보와 참여자 정보가 반환
        assert result is not None
        assert isinstance(result, dict)
        assert "match" in result
        assert "fighters" in result
        
        # 매치 정보 확인
        assert isinstance(result["match"], MatchSchema)
        assert result["match"].id == match.id
        
        # 파이터 정보 확인 (2명)
        assert isinstance(result["fighters"], list)
        assert len(result["fighters"]) == 2
        
        # 각 파이터 정보 확인
        for fighter_info in result["fighters"]:
            assert "fighter" in fighter_info
            assert "result" in fighter_info
            assert fighter_info["result"] in ["win", "loss", "draw"]
    
    @pytest.mark.asyncio
    async def test_get_match_with_participants_nonexistent(self, clean_test_session):
        """존재하지 않는 매치의 참여자 정보 조회 테스트"""
        # When: 존재하지 않는 매치 ID로 조회
        result = await match_repo.get_match_with_participants(clean_test_session, 99999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_match_statistics(self, match_with_statistics, clean_test_session):
        """매치 통계 정보 조회 테스트"""
        # Given: match_with_statistics fixture 사용
        match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics
        
        # When: 매치 통계 정보 조회
        result = await match_repo.get_match_statistics(clean_test_session, match.id)
        
        # Then: 매치 통계 정보가 반환
        assert result is not None
        assert isinstance(result, dict)
        assert "match_id" in result
        assert "fighter_stats" in result
        assert "combined_stats" in result
        
        # 매치 ID 확인
        assert result["match_id"] == match.id
        
        # 파이터별 통계 확인
        fighter_stats = result["fighter_stats"]
        assert isinstance(fighter_stats, list)
        assert len(fighter_stats) >= 1  # 최소 1명의 파이터 통계
        
        # 첫 번째 파이터 통계 확인
        first_fighter_stat = fighter_stats[0]
        assert "fighter_id" in first_fighter_stat
        assert "result" in first_fighter_stat
        assert "basic_stats" in first_fighter_stat
        assert "sig_str_stats" in first_fighter_stat
        
        # 합계 통계 확인
        combined_stats = result["combined_stats"]
        assert isinstance(combined_stats, dict)
        expected_combined_fields = [
            "total_strikes_attempted", "total_strikes_landed",
            "total_sig_str_attempted", "total_sig_str_landed",
            "total_takedowns_attempted", "total_takedowns_landed",
            "total_control_time", "total_knockdowns", "total_submission_attempts"
        ]
        
        for field in expected_combined_fields:
            assert field in combined_stats
            assert isinstance(combined_stats[field], (int, float))
            assert combined_stats[field] >= 0
    
    @pytest.mark.asyncio
    async def test_get_match_statistics_nonexistent(self, clean_test_session):
        """존재하지 않는 매치의 통계 정보 조회 테스트"""
        # When: 존재하지 않는 매치 ID로 조회
        result = await match_repo.get_match_statistics(clean_test_session, 99999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_matches_with_high_activity(self, match_with_statistics, clean_test_session):
        """높은 활동량 매치 조회 테스트"""
        # Given: match_with_statistics fixture 사용 (총 타격 시도가 있는 매치)
        match, fighters, fighter_matches, basic_stats, strike_stats = match_with_statistics
        
        # When: 낮은 임계값으로 높은 활동량 매치 조회 (테스트 데이터에 맞춤)
        result = await match_repo.get_matches_with_high_activity(
            clean_test_session, min_strikes=50, limit=10
        )
        
        # Then: 결과 반환 (조건에 맞는 매치가 있을 수 있음)
        assert isinstance(result, list)
        
        # 결과가 있다면 구조 확인
        if result:
            first_match = result[0]
            assert isinstance(first_match, dict)
            assert "match" in first_match
            assert "total_strikes" in first_match
            assert "activity_rating" in first_match
            
            # 매치 정보 확인
            assert isinstance(first_match["match"], MatchSchema)
            
            # 총 타격 수 확인
            assert isinstance(first_match["total_strikes"], (int, type(None)))
            assert first_match["total_strikes"] >= 50
            
            # 활동 등급 확인
            assert first_match["activity_rating"] in ["high", "very_high"]
    
    @pytest.mark.asyncio
    async def test_get_matches_by_finish_method(self, multiple_matches_for_event, clean_test_session):
        """피니시 방법별 매치 조회 테스트"""
        # Given: multiple_matches_for_event fixture 사용 (다양한 피니시 방법)
        event, matches = multiple_matches_for_event
        
        # When: Decision으로 끝난 매치들 조회
        result = await match_repo.get_matches_by_finish_method(
            clean_test_session, "Decision", limit=20
        )
        
        # Then: Decision 매치들이 반환
        assert isinstance(result, list)
        
        # 결과가 있다면 구조 확인
        if result:
            for match in result:
                assert isinstance(match, MatchSchema)
                assert "Decision" in match.method
    
    @pytest.mark.asyncio
    async def test_get_matches_by_finish_method_ko(self, clean_test_session):
        """KO 피니시 방법 매치 조회 테스트"""
        # When: KO로 끝난 매치들 조회
        result = await match_repo.get_matches_by_finish_method(
            clean_test_session, "KO", limit=20
        )
        
        # Then: 결과 반환 (KO 매치가 없을 수도 있음)
        assert isinstance(result, list)
        
        # 결과가 있다면 KO 방법 확인
        for match in result:
            assert isinstance(match, MatchSchema)
            assert "KO" in match.method
    
    @pytest.mark.asyncio
    async def test_get_matches_by_duration_long_fights(self, multiple_matches_for_event, clean_test_session):
        """긴 지속시간 매치 조회 테스트"""
        # Given: multiple_matches_for_event fixture 사용
        event, matches = multiple_matches_for_event
        
        # When: 3라운드 이상 지속된 매치들 조회
        result = await match_repo.get_matches_by_duration(
            clean_test_session, min_rounds=3, limit=20
        )
        
        # Then: 3라운드 이상 매치들이 반환
        assert isinstance(result, list)
        
        # 결과가 있다면 라운드 수 확인
        for match in result:
            assert isinstance(match, MatchSchema)
            if match.result_round is not None:
                assert match.result_round >= 3
    
    @pytest.mark.asyncio
    async def test_get_matches_by_duration_short_fights(self, clean_test_session):
        """짧은 지속시간 매치 조회 테스트"""
        # When: 1라운드에 끝난 매치들 조회
        result = await match_repo.get_matches_by_duration(
            clean_test_session, min_rounds=1, max_rounds=1, limit=20
        )
        
        # Then: 1라운드 매치들이 반환
        assert isinstance(result, list)
        
        # 결과가 있다면 라운드 수 확인
        for match in result:
            assert isinstance(match, MatchSchema)
            if match.result_round is not None:
                assert match.result_round == 1
    
    @pytest.mark.asyncio
    async def test_get_matches_by_duration_no_conditions(self, clean_test_session):
        """조건 없는 매치 지속시간 조회 테스트"""
        # When: 조건 없이 매치들 조회
        result = await match_repo.get_matches_by_duration(clean_test_session, limit=5)
        
        # Then: 최근 매치들이 반환
        assert isinstance(result, list)
        assert len(result) <= 5
        
        # 결과가 있다면 MatchSchema 타입 확인
        for match in result:
            assert isinstance(match, MatchSchema)


class TestNewMatchRepositoryEdgeCasesWithTestDB:
    """새로 추가된 함수들의 엣지 케이스 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_match_with_winner_loser_empty_fighters(self, sample_match, clean_test_session):
        """파이터가 없는 매치의 승자/패자 정보 조회 테스트"""
        # Given: 파이터가 연결되지 않은 매치
        
        # When: 파이터가 없는 매치의 승자/패자 정보 조회
        result = await match_repo.get_match_with_winner_loser(clean_test_session, sample_match.id)
        
        # Then: 매치 정보는 있지만 파이터 정보는 비어있음
        if result is not None:  # 매치는 존재하지만 파이터가 없을 수 있음
            assert isinstance(result, dict)
            assert "match" in result
            assert "fighters" in result
            assert isinstance(result["fighters"], list)
            assert len(result["fighters"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_matches_with_high_activity_no_matches(self, clean_test_session):
        """조건에 맞는 매치가 없는 경우의 높은 활동량 매치 조회 테스트"""
        # When: 매우 높은 임계값으로 조회 (조건에 맞는 매치가 없을 것)
        result = await match_repo.get_matches_with_high_activity(
            clean_test_session, min_strikes=10000, limit=10
        )
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_matches_by_finish_method_no_matches(self, clean_test_session):
        """조건에 맞는 매치가 없는 피니시 방법 조회 테스트"""
        # When: 존재하지 않는 피니시 방법으로 조회
        result = await match_repo.get_matches_by_finish_method(
            clean_test_session, "NonexistentMethod", limit=20
        )
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_matches_by_duration_impossible_conditions(self, clean_test_session):
        """불가능한 조건의 매치 지속시간 조회 테스트"""
        # When: 불가능한 조건으로 조회 (최소 라운드가 최대 라운드보다 큰 경우)
        result = await match_repo.get_matches_by_duration(
            clean_test_session, min_rounds=5, max_rounds=3, limit=20
        )
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0


if __name__ == "__main__":
    print("Match Repositories 테스트 실행...")
    print("✅ Test Database를 사용한 완전한 통합 테스트!")
    print("✅ 새로 추가된 Repository 함수들 테스트 포함!")
    print("\n테스트 실행:")
    print("uv run pytest tests/match/test_repositories.py -v")