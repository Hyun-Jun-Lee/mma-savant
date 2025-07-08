"""
Event Composer 테스트
composition/event_composer.py의 비즈니스 로직 레이어에 대한 포괄적인 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import date

from composition import event_composer
from composition.dto import (
    EventWithAllMatchesDTO, EventWithMainMatchDTO, UpcomingEventWithFeaturedMatchesDTO,
    EventComparisonDTO, EventRankingImpactDTO, MatchDetailDTO, MatchFighterResultDTO,
    EventSummaryStatsDTO, FeaturedMatchDTO
)
from event.models import EventSchema
from match.models import MatchSchema
from fighter.models import FighterSchema


class TestEventComposerWithTestDB:
    """Test DB를 사용한 Event Composer 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_with_all_matches_success(self, sample_event, clean_test_session):
        """이벤트와 모든 매치 정보 조회 성공 테스트"""
        # When: 이벤트 이름으로 모든 매치 조회
        result = await event_composer.get_event_with_all_matches(clean_test_session, sample_event.name)
        
        # Then: EventWithAllMatchesDTO 반환
        assert result is not None
        assert isinstance(result, EventWithAllMatchesDTO)
        assert result.event.id == sample_event.id
        assert result.event.name == sample_event.name
        assert isinstance(result.matches, list)
        assert isinstance(result.summary, EventSummaryStatsDTO)
        assert isinstance(result.summary.total_matches, int)
        assert isinstance(result.summary.main_events_count, int)
        assert isinstance(result.summary.finish_methods, dict)
    
    @pytest.mark.asyncio
    async def test_get_event_with_all_matches_nonexistent(self, clean_test_session):
        """존재하지 않는 이벤트 조회 테스트"""
        # When: 존재하지 않는 이벤트 조회
        result = await event_composer.get_event_with_all_matches(clean_test_session, "Nonexistent Event")
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_recent_events_with_main_match(self, multiple_events_different_dates, clean_test_session):
        """최근 이벤트와 메인 매치 조회 테스트"""
        # When: 최근 이벤트들과 메인 매치 조회
        result = await event_composer.get_recent_events_with_main_match(clean_test_session, limit=3)
        
        # Then: EventWithMainMatchDTO 리스트 반환
        assert isinstance(result, list)
        assert len(result) <= 3
        
        for event_data in result:
            assert isinstance(event_data, EventWithMainMatchDTO)
            assert isinstance(event_data.event, EventSchema)
            # main_match는 Optional이므로 None일 수 있음
            if event_data.main_match:
                assert isinstance(event_data.main_match, MatchDetailDTO)
    
    @pytest.mark.asyncio
    async def test_get_upcoming_events_with_featured_matches(self, events_past_and_future, clean_test_session):
        """다가오는 이벤트와 주요 매치 조회 테스트"""
        # When: 다가오는 이벤트들과 주요 매치 조회
        result = await event_composer.get_upcoming_events_with_featured_matches(clean_test_session, limit=2)
        
        # Then: UpcomingEventWithFeaturedMatchesDTO 리스트 반환
        assert isinstance(result, list)
        assert len(result) <= 2
        
        for event_data in result:
            assert isinstance(event_data, UpcomingEventWithFeaturedMatchesDTO)
            assert isinstance(event_data.event, EventSchema)
            # main_event는 Optional
            if event_data.main_event:
                assert isinstance(event_data.main_event, FeaturedMatchDTO)
            # featured_matches는 최대 3개
            assert len(event_data.featured_matches) <= 3
            for match in event_data.featured_matches:
                assert isinstance(match, FeaturedMatchDTO)


class TestEventComposerWithMocks:
    """Mock을 사용한 Event Composer 단위 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_event_with_all_matches_with_mock_data(self, clean_test_session):
        """Mock 데이터로 이벤트 모든 매치 조회 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        mock_event = EventSchema(
            id=1,
            name="UFC Test Event",
            location="Las Vegas, NV",
            event_date=date(2024, 8, 1),
            url="http://example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_event_summary = {
            "event": mock_event,
            "matches": [
                MatchSchema(
                    id=1,
                    event_id=1,
                    method="KO/TKO",
                    is_main_event=True,
                    order=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ],
            "summary": {
                "total_matches": 1,
                "main_events_count": 1,
                "finish_methods": {"KO/TKO": 1}
            }
        }
        
        mock_match_result = {
            "fighters": [
                {
                    "fighter": FighterSchema(
                        id=1, name="Fighter 1", created_at=datetime.now(), updated_at=datetime.now()
                    ),
                    "result": "Win"
                },
                {
                    "fighter": FighterSchema(
                        id=2, name="Fighter 2", created_at=datetime.now(), updated_at=datetime.now()
                    ),
                    "result": "Loss"
                }
            ],
            "winner": {
                "fighter": FighterSchema(
                    id=1, name="Fighter 1", created_at=datetime.now(), updated_at=datetime.now()
                ),
                "result": "Win"
            },
            "loser": {
                "fighter": FighterSchema(
                    id=2, name="Fighter 2", created_at=datetime.now(), updated_at=datetime.now()
                ),
                "result": "Loss"
            }
        }
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.event_composer.event_repo.get_event_by_name', return_value=mock_event), \
             patch('composition.event_composer.get_event_with_matches_summary', return_value=mock_event_summary), \
             patch('composition.event_composer.match_repo.get_match_with_winner_loser', return_value=mock_match_result):
            
            result = await event_composer.get_event_with_all_matches(clean_test_session, "UFC Test Event")
        
        # Then: 올바른 DTO 구조 반환
        assert isinstance(result, EventWithAllMatchesDTO)
        assert result.event.name == "UFC Test Event"
        assert len(result.matches) == 1
        assert result.matches[0].match_info.method == "KO/TKO"
        assert len(result.matches[0].fighters) == 2
        assert result.matches[0].winner.fighter.name == "Fighter 1"
        assert result.matches[0].loser.fighter.name == "Fighter 2"
        assert result.summary.total_matches == 1
        assert result.summary.main_events_count == 1
    
    @pytest.mark.asyncio
    async def test_compare_events_by_performance_with_mocks(self, clean_test_session):
        """Mock을 사용한 이벤트 성과 비교 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        event1_summary = {
            "event": EventSchema(
                id=1, name="UFC Event 1", location="Vegas", event_date=date(2024, 1, 1),
                created_at=datetime.now(), updated_at=datetime.now()
            ),
            "matches": [],
            "summary": {
                "total_matches": 10,
                "main_events_count": 1,
                "finish_methods": {"KO/TKO": 5, "Decision": 5}
            }
        }
        
        event2_summary = {
            "event": EventSchema(
                id=2, name="UFC Event 2", location="New York", event_date=date(2024, 2, 1),
                created_at=datetime.now(), updated_at=datetime.now()
            ),
            "matches": [],
            "summary": {
                "total_matches": 8,
                "main_events_count": 1,
                "finish_methods": {"KO/TKO": 3, "Decision": 5}
            }
        }
        
        # When: Mock을 사용하여 함수 호출
        with patch('composition.event_composer.get_event_with_matches_summary', side_effect=[event1_summary, event2_summary]):
            result = await event_composer.compare_events_by_performance(clean_test_session, 1, 2)
        
        # Then: 올바른 비교 결과 반환
        assert isinstance(result, EventComparisonDTO)
        assert result.event1.event_info.name == "UFC Event 1"
        assert result.event2.event_info.name == "UFC Event 2"
        assert result.event1.stats.total_matches == 10
        assert result.event2.stats.total_matches == 8
        assert result.comparison.more_matches == "event1"
        assert result.comparison.match_difference == 2
    
    @pytest.mark.asyncio
    async def test_get_recent_events_with_main_match_empty_main_match(self, clean_test_session):
        """메인 매치가 없는 경우 테스트"""
        # Given: Mock 데이터 설정 (메인 매치 없음)
        from datetime import datetime
        mock_events = [
            EventSchema(
                id=1, name="UFC Event", location="Vegas", event_date=date(2024, 1, 1),
                created_at=datetime.now(), updated_at=datetime.now()
            )
        ]
        
        # When: Mock을 사용하여 함수 호출
        with patch('event.repositories.get_recent_events', return_value=mock_events), \
             patch('composition.repositories.get_event_main_event_match', return_value=None):
            
            result = await event_composer.get_recent_events_with_main_match(clean_test_session, limit=1)
        
        # Then: 메인 매치가 None인 결과 반환
        assert len(result) == 1
        assert isinstance(result[0], EventWithMainMatchDTO)
        assert result[0].event.name == "UFC Event"
        assert result[0].main_match is None
    
    @pytest.mark.asyncio
    async def test_get_upcoming_events_with_featured_matches_filtering(self, clean_test_session):
        """주요 매치 필터링 로직 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        mock_events = [
            EventSchema(
                id=1, name="UFC Future Event", location="Vegas", event_date=date(2025, 1, 1),
                created_at=datetime.now(), updated_at=datetime.now()
            )
        ]
        
        mock_matches = [
            MatchSchema(id=1, event_id=1, is_main_event=True, order=1, created_at=datetime.now(), updated_at=datetime.now()),  # 메인 이벤트
            MatchSchema(id=2, event_id=1, is_main_event=False, order=5, created_at=datetime.now(), updated_at=datetime.now()),  # 주요 매치 (order >= 3)
            MatchSchema(id=3, event_id=1, is_main_event=False, order=4, created_at=datetime.now(), updated_at=datetime.now()),  # 주요 매치
            MatchSchema(id=4, event_id=1, is_main_event=False, order=2, created_at=datetime.now(), updated_at=datetime.now()),  # 일반 매치 (제외)
        ]
        
        mock_match_detail = {"fighters": []}
        
        # When: Mock을 사용하여 함수 호출
        with patch('event.repositories.get_upcoming_events', return_value=mock_events), \
             patch('match.repositories.get_matches_by_event_id', return_value=mock_matches), \
             patch('match.repositories.get_match_with_participants', return_value=mock_match_detail):
            
            result = await event_composer.get_upcoming_events_with_featured_matches(clean_test_session, limit=1)
        
        # Then: 올바른 필터링 결과
        assert len(result) == 1
        event_data = result[0]
        assert event_data.main_event is not None  # 메인 이벤트 있음
        assert len(event_data.featured_matches) == 2  # order >= 3인 매치 2개
    
    @pytest.mark.asyncio
    async def test_get_event_rankings_impact_with_ranked_fighters(self, clean_test_session):
        """랭킹 파이터가 있는 이벤트 영향 분석 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        mock_matches = [
            MatchSchema(id=1, event_id=1, is_main_event=True, created_at=datetime.now(), updated_at=datetime.now())
        ]
        
        mock_match_result = {
            "winner": {
                "fighter": FighterSchema(
                    id=1, name="Ranked Fighter 1", created_at=datetime.now(), updated_at=datetime.now()
                )
            },
            "loser": {
                "fighter": FighterSchema(
                    id=2, name="Ranked Fighter 2", created_at=datetime.now(), updated_at=datetime.now()
                )
            }
        }
        
        # Mock 랭킹 데이터
        from unittest.mock import MagicMock
        mock_ranking1 = MagicMock()
        mock_ranking1.ranking = 3
        mock_ranking1.weight_class_id = 1
        
        mock_ranking2 = MagicMock()
        mock_ranking2.ranking = 8
        mock_ranking2.weight_class_id = 1
        
        # When: Mock을 사용하여 함수 호출
        with patch('match.repositories.get_matches_by_event_id', return_value=mock_matches), \
             patch('match.repositories.get_match_with_winner_loser', return_value=mock_match_result), \
             patch('fighter.repositories.get_ranking_by_fighter_id', side_effect=[[mock_ranking1], [mock_ranking2]]):
            
            result = await event_composer.get_event_rankings_impact(clean_test_session, 1)
        
        # Then: 올바른 랭킹 영향 분석 결과
        assert isinstance(result, EventRankingImpactDTO)
        assert result.event_id == 1
        assert len(result.ranking_impacts) == 1
        
        impact = result.ranking_impacts[0]
        assert impact.winner.fighter.name == "Ranked Fighter 1"
        assert impact.loser.fighter.name == "Ranked Fighter 2"
        assert impact.potential_impact.winner_moving_up is True
        assert impact.potential_impact.loser_moving_down is True
        assert impact.potential_impact.title_implications is True  # 메인 이벤트 + 랭킹 5위 이내
        
        assert result.summary.matches_with_ranked_fighters == 1
        assert result.summary.title_implication_matches == 1


class TestEventComposerErrorHandling:
    """Event Composer 에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_compare_events_missing_event1(self, clean_test_session):
        """첫 번째 이벤트가 없는 경우 테스트"""
        # Given: 첫 번째 이벤트 없음
        with patch('composition.repositories.get_event_with_matches_summary', side_effect=[None, {}]):
            # When: 비교 함수 호출
            result = await event_composer.compare_events_by_performance(clean_test_session, 999, 1)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_compare_events_missing_event2(self, clean_test_session):
        """두 번째 이벤트가 없는 경우 테스트"""
        # Given: 두 번째 이벤트 없음
        with patch('composition.repositories.get_event_with_matches_summary', side_effect=[{}, None]):
            # When: 비교 함수 호출
            result = await event_composer.compare_events_by_performance(clean_test_session, 1, 999)
        
        # Then: None 반환
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_event_rankings_impact_no_winner_loser(self, clean_test_session):
        """승부가 결정되지 않은 매치의 영향 분석 테스트"""
        # Given: Mock 데이터 설정 (승자/패자 없음)
        mock_matches = [
            MatchSchema(id=1, event_id=1, is_main_event=False)
        ]
        
        mock_match_result = {
            "winner": None,
            "loser": None
        }
        
        # When: Mock을 사용하여 함수 호출
        with patch('match.repositories.get_matches_by_event_id', return_value=mock_matches), \
             patch('match.repositories.get_match_with_winner_loser', return_value=mock_match_result):
            
            result = await event_composer.get_event_rankings_impact(clean_test_session, 1)
        
        # Then: 빈 랭킹 영향 결과
        assert isinstance(result, EventRankingImpactDTO)
        assert result.event_id == 1
        assert len(result.ranking_impacts) == 0
        assert result.summary.matches_with_ranked_fighters == 0
        assert result.summary.title_implication_matches == 0
    
    @pytest.mark.asyncio
    async def test_get_event_with_all_matches_no_match_results(self, clean_test_session):
        """매치 결과가 없는 경우 테스트"""
        # Given: Mock 데이터 설정
        from datetime import datetime
        mock_event = EventSchema(
            id=1, name="UFC Test Event", location="Vegas", event_date=date(2024, 1, 1),
            created_at=datetime.now(), updated_at=datetime.now()
        )
        mock_event_summary = {
            "event": mock_event,
            "matches": [
                MatchSchema(
                    id=1, event_id=1, method="TBD", is_main_event=True,
                    created_at=datetime.now(), updated_at=datetime.now()
                )
            ],
            "summary": {
                "total_matches": 1,
                "main_events_count": 1,
                "finish_methods": {}
            }
        }
        
        # When: 매치 결과가 None인 경우
        with patch('composition.event_composer.event_repo.get_event_by_name', return_value=mock_event), \
             patch('composition.event_composer.get_event_with_matches_summary', return_value=mock_event_summary), \
             patch('composition.event_composer.match_repo.get_match_with_winner_loser', return_value=None):
            
            result = await event_composer.get_event_with_all_matches(clean_test_session, "UFC Test Event")
        
        # Then: 매치 결과 없이도 정상 처리
        assert isinstance(result, EventWithAllMatchesDTO)
        assert len(result.matches) == 0  # 매치 결과가 없으므로 빈 리스트


if __name__ == "__main__":
    print("Event Composer 테스트 실행...")
    print("✅ 비즈니스 로직 레이어 완전 테스트!")
    print("\n테스트 실행:")
    print("uv run pytest tests/composer/test_event_composer.py -v")