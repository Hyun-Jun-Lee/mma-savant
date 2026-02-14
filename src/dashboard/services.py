"""
Dashboard 서비스 레이어
Redis 캐싱 + Repository 호출 조합
"""
import json
import logging
from typing import Optional
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from dashboard import repositories as dashboard_repo
from dashboard.dto import (
    HomeResponseDTO, SummaryDTO, RecentEventDTO, UpcomingEventDTO,
    DivisionRankingDTO, RankingFighterDTO,
    OverviewResponseDTO, FinishMethodDTO, WeightClassActivityDTO,
    EventTimelineDTO, LeaderboardDTO, LeaderboardFighterDTO,
    FightDurationDTO, FightDurationRoundDTO,
    StrikingResponseDTO, StrikeTargetDTO, StrikingAccuracyDTO,
    KoTkoLeaderDTO, SigStrikesPerFightDTO,
    GrapplingResponseDTO, TakedownAccuracyDTO, SubmissionTechniqueDTO,
    ControlTimeDTO, GroundStrikesDTO, SubmissionEfficiencyDTO,
    SubmissionEfficiencyFighterDTO,
)
from dashboard.exceptions import DashboardQueryError
from database.connection.redis_conn import redis_client

logger = logging.getLogger(__name__)

# Redis 캐싱 설정
CACHE_TTL = 60 * 60 * 24 * 7  # 7일


def _cache_key(tab: str, weight_class_id: Optional[int] = None) -> str:
    suffix = f":{weight_class_id}" if weight_class_id is not None else ":all"
    return f"dashboard:{tab}{suffix}"


def _get_cached(key: str) -> Optional[dict]:
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Redis cache read failed for {key}: {e}")
    return None


def _set_cache(key: str, data: dict) -> None:
    try:
        redis_client.set(key, json.dumps(data, default=str), ex=CACHE_TTL)
    except Exception as e:
        logger.warning(f"Redis cache write failed for {key}: {e}")


# ===========================
# Tab 1: Home
# ===========================

async def get_home(session: AsyncSession) -> HomeResponseDTO:
    cache_key = _cache_key("home")
    cached = _get_cached(cache_key)
    if cached:
        return HomeResponseDTO(**cached)

    try:
        summary_data = await dashboard_repo.get_summary(session)
        recent_events_data = await dashboard_repo.get_recent_events(session)
        upcoming_events_data = await dashboard_repo.get_upcoming_events(session)
        rankings_data = await dashboard_repo.get_rankings(session)

        # rankings를 체급별로 그룹핑
        divisions = defaultdict(list)
        division_names = {}
        for row in rankings_data:
            wc_id = row["weight_class_id"]
            division_names[wc_id] = row["weight_class"]
            divisions[wc_id].append(RankingFighterDTO(
                ranking=row["ranking"],
                fighter_name=row["fighter_name"],
                wins=row["wins"],
                losses=row["losses"],
                draws=row["draws"],
            ))

        rankings = [
            DivisionRankingDTO(
                weight_class_id=wc_id,
                weight_class=division_names[wc_id],
                fighters=fighters,
            )
            for wc_id, fighters in divisions.items()
        ]

        response = HomeResponseDTO(
            summary=SummaryDTO(**summary_data),
            recent_events=[RecentEventDTO(**e) for e in recent_events_data],
            upcoming_events=[UpcomingEventDTO(**e) for e in upcoming_events_data],
            rankings=rankings,
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_home", str(e))


# ===========================
# Tab 2: Overview
# ===========================

async def get_overview(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> OverviewResponseDTO:
    cache_key = _cache_key("overview", weight_class_id)
    cached = _get_cached(cache_key)
    if cached:
        return OverviewResponseDTO(**cached)

    try:
        finish_methods_data = await dashboard_repo.get_finish_methods(session, weight_class_id)
        weight_class_activity_data = await dashboard_repo.get_weight_class_activity(session)
        events_timeline_data = await dashboard_repo.get_events_timeline(session)

        wins_data = await dashboard_repo.get_leaderboard_wins(session, weight_class_id)
        winrate10_data = await dashboard_repo.get_leaderboard_winrate(session, 10, weight_class_id)
        winrate20_data = await dashboard_repo.get_leaderboard_winrate(session, 20, weight_class_id)
        winrate30_data = await dashboard_repo.get_leaderboard_winrate(session, 30, weight_class_id)

        rounds_data = await dashboard_repo.get_fight_duration_rounds(session, weight_class_id)
        avg_round = await dashboard_repo.get_fight_duration_avg_round(session, weight_class_id)

        response = OverviewResponseDTO(
            finish_methods=[FinishMethodDTO(**r) for r in finish_methods_data],
            weight_class_activity=[WeightClassActivityDTO(**r) for r in weight_class_activity_data],
            events_timeline=[EventTimelineDTO(**r) for r in events_timeline_data],
            leaderboard=LeaderboardDTO(
                wins=[LeaderboardFighterDTO(**r) for r in wins_data],
                winrate_min10=[LeaderboardFighterDTO(**r) for r in winrate10_data],
                winrate_min20=[LeaderboardFighterDTO(**r) for r in winrate20_data],
                winrate_min30=[LeaderboardFighterDTO(**r) for r in winrate30_data],
            ),
            fight_duration=FightDurationDTO(
                rounds=[FightDurationRoundDTO(**r) for r in rounds_data],
                avg_round=avg_round,
            ),
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_overview", str(e))


# ===========================
# Tab 3: Striking
# ===========================

async def get_striking(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> StrikingResponseDTO:
    cache_key = _cache_key("striking", weight_class_id)
    cached = _get_cached(cache_key)
    if cached:
        return StrikingResponseDTO(**cached)

    try:
        strike_targets_data = await dashboard_repo.get_strike_targets(session, weight_class_id)
        striking_accuracy_data = await dashboard_repo.get_striking_accuracy(session, weight_class_id)
        ko_tko_leaders_data = await dashboard_repo.get_ko_tko_leaders(session, weight_class_id)
        sig_strikes_data = await dashboard_repo.get_sig_strikes_per_fight(session, weight_class_id)

        response = StrikingResponseDTO(
            strike_targets=[StrikeTargetDTO(**r) for r in strike_targets_data],
            striking_accuracy=[StrikingAccuracyDTO(**r) for r in striking_accuracy_data],
            ko_tko_leaders=[KoTkoLeaderDTO(**r) for r in ko_tko_leaders_data],
            sig_strikes_per_fight=[SigStrikesPerFightDTO(**r) for r in sig_strikes_data],
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_striking", str(e))


# ===========================
# Tab 4: Grappling
# ===========================

async def get_grappling(
    session: AsyncSession, weight_class_id: Optional[int] = None
) -> GrapplingResponseDTO:
    cache_key = _cache_key("grappling", weight_class_id)
    cached = _get_cached(cache_key)
    if cached:
        return GrapplingResponseDTO(**cached)

    try:
        takedown_data = await dashboard_repo.get_takedown_accuracy(session, weight_class_id)
        sub_techniques_data = await dashboard_repo.get_submission_techniques(session, weight_class_id)
        control_time_data = await dashboard_repo.get_control_time(session)
        ground_strikes_data = await dashboard_repo.get_ground_strikes(session, weight_class_id)
        sub_efficiency_fighters = await dashboard_repo.get_submission_efficiency_fighters(session, weight_class_id)
        avg_ratio = await dashboard_repo.get_submission_efficiency_avg_ratio(session, weight_class_id)

        response = GrapplingResponseDTO(
            takedown_accuracy=[TakedownAccuracyDTO(**r) for r in takedown_data],
            submission_techniques=[SubmissionTechniqueDTO(**r) for r in sub_techniques_data],
            control_time=[ControlTimeDTO(**r) for r in control_time_data],
            ground_strikes=[GroundStrikesDTO(**r) for r in ground_strikes_data],
            submission_efficiency=SubmissionEfficiencyDTO(
                fighters=[SubmissionEfficiencyFighterDTO(**r) for r in sub_efficiency_fighters],
                avg_efficiency_ratio=avg_ratio,
            ),
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_grappling", str(e))
