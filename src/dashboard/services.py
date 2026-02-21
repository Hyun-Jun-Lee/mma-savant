"""
Dashboard 서비스 레이어
Redis 캐싱 + Repository 호출 조합
"""
import json
import logging
from typing import List, Optional, Type, TypeVar
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


def _chart_cache_key(
    chart_name: str,
    weight_class_id: Optional[int] = None,
    min_fights: Optional[int] = None,
    limit: Optional[int] = None,
    ufc_only: bool = False,
) -> str:
    """차트별 캐시 키 생성."""
    wc = str(weight_class_id) if weight_class_id is not None else "all"
    key = f"dashboard:chart:{chart_name}:{wc}"
    if min_fights is not None and min_fights != 10:
        key += f":{min_fights}"
    if limit is not None and limit != 10:
        key += f":{limit}"
    if ufc_only:
        key += ":ufc"
    return key


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


def _parse_cached_list(cache_key: str, model: Type[T], cached: dict) -> Optional[List[T]]:
    """캐시 데이터에서 items 리스트를 DTO 리스트로 변환."""
    try:
        return [model(**item) for item in cached["items"]]
    except (ValidationError, KeyError, TypeError):
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
# Chart-level service functions
# ===========================

# --- Overview Charts ---

async def get_chart_finish_methods(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
) -> List[FinishMethodDTO]:
    cache_key = _chart_cache_key("finish_methods", weight_class_id)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached_list(cache_key, FinishMethodDTO, cached)
        if parsed is not None:
            return parsed

    try:
        data = await dashboard_repo.get_finish_methods(session, weight_class_id)
        result = [FinishMethodDTO(**r) for r in data]
        _set_cache(cache_key, {"items": [item.model_dump() for item in result]})
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_finish_methods", str(e))


async def get_chart_fight_duration(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
) -> FightDurationDTO:
    cache_key = _chart_cache_key("fight_duration", weight_class_id)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached(cache_key, FightDurationDTO, cached)
        if parsed is not None:
            return parsed

    try:
        rounds_data = await dashboard_repo.get_fight_duration_rounds(session, weight_class_id)
        avg_round = await dashboard_repo.get_fight_duration_avg_round(session, weight_class_id)
        avg_time = await dashboard_repo.get_fight_duration_avg_time(session, weight_class_id)

        result = FightDurationDTO(
            rounds=[FightDurationRoundDTO(**r) for r in rounds_data],
            avg_round=avg_round,
            avg_time_seconds=avg_time,
        )
        _set_cache(cache_key, result.model_dump())
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_fight_duration", str(e))


async def get_chart_leaderboard(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    ufc_only: bool = False,
) -> LeaderboardDTO:
    cache_key = _chart_cache_key("leaderboard", weight_class_id, ufc_only=ufc_only)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached(cache_key, LeaderboardDTO, cached)
        if parsed is not None:
            return parsed

    try:
        wins_data = await dashboard_repo.get_leaderboard_wins(session, weight_class_id, ufc_only=ufc_only)
        winrate10_data = await dashboard_repo.get_leaderboard_winrate(session, 10, weight_class_id, ufc_only=ufc_only)
        winrate20_data = await dashboard_repo.get_leaderboard_winrate(session, 20, weight_class_id, ufc_only=ufc_only)
        winrate30_data = await dashboard_repo.get_leaderboard_winrate(session, 30, weight_class_id, ufc_only=ufc_only)

        result = LeaderboardDTO(
            wins=[LeaderboardFighterDTO(**r) for r in wins_data],
            winrate_min10=[LeaderboardFighterDTO(**r) for r in winrate10_data],
            winrate_min20=[LeaderboardFighterDTO(**r) for r in winrate20_data],
            winrate_min30=[LeaderboardFighterDTO(**r) for r in winrate30_data],
        )
        _set_cache(cache_key, result.model_dump())
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_leaderboard", str(e))


# --- Striking Charts ---

async def get_chart_strike_targets(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
) -> List[StrikeTargetDTO]:
    cache_key = _chart_cache_key("strike_targets", weight_class_id)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached_list(cache_key, StrikeTargetDTO, cached)
        if parsed is not None:
            return parsed

    try:
        data = await dashboard_repo.get_strike_targets(session, weight_class_id)
        result = [StrikeTargetDTO(**r) for r in data]
        _set_cache(cache_key, {"items": [item.model_dump() for item in result]})
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_strike_targets", str(e))


async def get_chart_striking_accuracy(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> StrikingAccuracyLeaderboardDTO:
    cache_key = _chart_cache_key("striking_accuracy", weight_class_id, min_fights, limit)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached(cache_key, StrikingAccuracyLeaderboardDTO, cached)
        if parsed is not None:
            return parsed

    try:
        acc10 = await dashboard_repo.get_striking_accuracy(session, weight_class_id, 10, limit)
        acc20 = await dashboard_repo.get_striking_accuracy(session, weight_class_id, 20, limit)
        acc30 = await dashboard_repo.get_striking_accuracy(session, weight_class_id, 30, limit)

        result = StrikingAccuracyLeaderboardDTO(
            min10=[StrikingAccuracyDTO(**r) for r in acc10],
            min20=[StrikingAccuracyDTO(**r) for r in acc20],
            min30=[StrikingAccuracyDTO(**r) for r in acc30],
        )
        _set_cache(cache_key, result.model_dump())
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_striking_accuracy", str(e))


async def get_chart_ko_tko_leaders(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    limit: int = 10,
) -> List[KoTkoLeaderDTO]:
    cache_key = _chart_cache_key("ko_tko_leaders", weight_class_id, limit=limit)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached_list(cache_key, KoTkoLeaderDTO, cached)
        if parsed is not None:
            return parsed

    try:
        data = await dashboard_repo.get_ko_tko_leaders(session, weight_class_id, limit)
        result = [KoTkoLeaderDTO(**r) for r in data]
        _set_cache(cache_key, {"items": [item.model_dump() for item in result]})
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_ko_tko_leaders", str(e))


async def get_chart_sig_strikes(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> SigStrikesLeaderboardDTO:
    cache_key = _chart_cache_key("sig_strikes", weight_class_id, min_fights, limit)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached(cache_key, SigStrikesLeaderboardDTO, cached)
        if parsed is not None:
            return parsed

    try:
        sig10 = await dashboard_repo.get_sig_strikes_per_fight(session, weight_class_id, 10, limit)
        sig20 = await dashboard_repo.get_sig_strikes_per_fight(session, weight_class_id, 20, limit)
        sig30 = await dashboard_repo.get_sig_strikes_per_fight(session, weight_class_id, 30, limit)

        result = SigStrikesLeaderboardDTO(
            min10=[SigStrikesPerFightDTO(**r) for r in sig10],
            min20=[SigStrikesPerFightDTO(**r) for r in sig20],
            min30=[SigStrikesPerFightDTO(**r) for r in sig30],
        )
        _set_cache(cache_key, result.model_dump())
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_sig_strikes", str(e))


# --- Grappling Charts ---

async def get_chart_takedown_accuracy(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> TakedownLeaderboardDTO:
    cache_key = _chart_cache_key("takedown_accuracy", weight_class_id, min_fights, limit)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached(cache_key, TakedownLeaderboardDTO, cached)
        if parsed is not None:
            return parsed

    try:
        td10 = await dashboard_repo.get_takedown_accuracy(session, weight_class_id, 10, limit)
        td20 = await dashboard_repo.get_takedown_accuracy(session, weight_class_id, 20, limit)
        td30 = await dashboard_repo.get_takedown_accuracy(session, weight_class_id, 30, limit)

        result = TakedownLeaderboardDTO(
            min10=[TakedownAccuracyDTO(**r) for r in td10],
            min20=[TakedownAccuracyDTO(**r) for r in td20],
            min30=[TakedownAccuracyDTO(**r) for r in td30],
        )
        _set_cache(cache_key, result.model_dump())
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_takedown_accuracy", str(e))


async def get_chart_submission_techniques(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
) -> List[SubmissionTechniqueDTO]:
    cache_key = _chart_cache_key("sub_techniques", weight_class_id)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached_list(cache_key, SubmissionTechniqueDTO, cached)
        if parsed is not None:
            return parsed

    try:
        data = await dashboard_repo.get_submission_techniques(session, weight_class_id)
        result = [SubmissionTechniqueDTO(**r) for r in data]
        _set_cache(cache_key, {"items": [item.model_dump() for item in result]})
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_submission_techniques", str(e))


async def get_chart_ground_strikes(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> List[GroundStrikesDTO]:
    cache_key = _chart_cache_key("ground_strikes", weight_class_id, min_fights, limit)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached_list(cache_key, GroundStrikesDTO, cached)
        if parsed is not None:
            return parsed

    try:
        data = await dashboard_repo.get_ground_strikes(session, weight_class_id, min_fights, limit)
        result = [GroundStrikesDTO(**r) for r in data]
        _set_cache(cache_key, {"items": [item.model_dump() for item in result]})
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_ground_strikes", str(e))


async def get_chart_submission_efficiency(
    session: AsyncSession,
    weight_class_id: Optional[int] = None,
    min_fights: int = 10,
    limit: int = 10,
) -> SubmissionEfficiencyDTO:
    cache_key = _chart_cache_key("sub_efficiency", weight_class_id, min_fights, limit)
    cached = _get_cached(cache_key)
    if cached:
        parsed = _parse_cached(cache_key, SubmissionEfficiencyDTO, cached)
        if parsed is not None:
            return parsed

    try:
        fighters_data = await dashboard_repo.get_submission_efficiency_fighters(session, weight_class_id, min_fights, limit)
        avg_ratio = await dashboard_repo.get_submission_efficiency_avg_ratio(session, weight_class_id, min_fights)

        result = SubmissionEfficiencyDTO(
            fighters=[SubmissionEfficiencyFighterDTO(**r) for r in fighters_data],
            avg_efficiency_ratio=avg_ratio,
        )
        _set_cache(cache_key, result.model_dump())
        return result
    except Exception as e:
        raise DashboardQueryError("get_chart_submission_efficiency", str(e))


# ===========================
# Tab 2: Overview (uses chart functions)
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
        finish_methods = await get_chart_finish_methods(session, weight_class_id)
        weight_class_activity_data = await dashboard_repo.get_weight_class_activity(session)
        events_timeline_data = await dashboard_repo.get_events_timeline(session)
        leaderboard = await get_chart_leaderboard(session, weight_class_id, ufc_only)
        fight_duration = await get_chart_fight_duration(session, weight_class_id)

        response = OverviewResponseDTO(
            finish_methods=finish_methods,
            weight_class_activity=[WeightClassActivityDTO(**r) for r in weight_class_activity_data],
            events_timeline=[EventTimelineDTO(**r) for r in events_timeline_data],
            leaderboard=leaderboard,
            fight_duration=fight_duration,
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_overview", str(e))


# ===========================
# Tab 3: Striking (uses chart functions)
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
        strike_targets = await get_chart_strike_targets(session, weight_class_id)
        striking_accuracy = await get_chart_striking_accuracy(session, weight_class_id, min_fights, limit)
        ko_tko_leaders = await get_chart_ko_tko_leaders(session, weight_class_id, limit)
        sig_strikes = await get_chart_sig_strikes(session, weight_class_id, min_fights, limit)

        response = StrikingResponseDTO(
            strike_targets=strike_targets,
            striking_accuracy=striking_accuracy,
            ko_tko_leaders=ko_tko_leaders,
            sig_strikes_per_fight=sig_strikes,
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_striking", str(e))


# ===========================
# Tab 4: Grappling (uses chart functions)
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
        takedown_accuracy = await get_chart_takedown_accuracy(session, weight_class_id, min_fights, limit)
        submission_techniques = await get_chart_submission_techniques(session, weight_class_id)
        control_time_data = await dashboard_repo.get_control_time(session)
        ground_strikes = await get_chart_ground_strikes(session, weight_class_id, min_fights, limit)
        submission_efficiency = await get_chart_submission_efficiency(session, weight_class_id, min_fights, limit)

        response = GrapplingResponseDTO(
            takedown_accuracy=takedown_accuracy,
            submission_techniques=submission_techniques,
            control_time=[ControlTimeDTO(**r) for r in control_time_data],
            ground_strikes=ground_strikes,
            submission_efficiency=submission_efficiency,
        )

        _set_cache(cache_key, response.model_dump())
        return response

    except Exception as e:
        raise DashboardQueryError("get_grappling", str(e))
