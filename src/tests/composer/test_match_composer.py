"""
Match Composer 테스트
composition/match_composer.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta

from composition import match_composer
from composition.dto import (
    FOTNCandidatesDTO, CardQualityAnalysisDTO, ExcitingMatchDTO,
    ComebackPerformancesDTO, StyleClashAnalysisDTO, PerformanceOutliersDTO
)
from event.models import EventSchema
from match.models import MatchSchema
from fighter.models import FighterSchema


class TestMatchComposerWithTestDB:
    """Test DB를 사용한 Match Composer 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fight_of_the_night_candidates_success(self, sample_event, clean_test_session):
        """Fight of the Night 후보 분석 성공 테스트"""
        # When: 이벤트의 FOTN 후보 조회
        result = await match_composer.get_fight_of_the_night_candidates(clean_test_session, sample_event.id)
        
        # Then: FOTNCandidatesDTO 반환
        if result:  # 매치가 있는 경우만 검증
            assert isinstance(result, FOTNCandidatesDTO)
            assert result.event.id == sample_event.id
            assert isinstance(result.fotn_candidates, list)
            assert len(result.fotn_candidates) <= 5
            assert result.analysis_criteria is not None
            
            for candidate in result.fotn_candidates:
                assert candidate.fotn_score >= 0
                assert candidate.analysis.entertainment_value in ["high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_get_fight_of_the_night_candidates_nonexistent_event(self, clean_test_session):
        """존재하지 않는 이벤트의 FOTN 후보 조회 테스트"""
        from composition.exceptions import CompositionNotFoundError
        
        # When & Then: 존재하지 않는 이벤트 조회 시 CompositionNotFoundError 발생
        with pytest.raises(CompositionNotFoundError) as exc_info:
            await match_composer.get_fight_of_the_night_candidates(clean_test_session, 999)
        
        assert "Event not found: 999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_card_quality_success(self, sample_event, clean_test_session):
        """카드 품질 분석 성공 테스트"""
        # When: 이벤트 카드 품질 분석
        result = await match_composer.analyze_card_quality(clean_test_session, sample_event.id)
        
        # Then: CardQualityAnalysisDTO 반환
        assert isinstance(result, CardQualityAnalysisDTO)
        assert result.event.id == sample_event.id
        assert result.card_analysis.total_matches >= 0
        assert result.quality_assessment.overall_grade in ["Premium", "High Quality", "Good", "Average", "Below Average", "No Matches"]
        assert 0 <= result.quality_assessment.quality_score <= result.quality_assessment.max_score
    
    @pytest.mark.asyncio
    async def test_get_most_exciting_matches_by_period(self, multiple_events_different_dates, clean_test_session):
        """기간별 흥미진진한 매치 조회 테스트"""
        # When: 최근 30일 흥미진진한 매치 조회
        result = await match_composer.get_most_exciting_matches_by_period(clean_test_session, days=30, limit=5)
        
        # Then: ExcitingMatchDTO 리스트 반환
        assert isinstance(result, list)
        assert len(result) <= 5
        
        for match_dto in result:
            assert isinstance(match_dto, ExcitingMatchDTO)
            assert match_dto.excitement_score >= 0
            assert isinstance(match_dto.highlights.main_event, bool)
    
    @pytest.mark.asyncio
    async def test_analyze_comeback_performances(self, sample_event, clean_test_session):
        """컴백 성과 분석 테스트"""
        # When: 이벤트의 컴백 성과 분석
        result = await match_composer.analyze_comeback_performances(clean_test_session, sample_event.id)
        
        # Then: ComebackPerformancesDTO 반환
        assert isinstance(result, ComebackPerformancesDTO)
        assert result.event_id == sample_event.id
        assert isinstance(result.comeback_performances, list)
        assert result.total_comebacks == len(result.comeback_performances)


class TestMatchComposerWithMocks:
    """Mock을 사용한 Match Composer 단위 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fight_of_the_night_candidates_with_mock_data(self, clean_test_session):
        """Mock 데이터로 FOTN 후보 분석 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        
        mock_event = EventSchema(
            id=1, name="UFC Test Event", location="Vegas", event_date=date(2024, 1, 1),
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_match = MatchSchema(
            id=1, event_id=1, method="KO/TKO", result_round=1, is_main_event=True,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_event_summary = {
            "event": mock_event,
            "matches": [mock_match],
            "summary": {"total_matches": 1}
        }
        
        mock_match_detail = {
            "fighters": [
                {"fighter": FighterSchema(id=1, name="Fighter 1", created_at=datetime.now(), updated_at=datetime.now()), "result": "Win"},
                {"fighter": FighterSchema(id=2, name="Fighter 2", created_at=datetime.now(), updated_at=datetime.now()), "result": "Loss"}
            ],
            "winner": {"fighter": FighterSchema(id=1, name="Fighter 1", created_at=datetime.now(), updated_at=datetime.now()), "result": "Win"},
            "loser": {"fighter": FighterSchema(id=2, name="Fighter 2", created_at=datetime.now(), updated_at=datetime.now()), "result": "Loss"}
        }
        
        mock_match_stats = {"total_strikes_attempted": 150}
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.match_composer.get_event_with_matches_summary', return_value=mock_event_summary), \
             patch('composition.match_composer.match_repo.get_match_with_winner_loser', return_value=mock_match_detail), \
             patch('composition.match_composer.match_repo.get_match_statistics', return_value=mock_match_stats):
            
            result = await match_composer.get_fight_of_the_night_candidates(clean_test_session, 1)
        
        # Then: 올바른 DTO 구조 반환
        assert isinstance(result, FOTNCandidatesDTO)
        assert result.event.name == "UFC Test Event"
        assert len(result.fotn_candidates) == 1
        assert result.fotn_candidates[0].fotn_score > 0
        assert result.fotn_candidates[0].analysis.entertainment_value in ["high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_analyze_card_quality_with_mock_data(self, clean_test_session):
        """Mock 데이터로 카드 품질 분석 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        
        mock_event = EventSchema(
            id=1, name="UFC Premium Event", location="Vegas", event_date=date(2024, 1, 1),
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_matches = [
            MatchSchema(id=1, event_id=1, is_main_event=True, weight_class_id=1, method="KO/TKO", created_at=datetime.now(), updated_at=datetime.now()),
            MatchSchema(id=2, event_id=1, is_main_event=False, weight_class_id=2, method="Decision", created_at=datetime.now(), updated_at=datetime.now())
        ]
        
        # Mock 파이터 매치 관계 - 각 매치마다 2명씩
        mock_fighter_matches_match1 = [
            AsyncMock(fighter_id=1),
            AsyncMock(fighter_id=2)
        ]
        mock_fighter_matches_match2 = [
            AsyncMock(fighter_id=3),
            AsyncMock(fighter_id=4)
        ]
        
        # Mock 파이터들 (챔피언과 랭킹 파이터 포함)
        mock_champion = FighterSchema(id=1, name="Champion Fighter", belt=True, created_at=datetime.now(), updated_at=datetime.now())
        mock_ranked_fighter = FighterSchema(id=2, name="Ranked Fighter", created_at=datetime.now(), updated_at=datetime.now())
        mock_regular_fighter1 = FighterSchema(id=3, name="Regular Fighter 1", created_at=datetime.now(), updated_at=datetime.now())
        mock_regular_fighter2 = FighterSchema(id=4, name="Regular Fighter 2", created_at=datetime.now(), updated_at=datetime.now())
        
        # Mock 랭킹 데이터
        mock_ranking = AsyncMock()
        mock_ranking.ranking = 5
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.match_composer.event_repo.get_event_by_id', return_value=mock_event), \
             patch('composition.match_composer.match_repo.get_matches_by_event_id', return_value=mock_matches), \
             patch('composition.match_composer.match_repo.get_fighter_match_by_match_id', side_effect=[mock_fighter_matches_match1, mock_fighter_matches_match2]), \
             patch('composition.match_composer.fighter_repo.get_fighter_by_id', side_effect=[mock_champion, mock_ranked_fighter, mock_regular_fighter1, mock_regular_fighter2]), \
             patch('composition.match_composer.fighter_repo.get_ranking_by_fighter_id', side_effect=[[], [mock_ranking], [], []]):
            
            result = await match_composer.analyze_card_quality(clean_test_session, 1)
        
        # Then: 올바른 카드 품질 분석 반환
        assert isinstance(result, CardQualityAnalysisDTO)
        assert result.event.name == "UFC Premium Event"
        assert result.card_analysis.total_matches == 2
        assert result.card_analysis.champions >= 1
        assert result.card_analysis.ranked_fighters >= 1
        assert result.quality_assessment.overall_grade in ["Premium", "High Quality", "Good", "Average", "Below Average"]
    
    @pytest.mark.asyncio
    async def test_get_style_clash_analysis_with_mock_data(self, clean_test_session):
        """Mock 데이터로 스타일 충돌 분석 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        
        mock_match = MatchSchema(
            id=1, event_id=1, method="Decision", result_round=3,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        # 신체적 차이가 있는 두 파이터
        fighter1 = FighterSchema(
            id=1, name="Tall Fighter", height=185.0, reach=190.0, stance="Orthodox",
            wins=15, losses=2, draws=0, created_at=datetime.now(), updated_at=datetime.now()
        )
        fighter2 = FighterSchema(
            id=2, name="Short Fighter", height=170.0, reach=175.0, stance="Southpaw",
            wins=8, losses=1, draws=0, created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_match_detail = {
            "fighters": [
                {"fighter": {"id": 1, "name": "Tall Fighter"}, "result": "Win"},
                {"fighter": {"id": 2, "name": "Short Fighter"}, "result": "Loss"}
            ],
            "winner": {"fighter": {"name": "Tall Fighter"}}
        }
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.match_composer.match_repo.get_match_by_id', return_value=mock_match), \
             patch('composition.match_composer.match_repo.get_match_with_winner_loser', return_value=mock_match_detail), \
             patch('composition.match_composer.fighter_repo.get_fighter_by_id', side_effect=[fighter1, fighter2]):
            
            result = await match_composer.get_style_clash_analysis(clean_test_session, 1)
        
        # Then: 올바른 스타일 충돌 분석 반환
        assert isinstance(result, StyleClashAnalysisDTO)
        assert len(result.fighters) == 2
        assert len(result.style_contrasts) >= 2  # 키, 리치, 스탠스 차이
        
        # 스타일 대조 확인
        contrast_aspects = [contrast.aspect for contrast in result.style_contrasts]
        assert "stance" in contrast_aspects  # Orthodox vs Southpaw
        assert "height" in contrast_aspects  # 15cm 차이
        assert "reach" in contrast_aspects   # 15cm 차이
    
    @pytest.mark.asyncio
    async def test_get_performance_outliers_with_mock_data(self, clean_test_session):
        """Mock 데이터로 성과 예외자 분석 테스트"""
        # Given: Mock 데이터 설정
        mock_top_performers = [
            {
                "fighter": FighterSchema(id=1, name="Strike Machine", created_at=datetime.now(), updated_at=datetime.now()),
                "stat_name": "sig_str_landed",
                "stat_value": 75  # 임계값 50을 초과하는 예외적 성과
            }
        ]
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.match_composer.get_top_performers_in_event', side_effect=[mock_top_performers, [], []]):
            result = await match_composer.get_performance_outliers_in_event(clean_test_session, 1)
        
        # Then: 올바른 성과 예외자 분석 반환
        assert isinstance(result, PerformanceOutliersDTO)
        assert result.event_id == 1
        assert len(result.outlier_performances) == 1
        assert result.outlier_performances[0].fighter.name == "Strike Machine"
        assert result.outlier_performances[0].category == "striking"
        assert result.outlier_performances[0].outlier_rating == "notable"
        assert result.analysis_summary.total_outliers == 1


class TestMatchComposerErrorHandling:
    """Match Composer 에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_fight_of_the_night_candidates_no_event_summary(self, clean_test_session):
        """이벤트 요약이 없는 경우 테스트"""
        from composition.exceptions import CompositionNotFoundError
        
        # Given: 이벤트 요약이 None
        with patch('composition.match_composer.get_event_with_matches_summary', return_value=None):
            # When & Then: CompositionNotFoundError 발생
            with pytest.raises(CompositionNotFoundError) as exc_info:
                await match_composer.get_fight_of_the_night_candidates(clean_test_session, 1)
        
            assert "Event not found: 1" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_card_quality_no_event(self, clean_test_session):
        """존재하지 않는 이벤트의 카드 품질 분석 테스트"""
        from composition.exceptions import CompositionNotFoundError
        
        # Given: 이벤트가 None
        with patch('composition.match_composer.event_repo.get_event_by_id', return_value=None):
            # When & Then: CompositionNotFoundError 발생
            with pytest.raises(CompositionNotFoundError) as exc_info:
                await match_composer.analyze_card_quality(clean_test_session, 999)
        
            assert "Event not found: 999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_card_quality_no_matches(self, clean_test_session):
        """매치가 없는 이벤트의 카드 품질 분석 테스트"""
        # Given: 이벤트는 있지만 매치가 없음
        from datetime import datetime
        mock_event = EventSchema(
            id=1, name="Empty Event", location="Vegas", event_date=date(2024, 1, 1),
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        with patch('composition.match_composer.event_repo.get_event_by_id', return_value=mock_event), \
             patch('composition.match_composer.match_repo.get_matches_by_event_id', return_value=[]):
            
            # When: 카드 품질 분석
            result = await match_composer.analyze_card_quality(clean_test_session, 1)
        
        # Then: 빈 카드 분석 반환
        assert isinstance(result, CardQualityAnalysisDTO)
        assert result.card_analysis.total_matches == 0
        assert result.quality_assessment.overall_grade == "No Matches"
    
    @pytest.mark.asyncio
    async def test_get_style_clash_analysis_no_match(self, clean_test_session):
        """존재하지 않는 매치의 스타일 충돌 분석 테스트"""
        from composition.exceptions import CompositionNotFoundError
        
        # Given: 매치가 None
        with patch('composition.match_composer.match_repo.get_match_by_id', return_value=None):
            # When & Then: CompositionNotFoundError 발생
            with pytest.raises(CompositionNotFoundError) as exc_info:
                await match_composer.get_style_clash_analysis(clean_test_session, 999)
        
            assert "Match not found: 999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_style_clash_analysis_insufficient_fighters(self, clean_test_session):
        """파이터 정보가 부족한 매치의 스타일 충돌 분석 테스트"""
        from composition.exceptions import CompositionNotFoundError
        from datetime import datetime
        mock_match = MatchSchema(
            id=1, event_id=1, method="No Contest",
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        mock_match_detail = {
            "fighters": [{"fighter": {"id": 1, "name": "Only Fighter"}}]  # 파이터 한 명만
        }
        
        with patch('composition.match_composer.match_repo.get_match_by_id', return_value=mock_match), \
             patch('composition.match_composer.match_repo.get_match_with_winner_loser', return_value=mock_match_detail):
            
            # When & Then: CompositionNotFoundError 발생
            with pytest.raises(CompositionNotFoundError) as exc_info:
                await match_composer.get_style_clash_analysis(clean_test_session, 1)
        
            assert "Match fighters not found: 1" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_most_exciting_matches_empty_period(self, clean_test_session):
        """매치가 없는 기간의 흥미진진한 매치 조회 테스트"""
        # Given: 해당 기간에 이벤트가 없음
        with patch('composition.match_composer.event_repo.get_events_date_range', return_value=[]):
            # When: 흥미진진한 매치 조회
            result = await match_composer.get_most_exciting_matches_by_period(clean_test_session, days=30)
        
        # Then: 빈 리스트 반환
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_comeback_performances_no_matches(self, clean_test_session):
        """매치가 없는 이벤트의 컴백 성과 분석 테스트"""
        # Given: 매치가 없는 이벤트
        with patch('composition.match_composer.match_repo.get_matches_by_event_id', return_value=[]):
            # When: 컴백 성과 분석
            result = await match_composer.analyze_comeback_performances(clean_test_session, 1)
        
        # Then: 빈 컴백 성과 반환
        assert isinstance(result, ComebackPerformancesDTO)
        assert result.event_id == 1
        assert len(result.comeback_performances) == 0
        assert result.total_comebacks == 0


if __name__ == "__main__":
    print("Match Composer 테스트 실행...")
    print("✅ 매치 분석 비즈니스 로직 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/composer/test_match_composer.py -v")