"""
Dashboard 서비스 레이어
Redis 캐싱 + Repository 호출 조합
"""
import json
import logging
from typing import Optional, Type, TypeVar
from collections import defaultdict

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard import repositories as dashboard_repo
from dashboard.dto import (
    HomeResponseDTO, SummaryDTO, RecentEventDTO, UpcomingEventDTO,
    DivisionRankingDTO, RankingFighterDTO,
    OverviewResponseDTO, FinishMethodDTO, WeightClassActivityDTO,
    EventTimelineDTO, LeaderboardDTO, LeaderboardFighterDTO,
    FightDurationDTO, FightDurationRoundDTO,
    StrikingResponseDTO, StrikeTargetDTO, StrikingAccuracyDTO,
    StrikingAccuracyLeaderboardDTO, SigStrikesLeaderboardDTO,
    KoTkoLeaderDTO, SigStrikesPerFightDTO,
    GrapplingResponseDTO, TakedownAccuracyDTO, TakedownLeaderboardDTO,
    SubmissionTechniqueDTO,
    ControlTimeDTO, GroundStrikesDTO, SubmissionEfficiencyDTO,
    SubmissionEfficiencyFighterDTO,
)
from dashboard.exceptions import DashboardQueryError
from database.connection.redis_conn import redis_client

logger = logging.getLogger(__name__)

# Redis 캐싱 설정
CACHE_TTL = 60 * 60 * 24 * 7  # 7일


def _cache_key(
    tab: str,
    weight_class_id: Optional[int] = None,
    min_fights: Optional[int] = None,
    limit: Optional[int] = None,
    ufc_only: bool = False,
) -> str:
    suffix = f":{weight_class_id}" if weight_class_id is not None else ":all"
    if min_fights is not None and min_fights != 10:
        suffix += f":mf{min_fights}"
    if limit is not None and limit != 10:
        suffix += f":l{limit}"
    if ufc_only:
        suffix += ":ufc"
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


T = TypeVar("T", bound=BaseModel)


def _parse_cached(cache_key: str, model: Type[T], cached: dict) -> Optional[T]:
    """캐시 데이터를 DTO로 변환. 실패 시 stale 캐시를 삭제하고 None 반환."""
    try:
        return model(**cached)
    except ValidationError:
        logger.warning(f"Stale cache detected for {cache_key}, deleting")
        try:
            redis_client.delete(cache_key)
        except Exception:
            pass
        return None


# ===========================
# Tab 1: Home
# ===========================

async def get_home(session: AsyncSession) -> HomeResponseDTO:
    cache_key = _cache_key("home")
    cached = _get_cached(cache_key)
    if cached:
        result = _parse_cached(cache_key, HomeResponseDTO, cached)
        if result:
            return result

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
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    ufc_only: bool = False,
) -> OverviewResponseDTO:
    cache_key = _cache_key("overview", weight_class_id, ufc_only=ufc_only)
    cached = _get_cached(cache_key)
    if cached:
        result = _parse_cached(cache_key, OverviewResponseDTO, cached)
        if result:
            return result

    try:
        finish_methods_data = await dashboard_repo.get_finish_methods(session, weight_class_id)
        weight_class_activity_data = await dashboard_repo.get_weight_class_activity(session)
        events_timeline_data = await dashboard_repo.get_events_timeline(session)

        wins_data = await dashboard_repo.get_leaderboard_wins(session, weight_class_id, ufc_only=ufc_only)
        winrate10_data = await dashboard_repo.get_leaderboard_winrate(session, 10, weight_class_id, ufc_only=ufc_only)
        winrate20_data = await dashboard_repo.get_leaderboard_winrate(session, 20, weight_class_id, ufc_only=ufc_only)
        winrate30_data = await dashboard_repo.get_leaderboard_winrate(session, 30, weight_class_id, ufc_only=ufc_only)

        rounds_data = await dashboard_repo.get_fight_duration_rounds(session, weight_class_id)
        avg_round = await dashboard_repo.get_fight_duration_avg_round(session, weight_class_id)
        avg_time = await dashboard_repo.get_fight_duration_avg_time(session, weight_class_id)

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
                avg_time_seconds=avg_time,
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
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10, limit: int = 10
) -> StrikingResponseDTO:
    cache_key = _cache_key("striking", weight_class_id, min_fights, limit)
    cached = _get_cached(cache_key)
    if cached:
        result = _parse_cached(cache_key, StrikingResponseDTO, cached)
        if result:
            return result

    try:
        strike_targets_data = await dashboard_repo.get_strike_targets(session, weight_class_id)
        ko_tko_leaders_data = await dashboard_repo.get_ko_tko_leaders(session, weight_class_id, limit)

        acc10 = await dashboard_repo.get_striking_accuracy(session, weight_class_id, 10, limit)
        acc20 = await dashboard_repo.get_striking_accuracy(session, weight_class_id, 20, limit)
        acc30 = await dashboard_repo.get_striking_accuracy(session, weight_class_id, 30, limit)

        sig10 = await dashboard_repo.get_sig_strikes_per_fight(session, weight_class_id, 10, limit)
        sig20 = await dashboard_repo.get_sig_strikes_per_fight(session, weight_class_id, 20, limit)
        sig30 = await dashboard_repo.get_sig_strikes_per_fight(session, weight_class_id, 30, limit)

        response = StrikingResponseDTO(
            strike_targets=[StrikeTargetDTO(**r) for r in strike_targets_data],
            striking_accuracy=StrikingAccuracyLeaderboardDTO(
                min10=[StrikingAccuracyDTO(**r) for r in acc10],
                min20=[StrikingAccuracyDTO(**r) for r in acc20],
                min30=[StrikingAccuracyDTO(**r) for r in acc30],
            ),
            ko_tko_leaders=[KoTkoLeaderDTO(**r) for r in ko_tko_leaders_data],
            sig_strikes_per_fight=SigStrikesLeaderboardDTO(
                min10=[SigStrikesPerFightDTO(**r) for r in sig10],
                min20=[SigStrikesPerFightDTO(**r) for r in sig20],
                min30=[SigStrikesPerFightDTO(**r) for r in sig30],
            ),
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_striking", str(e))


# ===========================
# Tab 4: Grappling
# ===========================

async def get_grappling(
    session: AsyncSession, weight_class_id: Optional[int] = None, min_fights: int = 10, limit: int = 10
) -> GrapplingResponseDTO:
    cache_key = _cache_key("grappling", weight_class_id, min_fights, limit)
    cached = _get_cached(cache_key)
    if cached:
        result = _parse_cached(cache_key, GrapplingResponseDTO, cached)
        if result:
            return result

    try:
        td10 = await dashboard_repo.get_takedown_accuracy(session, weight_class_id, 10, limit)
        td20 = await dashboard_repo.get_takedown_accuracy(session, weight_class_id, 20, limit)
        td30 = await dashboard_repo.get_takedown_accuracy(session, weight_class_id, 30, limit)
        sub_techniques_data = await dashboard_repo.get_submission_techniques(session, weight_class_id, limit)
        control_time_data = await dashboard_repo.get_control_time(session)
        ground_strikes_data = await dashboard_repo.get_ground_strikes(session, weight_class_id, min_fights, limit)
        sub_efficiency_fighters = await dashboard_repo.get_submission_efficiency_fighters(session, weight_class_id, min_fights, limit)
        avg_ratio = await dashboard_repo.get_submission_efficiency_avg_ratio(session, weight_class_id, min_fights)

        response = GrapplingResponseDTO(
            takedown_accuracy=TakedownLeaderboardDTO(
                min10=[TakedownAccuracyDTO(**r) for r in td10],
                min20=[TakedownAccuracyDTO(**r) for r in td20],
                min30=[TakedownAccuracyDTO(**r) for r in td30],
            ),
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
