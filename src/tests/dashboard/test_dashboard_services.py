"""
Dashboard Service 테스트
Redis 캐싱은 mock 처리, DB 쿼리는 실제 테스트 DB 사용
"""
import json

import pytest
from unittest.mock import patch, call

from dashboard import services as dashboard_service
from dashboard.dto import (
    HomeResponseDTO,
    OverviewResponseDTO,
    StrikingResponseDTO,
    GrapplingResponseDTO,
    FinishMethodDTO,
    FightDurationDTO,
    LeaderboardDTO,
    StrikeTargetDTO,
    StrikingAccuracyLeaderboardDTO,
    KoTkoLeaderDTO,
    SigStrikesLeaderboardDTO,
    TakedownLeaderboardDTO,
    SubmissionTechniqueDTO,
    GroundStrikesDTO,
    SubmissionEfficiencyDTO,
)

REDIS_PATCH = "dashboard.services.redis_client"


# =============================================================================
# Home Service
# =============================================================================

@pytest.mark.asyncio
async def test_get_home_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_home(clean_test_session)

        assert isinstance(result, HomeResponseDTO)
        assert result.summary.total_fighters == 3
        assert result.summary.total_matches == 9
        assert result.summary.total_events == 7
        assert len(result.recent_events) == 5
        assert len(result.upcoming_events) == 2
        assert len(result.rankings) >= 1
        # 캐시 저장 호출 확인
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_home_cache_hit(clean_test_session):
    cached = {
        "summary": {"total_fighters": 100, "total_matches": 200, "total_events": 50},
        "recent_events": [],
        "upcoming_events": [],
        "rankings": [],
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_home(clean_test_session)

        assert isinstance(result, HomeResponseDTO)
        assert result.summary.total_fighters == 100
        mock_redis.set.assert_not_called()


# =============================================================================
# Overview Service
# =============================================================================

@pytest.mark.asyncio
async def test_get_overview_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_overview(clean_test_session)

        assert isinstance(result, OverviewResponseDTO)
        assert len(result.finish_methods) > 0
        assert len(result.weight_class_activity) > 0
        assert len(result.events_timeline) > 0
        assert result.leaderboard is not None
        assert len(result.leaderboard.wins) > 0
        assert result.fight_duration is not None
        assert result.fight_duration.avg_round > 0
        # 탭 함수가 차트 함수를 호출하므로 chart-level + tab-level 캐시 set 발생
        assert mock_redis.set.call_count >= 1


@pytest.mark.asyncio
async def test_get_overview_with_weight_class(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_overview(clean_test_session, weight_class_id=4)

        assert isinstance(result, OverviewResponseDTO)
        assert len(result.finish_methods) > 0


# =============================================================================
# Striking Service
# =============================================================================

@pytest.mark.asyncio
async def test_get_striking_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_striking(clean_test_session)

        assert isinstance(result, StrikingResponseDTO)
        assert len(result.strike_targets) == 5
        assert len(result.striking_accuracy.min10) >= 0
        assert len(result.ko_tko_leaders) >= 1
        assert result.sig_strikes_per_fight.min10 is not None
        # 탭 함수가 차트 함수를 호출하므로 chart-level + tab-level 캐시 set 발생
        assert mock_redis.set.call_count >= 1


@pytest.mark.asyncio
async def test_get_striking_cache_hit(clean_test_session):
    cached = {
        "strike_targets": [
            {"target": "Head", "landed": 500},
            {"target": "Body", "landed": 300},
            {"target": "Leg", "landed": 200},
            {"target": "Clinch", "landed": 100},
            {"target": "Ground", "landed": 50},
        ],
        "striking_accuracy": {"min10": [], "min20": [], "min30": []},
        "ko_tko_leaders": [],
        "sig_strikes_per_fight": {"min10": [], "min20": [], "min30": []},
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_striking(clean_test_session)

        assert isinstance(result, StrikingResponseDTO)
        assert result.strike_targets[0].landed == 500
        mock_redis.set.assert_not_called()


# =============================================================================
# Grappling Service
# =============================================================================

@pytest.mark.asyncio
async def test_get_grappling_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_grappling(clean_test_session)

        assert isinstance(result, GrapplingResponseDTO)
        assert len(result.takedown_accuracy.min10) >= 0
        assert len(result.submission_techniques) >= 1
        assert len(result.control_time) >= 1
        assert result.submission_efficiency is not None
        # 탭 함수가 차트 함수를 호출하므로 chart-level + tab-level 캐시 set 발생
        assert mock_redis.set.call_count >= 1


@pytest.mark.asyncio
async def test_get_grappling_cache_hit(clean_test_session):
    cached = {
        "takedown_accuracy": {"min10": [], "min20": [], "min30": []},
        "submission_techniques": [],
        "control_time": [],
        "ground_strikes": [],
        "submission_efficiency": {
            "fighters": [],
            "avg_efficiency_ratio": 0.15,
        },
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_grappling(clean_test_session)

        assert isinstance(result, GrapplingResponseDTO)
        assert result.submission_efficiency.avg_efficiency_ratio == 0.15
        mock_redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_get_grappling_redis_error(clean_test_session, dashboard_data):
    """Redis 에러 시에도 DB 쿼리로 정상 동작"""
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.side_effect = Exception("Redis connection failed")
        mock_redis.set.side_effect = Exception("Redis connection failed")

        result = await dashboard_service.get_grappling(clean_test_session)

        assert isinstance(result, GrapplingResponseDTO)
        assert len(result.takedown_accuracy.min10) >= 0


# =============================================================================
# Chart: Finish Methods
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_finish_methods_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_finish_methods(clean_test_session)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, FinishMethodDTO) for item in result)
        categories = {item.method_category for item in result}
        assert "KO/TKO" in categories
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_finish_methods_cache_hit(clean_test_session):
    cached = {"items": [
        {"method_category": "KO/TKO", "count": 100},
        {"method_category": "SUB", "count": 50},
    ]}
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_finish_methods(clean_test_session)

        assert len(result) == 2
        assert result[0].count == 100
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Fight Duration
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_fight_duration_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_fight_duration(clean_test_session)

        assert isinstance(result, FightDurationDTO)
        assert result.avg_round > 0
        assert result.avg_time_seconds is not None
        assert len(result.rounds) > 0
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_fight_duration_cache_hit(clean_test_session):
    cached = {
        "rounds": [{"result_round": 1, "fight_count": 10, "percentage": 50.0}],
        "avg_round": 1.5,
        "avg_time_seconds": 300,
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_fight_duration(clean_test_session)

        assert isinstance(result, FightDurationDTO)
        assert result.avg_round == 1.5
        assert result.avg_time_seconds == 300
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Leaderboard
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_leaderboard_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_leaderboard(clean_test_session)

        assert isinstance(result, LeaderboardDTO)
        assert len(result.wins) > 0
        assert hasattr(result, "winrate_min10")
        assert hasattr(result, "winrate_min20")
        assert hasattr(result, "winrate_min30")
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_leaderboard_cache_hit(clean_test_session):
    cached = {
        "wins": [{"name": "Test", "wins": 10, "losses": 1, "draws": 0, "win_rate": 90.9}],
        "winrate_min10": [],
        "winrate_min20": [],
        "winrate_min30": [],
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_leaderboard(clean_test_session)

        assert isinstance(result, LeaderboardDTO)
        assert result.wins[0].name == "Test"
        mock_redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_get_chart_leaderboard_ufc_only(clean_test_session, dashboard_data):
    """ufc_only=True 시 fighter_match 기반 결과"""
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_leaderboard(
            clean_test_session, ufc_only=True
        )

        assert isinstance(result, LeaderboardDTO)
        assert len(result.wins) > 0
        # ufc_only=True 시 fighter_match 테이블 기반 집계
        assert result.wins[0].name == "Alpha Fighter"


# =============================================================================
# Chart: Strike Targets
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_strike_targets_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_strike_targets(clean_test_session)

        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(item, StrikeTargetDTO) for item in result)
        targets = {item.target for item in result}
        assert targets == {"Head", "Body", "Leg", "Clinch", "Ground"}
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_strike_targets_cache_hit(clean_test_session):
    cached = {"items": [
        {"target": "Head", "landed": 999},
        {"target": "Body", "landed": 500},
        {"target": "Leg", "landed": 300},
        {"target": "Clinch", "landed": 100},
        {"target": "Ground", "landed": 50},
    ]}
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_strike_targets(clean_test_session)

        assert len(result) == 5
        assert result[0].landed == 999
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Striking Accuracy
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_striking_accuracy_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_striking_accuracy(clean_test_session)

        assert isinstance(result, StrikingAccuracyLeaderboardDTO)
        assert hasattr(result, "min10")
        assert hasattr(result, "min20")
        assert hasattr(result, "min30")
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_striking_accuracy_cache_hit(clean_test_session):
    cached = {
        "min10": [{"name": "A", "total_sig_landed": 100, "total_sig_attempted": 150, "accuracy": 66.7}],
        "min20": [],
        "min30": [],
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_striking_accuracy(clean_test_session)

        assert isinstance(result, StrikingAccuracyLeaderboardDTO)
        assert len(result.min10) == 1
        assert result.min10[0].accuracy == 66.7
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: KO/TKO Leaders
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_ko_tko_leaders_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_ko_tko_leaders(clean_test_session)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(item, KoTkoLeaderDTO) for item in result)
        assert result[0].name == "Alpha Fighter"
        assert result[0].ko_tko_finishes == 3
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_ko_tko_leaders_cache_hit(clean_test_session):
    cached = {"items": [
        {"name": "Test Fighter", "ko_tko_finishes": 15},
    ]}
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_ko_tko_leaders(clean_test_session)

        assert len(result) == 1
        assert result[0].ko_tko_finishes == 15
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Sig Strikes Per Fight
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_sig_strikes_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_sig_strikes(clean_test_session)

        assert isinstance(result, SigStrikesLeaderboardDTO)
        assert hasattr(result, "min10")
        assert hasattr(result, "min20")
        assert hasattr(result, "min30")
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_sig_strikes_cache_hit(clean_test_session):
    cached = {
        "min10": [{"name": "A", "sig_str_per_fight": 8.5, "total_fights": 15}],
        "min20": [],
        "min30": [],
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_sig_strikes(clean_test_session)

        assert isinstance(result, SigStrikesLeaderboardDTO)
        assert len(result.min10) == 1
        assert result.min10[0].sig_str_per_fight == 8.5
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Takedown Accuracy
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_takedown_accuracy_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_takedown_accuracy(clean_test_session)

        assert isinstance(result, TakedownLeaderboardDTO)
        assert hasattr(result, "min10")
        assert hasattr(result, "min20")
        assert hasattr(result, "min30")
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_takedown_accuracy_cache_hit(clean_test_session):
    cached = {
        "min10": [{"name": "A", "total_td_landed": 50, "total_td_attempted": 80, "td_accuracy": 62.5}],
        "min20": [],
        "min30": [],
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_takedown_accuracy(clean_test_session)

        assert isinstance(result, TakedownLeaderboardDTO)
        assert len(result.min10) == 1
        assert result.min10[0].td_accuracy == 62.5
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Submission Techniques
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_submission_techniques_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_submission_techniques(clean_test_session)

        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(item, SubmissionTechniqueDTO) for item in result)
        techniques = {item.technique for item in result}
        assert "Rear Naked Choke" in techniques
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_submission_techniques_cache_hit(clean_test_session):
    cached = {"items": [
        {"technique": "Armbar", "count": 50},
        {"technique": "Rear Naked Choke", "count": 80},
    ]}
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_submission_techniques(clean_test_session)

        assert len(result) == 2
        assert result[0].technique == "Armbar"
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Ground Strikes
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_ground_strikes_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_ground_strikes(clean_test_session)

        assert isinstance(result, list)
        assert all(isinstance(item, GroundStrikesDTO) for item in result)
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_ground_strikes_cache_hit(clean_test_session):
    cached = {"items": [
        {"name": "A", "total_ground_landed": 200, "total_ground_attempted": 350, "accuracy": 57.1},
    ]}
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_ground_strikes(clean_test_session)

        assert len(result) == 1
        assert result[0].accuracy == 57.1
        mock_redis.set.assert_not_called()


# =============================================================================
# Chart: Submission Efficiency
# =============================================================================

@pytest.mark.asyncio
async def test_get_chart_submission_efficiency_cache_miss(clean_test_session, dashboard_data):
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = None

        result = await dashboard_service.get_chart_submission_efficiency(clean_test_session)

        assert isinstance(result, SubmissionEfficiencyDTO)
        assert hasattr(result, "fighters")
        assert hasattr(result, "avg_efficiency_ratio")
        assert isinstance(result.avg_efficiency_ratio, float)
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_get_chart_submission_efficiency_cache_hit(clean_test_session):
    cached = {
        "fighters": [
            {"name": "A", "total_sub_attempts": 20, "sub_finishes": 12},
        ],
        "avg_efficiency_ratio": 0.45,
    }
    with patch(REDIS_PATCH) as mock_redis:
        mock_redis.get.return_value = json.dumps(cached)

        result = await dashboard_service.get_chart_submission_efficiency(clean_test_session)

        assert isinstance(result, SubmissionEfficiencyDTO)
        assert len(result.fighters) == 1
        assert result.avg_efficiency_ratio == 0.45
        mock_redis.set.assert_not_called()
