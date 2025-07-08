"""
Fighter Composer 테스트
composition/fighter_composer.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta

from composition import fighter_composer
from composition.dto import (
    FighterMatchRecordDTO, FighterVsRecordDTO, FighterVsRecordItemDTO, MatchInfoDTO,
    FighterTotalStatsDTO, FighterStatsComparisonDTO, FighterComparisonItemDTO, 
    FighterComparisonStatsDTO, TopStatFighterDTO, FighterCareerTimelineDTO,
    FighterVsStanceAnalysisDTO, DivisionalEliteComparisonDTO, FightOutcomePredictionDTO
)
from event.models import EventSchema
from match.models import MatchSchema
from fighter.models import FighterSchema


class TestFighterComposerWithTestDB:
    """Test DB를 사용한 Fighter Composer 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_all_matches_success(self, sample_fighter, clean_test_session):
        """파이터의 모든 매치 기록 조회 성공 테스트"""
        # When: 파이터의 모든 매치 조회
        result = await fighter_composer.get_fighter_all_matches(clean_test_session, sample_fighter.id)
        
        # Then: FighterMatchRecordDTO 리스트 반환
        assert isinstance(result, list)
        for match_record in result:
            assert isinstance(match_record, FighterMatchRecordDTO)
            assert match_record.match is not None
            assert match_record.result in ["Win", "Loss", "Draw"]
    
    @pytest.mark.asyncio
    async def test_get_fighter_all_matches_nonexistent_fighter(self, clean_test_session):
        """존재하지 않는 파이터의 매치 조회 테스트"""
        # When: 존재하지 않는 파이터 조회
        result = await fighter_composer.get_fighter_all_matches(clean_test_session, 999)
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_fighter_total_stat_success(self, sample_fighter, clean_test_session):
        """파이터 종합 통계 조회 성공 테스트"""
        # When: 파이터 종합 통계 조회
        result = await fighter_composer.get_fighter_total_stat(clean_test_session, sample_fighter.id)
        
        # Then: FighterTotalStatsDTO 반환
        if result:  # 통계가 있는 경우만 검증
            assert isinstance(result, FighterTotalStatsDTO)
            assert result.fighter.id == sample_fighter.id
            assert isinstance(result.basic_stats, dict)
            assert isinstance(result.sig_str_stats, dict)
            assert isinstance(result.accuracy, dict)
    
    @pytest.mark.asyncio
    async def test_get_fighter_total_stat_nonexistent_fighter(self, clean_test_session):
        """존재하지 않는 파이터의 통계 조회 테스트"""
        # When: 존재하지 않는 파이터 조회
        result = await fighter_composer.get_fighter_total_stat(clean_test_session, 999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_fighter_with_top_stat_success(self, clean_test_session):
        """특정 통계 상위 파이터 조회 성공 테스트"""
        # When: 특정 통계에서 상위 파이터들 조회
        result = await fighter_composer.get_fighter_with_top_stat(clean_test_session, "wins", limit=5)
        
        # Then: TopStatFighterDTO 리스트 반환
        assert isinstance(result, list)
        assert len(result) <= 5
        
        for stat_fighter in result:
            assert isinstance(stat_fighter, TopStatFighterDTO)
            assert stat_fighter.rank >= 1
            assert stat_fighter.stat_name == "wins"
            assert stat_fighter.total_stat >= 0


class TestFighterComposerWithMocks:
    """Mock을 사용한 Fighter Composer 단위 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fighter_all_matches_with_mock_data(self, clean_test_session):
        """Mock 데이터로 파이터 매치 기록 조회 테스트"""
        # Given: Mock 데이터 설정
        mock_event = EventSchema(
            id=1, name="UFC Test Event", location="Vegas", event_date=date(2024, 1, 1),
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_match = MatchSchema(
            id=1, event_id=1, method="Decision", result_round=3, is_main_event=False,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_fighter_match = AsyncMock()
        mock_fighter_match.match_id = 1
        mock_fighter_match.result = "Win"
        
        mock_opponent = AsyncMock()
        mock_opponent.fighter_id = 2
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.fighter_composer.get_fighters_matches', return_value=[mock_fighter_match]), \
             patch('composition.fighter_composer.get_match_by_id', return_value=mock_match), \
             patch('composition.fighter_composer.get_event_by_id', return_value=mock_event), \
             patch('composition.fighter_composer.get_fighter_match_by_match_id', return_value=[mock_fighter_match, mock_opponent]), \
             patch('composition.fighter_composer.WeightClassSchema.get_name_by_id', return_value="Lightweight"):
            
            result = await fighter_composer.get_fighter_all_matches(clean_test_session, 1)
        
        # Then: 올바른 DTO 구조 반환
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], FighterMatchRecordDTO)
        assert result[0].result == "Win"
        assert result[0].weight_class == "Lightweight"
    
    @pytest.mark.asyncio
    async def test_get_fighter_total_stat_with_mock_data(self, clean_test_session):
        """Mock 데이터로 파이터 종합 통계 조회 테스트"""
        # Given: Mock 데이터 설정
        mock_fighter = FighterSchema(
            id=1, name="Test Fighter", wins=10, losses=2, draws=0,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_basic_stats = {
            "total_fights": 12,
            "wins": 10,
            "knockdowns": 5
        }
        
        mock_sig_str_stats = {
            "sig_str_landed": 150,
            "sig_str_attempted": 200
        }
        
        mock_accuracy = {
            "overall_accuracy": 75.0,
            "head_accuracy": 45.0
        }
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.fighter_composer.get_fighter_by_id', return_value=mock_fighter), \
             patch('composition.fighter_composer.get_fighter_basic_stats_aggregate', return_value=mock_basic_stats), \
             patch('composition.fighter_composer.get_fighter_sig_str_stats_aggregate', return_value=mock_sig_str_stats), \
             patch('composition.fighter_composer.calculate_fighter_accuracy', return_value=mock_accuracy):
            
            result = await fighter_composer.get_fighter_total_stat(clean_test_session, 1)
        
        # Then: 올바른 통계 DTO 반환
        assert isinstance(result, FighterTotalStatsDTO)
        assert result.fighter.name == "Test Fighter"
        assert result.basic_stats["wins"] == 10
        assert result.sig_str_stats["sig_str_landed"] == 150
        assert result.accuracy["overall_accuracy"] == 75.0
    
    @pytest.mark.asyncio
    async def test_compare_fighters_stats_with_mock_data(self, clean_test_session):
        """Mock 데이터로 파이터 통계 비교 테스트"""
        # Given: Mock 데이터 설정
        fighter1 = FighterSchema(
            id=1, name="Fighter One", wins=15, losses=2, draws=0,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        fighter2 = FighterSchema(
            id=2, name="Fighter Two", wins=8, losses=1, draws=0,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_f1_basic = {"knockdowns": 10, "takedowns": 5}
        mock_f1_sig_str = {"sig_str_landed": 200}
        mock_f1_accuracy = {"overall_accuracy": 80.0}
        
        mock_f2_basic = {"knockdowns": 6, "takedowns": 8}
        mock_f2_sig_str = {"sig_str_landed": 150}
        mock_f2_accuracy = {"overall_accuracy": 70.0}
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.fighter_composer.get_fighter_by_id', side_effect=[fighter1, fighter2]), \
             patch('composition.fighter_composer.get_fighter_basic_stats_aggregate', side_effect=[mock_f1_basic, mock_f2_basic]), \
             patch('composition.fighter_composer.get_fighter_sig_str_stats_aggregate', side_effect=[mock_f1_sig_str, mock_f2_sig_str]), \
             patch('composition.fighter_composer.calculate_fighter_accuracy', side_effect=[mock_f1_accuracy, mock_f2_accuracy]):
            
            result = await fighter_composer.compare_fighters_stats(clean_test_session, 1, 2)
        
        # Then: 올바른 비교 DTO 반환
        assert isinstance(result, FighterStatsComparisonDTO)
        assert result.fighter1.info.name == "Fighter One"
        assert result.fighter2.info.name == "Fighter Two"
        assert isinstance(result.comparison.stats, dict)
        assert isinstance(result.comparison.accuracy, dict)
    
    @pytest.mark.asyncio
    async def test_get_fighter_career_timeline_with_mock_data(self, clean_test_session):
        """Mock 데이터로 파이터 커리어 타임라인 조회 테스트"""
        # Given: Mock 데이터 설정
        mock_matches = [
            FighterMatchRecordDTO(
                event=EventSchema(id=1, name="UFC 100", event_date=date(2023, 1, 1), created_at=datetime.now(), updated_at=datetime.now()),
                opponent={"id": 2, "name": "Opponent"},
                match=MatchSchema(id=1, event_id=1, is_main_event=True, created_at=datetime.now(), updated_at=datetime.now()),
                result="Win",
                weight_class="Lightweight"
            ),
            FighterMatchRecordDTO(
                event=EventSchema(id=2, name="UFC 101", event_date=date(2023, 2, 1), created_at=datetime.now(), updated_at=datetime.now()),
                opponent={"id": 3, "name": "Another Opponent"},
                match=MatchSchema(id=2, event_id=2, is_main_event=False, created_at=datetime.now(), updated_at=datetime.now()),
                result="Win",
                weight_class="Lightweight"
            )
        ]
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.fighter_composer.get_fighter_all_matches', return_value=mock_matches):
            result = await fighter_composer.get_fighter_career_timeline(clean_test_session, 1)
        
        # Then: 올바른 커리어 타임라인 DTO 반환
        assert isinstance(result, FighterCareerTimelineDTO)
        assert result.fighter_id == 1
        assert len(result.career_timeline) == 2
        assert result.summary.total_fights == 2
        assert result.summary.wins == 2
        assert result.summary.main_events == 1
        assert len(result.summary.career_highlights) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_fighter_vs_style_with_mock_data(self, clean_test_session):
        """Mock 데이터로 파이터 대 스탠스 분석 테스트"""
        # Given: Mock 데이터 설정
        mock_fighter = FighterSchema(
            id=1, name="Orthodox Fighter", stance="Orthodox",
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_opponent = FighterSchema(
            id=2, name="Southpaw Opponent", stance="Southpaw",
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_vs_record = [
            FighterVsRecordDTO(
                match_info=MatchInfoDTO(
                    event_name="UFC Test",
                    event_date=date(2023, 1, 1),
                    is_main_event=False,
                    order=1,
                    match_id=1,
                    method="Decision",
                    result_round=3,
                    time="15:00",
                    weight_class="Lightweight"
                ),
                fighter1=FighterVsRecordItemDTO(
                    info=mock_fighter,
                    result="Win",
                    basic_stats={},
                    sig_str_stats={}
                ),
                fighter2=FighterVsRecordItemDTO(
                    info=mock_opponent,
                    result="Loss",
                    basic_stats={},
                    sig_str_stats={}
                )
            )
        ]
        
        # When: Mock을 사용하여 함수 호출
        with patch('fighter.repositories.get_fighter_by_id', return_value=mock_fighter), \
             patch('composition.repositories.get_all_opponents', return_value=[mock_opponent]), \
             patch('composition.fighter_composer.get_fighter_vs_record', return_value=mock_vs_record):
            
            result = await fighter_composer.analyze_fighter_vs_style(clean_test_session, 1, "Southpaw")
        
        # Then: 올바른 스탠스 분석 DTO 반환
        assert isinstance(result, FighterVsStanceAnalysisDTO)
        assert result.fighter.name == "Orthodox Fighter"
        assert result.opponent_stance == "Southpaw"
        assert result.analysis.total_fights_vs_stance == 1
        assert result.analysis.wins == 1
    
    @pytest.mark.asyncio
    async def test_get_divisional_elite_comparison_with_mock_data(self, clean_test_session):
        """Mock 데이터로 체급 엘리트 비교 테스트"""
        # Given: Mock 데이터 설정
        mock_fighters = [
            FighterSchema(id=1, name="Champion", created_at=datetime.now(), updated_at=datetime.now()),
            FighterSchema(id=2, name="Contender", created_at=datetime.now(), updated_at=datetime.now())
        ]
        
        mock_fighter_stats = FighterTotalStatsDTO(
            fighter=mock_fighters[0],
            basic_stats={"knockdowns": 10},
            sig_str_stats={"sig_str_landed": 200},
            accuracy={"overall_accuracy": 80.0}
        )
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.fighter_composer.WeightClassSchema.get_name_by_id', return_value="Lightweight"), \
             patch('fighter.repositories.get_fighters_by_weight_class_ranking', return_value=mock_fighters), \
             patch('composition.fighter_composer.get_fighter_total_stat', return_value=mock_fighter_stats):
            
            result = await fighter_composer.get_divisional_elite_comparison(clean_test_session, 1, top_n=2)
        
        # Then: 올바른 체급 비교 DTO 반환
        assert isinstance(result, DivisionalEliteComparisonDTO)
        assert result.weight_class == "Lightweight"
        assert result.weight_class_id == 1
        assert len(result.elite_fighters) == 2
        assert result.division_depth == 2
    
    @pytest.mark.asyncio
    async def test_predict_fight_outcome_with_mock_data(self, clean_test_session):
        """Mock 데이터로 경기 결과 예측 테스트"""
        # Given: Mock 데이터 설정
        # Mock 파이터 생성
        fighter1 = FighterSchema(id=1, name="Fighter 1", wins=10, losses=2, draws=0, created_at=datetime.now(), updated_at=datetime.now())
        fighter2 = FighterSchema(id=2, name="Fighter 2", wins=8, losses=3, draws=0, created_at=datetime.now(), updated_at=datetime.now())
        
        mock_comparison = FighterStatsComparisonDTO(
            fighter1=FighterComparisonItemDTO(
                info=fighter1, 
                basic_stats={"knockdowns": 5}, 
                sig_str_stats={"sig_str_landed": 100}, 
                accuracy={"overall_accuracy": 80.0}
            ),
            fighter2=FighterComparisonItemDTO(
                info=fighter2, 
                basic_stats={"knockdowns": 3}, 
                sig_str_stats={"sig_str_landed": 80}, 
                accuracy={"overall_accuracy": 70.0}
            ),
            comparison=FighterComparisonStatsDTO(stats={}, accuracy={})
        )
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.fighter_composer.compare_fighters_stats', return_value=mock_comparison), \
             patch('composition.fighter_composer.get_fighter_vs_record', return_value=[]), \
             patch('composition.repositories.get_fighters_common_opponents', return_value=[]):
            
            result = await fighter_composer.predict_fight_outcome(clean_test_session, 1, 2)
        
        # Then: 올바른 예측 DTO 반환
        assert isinstance(result, FightOutcomePredictionDTO)
        assert result.matchup.fighter1.name == "Fighter 1"
        assert result.matchup.fighter2.name == "Fighter 2"
        assert 0 <= result.prediction.fighter1_win_probability <= 100
        assert 0 <= result.prediction.fighter2_win_probability <= 100
        assert result.prediction.confidence in ["high", "medium", "low"]


class TestFighterComposerErrorHandling:
    """Fighter Composer 에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_compare_fighters_stats_invalid_fighters(self, clean_test_session):
        """존재하지 않는 파이터들 비교 테스트"""
        # Given: 존재하지 않는 파이터들
        with patch('composition.fighter_composer.get_fighter_by_id', side_effect=[None, None]):
            # When & Then: ValueError 발생
            with pytest.raises(ValueError, match="One or both fighters not found"):
                await fighter_composer.compare_fighters_stats(clean_test_session, 999, 998)
    
    @pytest.mark.asyncio
    async def test_get_fighter_with_top_stat_invalid_stat(self, clean_test_session):
        """유효하지 않은 통계 항목으로 상위 파이터 조회 테스트"""
        # When & Then: ValueError 발생
        with pytest.raises(ValueError, match="Invalid stat_name"):
            await fighter_composer.get_fighter_with_top_stat(clean_test_session, "invalid_stat")
    
    @pytest.mark.asyncio
    async def test_analyze_fighter_vs_style_fighter_not_found(self, clean_test_session):
        """존재하지 않는 파이터의 스탠스 분석 테스트"""
        # Given: 파이터가 None
        with patch('composition.fighter_composer.get_fighter_by_id', return_value=None):
            # When: 스탠스 분석
            result = await fighter_composer.analyze_fighter_vs_style(clean_test_session, 999, "Orthodox")
        
        # Then: 적절한 에러 DTO 반환
        assert isinstance(result, FighterVsStanceAnalysisDTO)
        assert result.fighter.name == "Not Found"
        assert result.analysis.total_fights_vs_stance == 0
    
    @pytest.mark.asyncio
    async def test_get_divisional_elite_comparison_invalid_weight_class(self, clean_test_session):
        """유효하지 않은 체급의 엘리트 비교 테스트"""
        # Given: 유효하지 않은 체급
        with patch('composition.fighter_composer.WeightClassSchema.get_name_by_id', return_value=None):
            # When: 체급 엘리트 비교
            result = await fighter_composer.get_divisional_elite_comparison(clean_test_session, 999)
        
        # Then: 빈 결과 DTO 반환
        assert isinstance(result, DivisionalEliteComparisonDTO)
        assert result.weight_class == "Unknown"
        assert len(result.elite_fighters) == 0
        assert result.division_depth == 0
    
    @pytest.mark.asyncio
    async def test_predict_fight_outcome_comparison_failed(self, clean_test_session):
        """파이터 비교 실패 시 경기 예측 테스트"""
        # Given: 비교 실패
        with patch('composition.fighter_composer.compare_fighters_stats', return_value=None):
            # When: 경기 예측
            result = await fighter_composer.predict_fight_outcome(clean_test_session, 1, 2)
        
        # Then: 더미 예측 DTO 반환
        assert isinstance(result, FightOutcomePredictionDTO)
        assert result.prediction.fighter1_win_probability == 50.0
        assert result.prediction.fighter2_win_probability == 50.0
        assert result.prediction.confidence == "low"
    
    @pytest.mark.asyncio
    async def test_get_fighter_career_timeline_no_matches(self, clean_test_session):
        """매치가 없는 파이터의 커리어 타임라인 테스트"""
        # Given: 매치가 없는 파이터
        with patch('composition.fighter_composer.get_fighter_all_matches', return_value=[]):
            # When: 커리어 타임라인 조회
            result = await fighter_composer.get_fighter_career_timeline(clean_test_session, 1)
        
        # Then: 빈 타임라인 DTO 반환
        assert isinstance(result, FighterCareerTimelineDTO)
        assert result.fighter_id == 1
        assert len(result.career_timeline) == 0
        assert result.summary.total_fights == 0
        assert result.summary.wins == 0
        assert result.summary.losses == 0


if __name__ == "__main__":
    print("Fighter Composer 테스트 실행...")
    print("✅ 파이터 분석 비즈니스 로직 완전 테스트!")
    print("\n테스트 실행:")
    print("cd src && uv run pytest tests/composer/test_fighter_composer.py -v")