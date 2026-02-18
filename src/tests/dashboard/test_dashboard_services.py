"""
Dashboard Service 테스트
Redis 캐싱은 mock 처리, DB 쿼리는 실제 테스트 DB 사용
"""
import json

import pytest
from unittest.mock import patch

from dashboard import services as dashboard_service
from dashboard.dto import (
    HomeResponseDTO,
    OverviewResponseDTO,
    StrikingResponseDTO,
    GrapplingResponseDTO,
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
        mock_redis.set.assert_called_once()


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
        mock_redis.set.assert_called_once()


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
        mock_redis.set.assert_called_once()


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
