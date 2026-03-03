from datetime import date
from typing import Optional, Literal, List

from sqlalchemy.ext.asyncio import AsyncSession

from common.models import WeightClassSchema
from fighter.dto import (
    FighterWithRankingsDTO, WeightClassRankingsDTO, RankedFighterDTO,
    FighterProfileDTO, FinishBreakdownDTO, FighterRecordDTO,
    StrikingStatsDTO, GrapplingStatsDTO, CareerStatsDTO,
    OpponentDTO, PerMatchBasicStatsDTO, PerMatchSigStrDTO, PerMatchStatsDTO,
    FightHistoryItemDTO, FighterDetailResponseDTO,
)
from fighter.models import FighterSchema
from fighter import repositories as fighter_repo
from match import repositories as match_repo
from fighter.exceptions import (
    FighterNotFoundError, FighterValidationError, FighterQueryError,
    FighterWeightClassError, FighterSearchError
)

async def _build_fighter_with_rankings(session: AsyncSession, fighter: FighterSchema) -> Optional[FighterWithRankingsDTO]:
    rankings = await fighter_repo.get_ranking_by_fighter_id(session, fighter.id)
    
    ranking_result = {}
    for ranking_obj in rankings:
        weight_class_name = WeightClassSchema.get_name_by_id(ranking_obj.weight_class_id)
        if weight_class_name:  # None 값 체크
            ranking_result[weight_class_name] = ranking_obj.ranking
    
    return FighterWithRankingsDTO(
        fighter=fighter,
        rankings=ranking_result
    )

async def get_fighter_by_id(session: AsyncSession, fighter_id: int) -> FighterWithRankingsDTO:
    """
    fighter_id로 fighter 조회.
    """
    # 입력 검증
    if not isinstance(fighter_id, int) or fighter_id <= 0:
        raise FighterValidationError("fighter_id", fighter_id, "fighter_id must be a positive integer")
    
    try:
        fighter = await fighter_repo.get_fighter_by_id(session, fighter_id)
        if not fighter:
            raise FighterNotFoundError(fighter_id, "id")

        return await _build_fighter_with_rankings(session, fighter)
    
    except FighterNotFoundError:
        raise
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_fighter_by_id", {"fighter_id": fighter_id}, str(e))
    

async def get_fighter_ranking_by_weight_class(session: AsyncSession, weight_class_name: str) -> WeightClassRankingsDTO:
    """
    특정 체급에 소속된 랭킹 있는 파이터들을 랭킹 순으로 조회
    """
    # 입력 검증
    if not weight_class_name or not weight_class_name.strip():
        raise FighterValidationError("weight_class_name", weight_class_name, "Weight class name cannot be empty")
    
    try:
        weight_class_id = WeightClassSchema.get_id_by_name(weight_class_name)
        if not weight_class_id:
            raise FighterWeightClassError(weight_class_name, f"Weight class '{weight_class_name}' not found")
            
        fighters = await fighter_repo.get_fighters_by_weight_class_ranking(session, weight_class_id)
        
        ranked_fighters = []
        for index, fighter in enumerate(fighters):
            ranked_fighters.append(
                RankedFighterDTO(
                    ranking=index + 1,
                    fighter=fighter
                )
            )
        
        ranked_fighters.sort(key=lambda x: x.ranking)
        
        return WeightClassRankingsDTO(
            weight_class_name=weight_class_name,
            rankings=ranked_fighters,
        )
    
    except FighterWeightClassError:
        raise
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_fighter_ranking_by_weight_class", {"weight_class_name": weight_class_name}, str(e))

async def get_top_fighters_by_record(session: AsyncSession, record: Literal["win", "loss", "draw"], weight_class_id: int = None, limit: int = 10) -> WeightClassRankingsDTO:
    """
    파이터의 기록(승,패,무) 기준으로 상위 limit개의 파이터 조회
    """
    # 입력 검증
    if record not in ["win", "loss", "draw"]:
        raise FighterValidationError("record", record, "record must be 'win', 'loss', or 'draw'")
    
    if not isinstance(limit, int) or limit <= 0:
        raise FighterValidationError("limit", limit, "limit must be a positive integer")
    
    if weight_class_id is not None and (not isinstance(weight_class_id, int) or weight_class_id <= 0):
        raise FighterValidationError("weight_class_id", weight_class_id, "weight_class_id must be a positive integer or None")
    
    try:
        fighter_with_rank = await fighter_repo.get_top_fighter_by_record(session, record, weight_class_id, limit)
        ranked_fighters = []
        
        weight_class_name = None
        if weight_class_id:
            weight_class_name = WeightClassSchema.get_name_by_id(weight_class_id)
        
        for rank_dict in fighter_with_rank:
            ranked_fighter = RankedFighterDTO(
                ranking=rank_dict["ranking"],
                fighter=rank_dict["fighter"],  
            )
            ranked_fighters.append(ranked_fighter)
        
        return WeightClassRankingsDTO(
            weight_class_name=weight_class_name,
            rankings=ranked_fighters,
        )
    
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_top_fighters_by_record", {"record": record, "weight_class_id": weight_class_id, "limit": limit}, str(e))

async def search_fighters(session: AsyncSession, search_term: str, limit: int = 10) -> List[FighterWithRankingsDTO]:
    """
    이름이나 닉네임으로 파이터를 검색하고 랭킹 정보와 함께 반환합니다.
    """
    # 입력 검증
    if not search_term or not search_term.strip():
        raise FighterValidationError("search_term", search_term, "Search term cannot be empty")
    
    if not isinstance(limit, int) or limit <= 0:
        raise FighterValidationError("limit", limit, "limit must be a positive integer")
    
    try:
        fighters = await fighter_repo.search_fighters_by_name(session, search_term, limit)
        
        results = []
        for fighter in fighters:
            fighter_with_rankings = await _build_fighter_with_rankings(session, fighter)
            if fighter_with_rankings:
                results.append(fighter_with_rankings)
        
        return results
    
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterSearchError({"search_term": search_term, "limit": limit}, str(e))

async def get_all_champions(session: AsyncSession) -> List[FighterWithRankingsDTO]:
    """
    현재 모든 챔피언들을 랭킹 정보와 함께 조회합니다.
    """
    try:
        champions = await fighter_repo.get_champions(session)
        
        results = []
        for champion in champions:
            champion_with_rankings = await _build_fighter_with_rankings(session, champion)
            if champion_with_rankings:
                results.append(champion_with_rankings)
        
        return results
    
    except Exception as e:
        raise FighterQueryError("get_all_champions", {}, str(e))


# ===========================
# Fighter Detail
# ===========================

def _calc_current_streak(rows: list[dict]) -> dict:
    if not rows:
        return {"type": "none", "count": 0}
    first = rows[0]["result"]
    if not first or first.lower() not in ("win", "loss"):
        return {"type": "none", "count": 0}
    streak_type = first.lower()
    count = 0
    for row in rows:
        if row["result"] and row["result"].lower() == streak_type:
            count += 1
        else:
            break
    return {"type": streak_type, "count": count}


def _calc_age(birthdate_val) -> Optional[int]:
    try:
        if birthdate_val is None:
            return None
        if isinstance(birthdate_val, date):
            bd = birthdate_val
        else:
            bd = date.fromisoformat(str(birthdate_val))
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except (ValueError, TypeError):
        return None


async def get_fighter_detail(session: AsyncSession, fighter_id: int) -> FighterDetailResponseDTO:
    if not isinstance(fighter_id, int) or fighter_id <= 0:
        raise FighterValidationError("fighter_id", fighter_id, "fighter_id must be a positive integer")

    try:
        # 1. fighter 기본 정보
        fighter = await fighter_repo.get_fighter_by_id(session, fighter_id)
        if not fighter:
            raise FighterNotFoundError(fighter_id, "id")

        # 2. rankings
        rankings_list = await fighter_repo.get_ranking_by_fighter_id(session, fighter_id)
        rankings_dict: dict[str, int] = {}
        for r in rankings_list:
            wc_name = WeightClassSchema.get_name_by_id(r.weight_class_id)
            if wc_name:
                rankings_dict[wc_name] = r.ranking

        # 3. fight history
        fight_history_rows = await fighter_repo.get_fight_history(session, fighter_id)

        # 4. finish breakdown
        finish_data = await fighter_repo.get_finish_breakdown(session, fighter_id)

        # 5. career aggregate stats (기존 함수 재사용)
        basic_agg = await match_repo.get_fighter_basic_stats_aggregate(session, fighter_id)
        sig_str_agg = await match_repo.get_fighter_sig_str_stats_aggregate(session, fighter_id)

        # 6. per-match stats 배치 조회
        fm_ids = [row["fighter_match_id"] for row in fight_history_rows]
        per_match_map = await fighter_repo.get_per_match_stats(session, fm_ids) if fm_ids else {}

        # === Profile ===
        birthdate_str = str(fighter.birthdate) if fighter.birthdate else None
        profile = FighterProfileDTO(
            id=fighter.id,
            name=fighter.name,
            nickname=fighter.nickname,
            nationality=fighter.nationality,
            stance=fighter.stance,
            belt=fighter.belt,
            height_cm=fighter.height_cm if fighter.height_cm else None,
            weight_kg=fighter.weight_kg if fighter.weight_kg else None,
            reach_cm=fighter.reach_cm if fighter.reach_cm else None,
            birthdate=birthdate_str,
            age=_calc_age(fighter.birthdate),
            rankings=rankings_dict,
        )

        # === Record ===
        total = fighter.wins + fighter.losses + fighter.draws
        win_rate = round(fighter.wins / total * 100, 1) if total > 0 else 0.0
        record = FighterRecordDTO(
            wins=fighter.wins,
            losses=fighter.losses,
            draws=fighter.draws,
            win_rate=win_rate,
            current_streak=_calc_current_streak(fight_history_rows),
            finish_breakdown=FinishBreakdownDTO(**finish_data),
        )

        # === Stats ===
        match_count = basic_agg.match_count
        if match_count > 0:
            sig_acc = round(basic_agg.sig_str_landed / basic_agg.sig_str_attempted * 100, 1) if basic_agg.sig_str_attempted > 0 else 0.0
            td_acc = round(basic_agg.td_landed / basic_agg.td_attempted * 100, 1) if basic_agg.td_attempted > 0 else 0.0
            avg_ctrl = basic_agg.control_time_seconds // match_count if match_count > 0 else 0

            striking = StrikingStatsDTO(
                sig_str_landed=basic_agg.sig_str_landed,
                sig_str_attempted=basic_agg.sig_str_attempted,
                sig_str_accuracy=sig_acc,
                knockdowns=basic_agg.knockdowns,
                head_landed=sig_str_agg.head_strikes_landed,
                head_attempted=sig_str_agg.head_strikes_attempts,
                body_landed=sig_str_agg.body_strikes_landed,
                body_attempted=sig_str_agg.body_strikes_attempts,
                leg_landed=sig_str_agg.leg_strikes_landed,
                leg_attempted=sig_str_agg.leg_strikes_attempts,
                match_count=match_count,
            )
            grappling = GrapplingStatsDTO(
                td_landed=basic_agg.td_landed,
                td_attempted=basic_agg.td_attempted,
                td_accuracy=td_acc,
                control_time_seconds=basic_agg.control_time_seconds,
                avg_control_time_seconds=avg_ctrl,
                submission_attempts=basic_agg.submission_attempts,
                match_count=match_count,
            )
            stats = CareerStatsDTO(striking=striking, grappling=grappling)
        else:
            stats = None

        # === Fight History ===
        fight_history: list[FightHistoryItemDTO] = []
        for row in fight_history_rows:
            # opponent가 없는 row는 건너뛰기
            if not row.get("opponent_id"):
                continue

            # weight_class 이름 변환
            wc_name = None
            if row.get("weight_class_id"):
                wc_name = WeightClassSchema.get_name_by_id(row["weight_class_id"])

            # per-match stats 매핑
            fm_id = row["fighter_match_id"]
            per_match = per_match_map.get(fm_id)
            match_stats = None
            if per_match:
                basic_schema = per_match.get("basic")
                sig_str_schema = per_match.get("sig_str")
                basic_dto = None
                sig_str_dto = None
                if basic_schema:
                    basic_dto = PerMatchBasicStatsDTO(
                        knockdowns=basic_schema.knockdowns or 0,
                        sig_str_landed=basic_schema.sig_str_landed or 0,
                        sig_str_attempted=basic_schema.sig_str_attempted or 0,
                        total_str_landed=basic_schema.total_str_landed or 0,
                        total_str_attempted=basic_schema.total_str_attempted or 0,
                        td_landed=basic_schema.td_landed or 0,
                        td_attempted=basic_schema.td_attempted or 0,
                        control_time_seconds=basic_schema.control_time_seconds or 0,
                        submission_attempts=basic_schema.submission_attempts or 0,
                    )
                if sig_str_schema:
                    sig_str_dto = PerMatchSigStrDTO(
                        head_landed=sig_str_schema.head_strikes_landed or 0,
                        head_attempted=sig_str_schema.head_strikes_attempts or 0,
                        body_landed=sig_str_schema.body_strikes_landed or 0,
                        body_attempted=sig_str_schema.body_strikes_attempts or 0,
                        leg_landed=sig_str_schema.leg_strikes_landed or 0,
                        leg_attempted=sig_str_schema.leg_strikes_attempts or 0,
                        clinch_landed=sig_str_schema.clinch_strikes_landed or 0,
                        clinch_attempted=sig_str_schema.clinch_strikes_attempts or 0,
                        ground_landed=sig_str_schema.ground_strikes_landed or 0,
                        ground_attempted=sig_str_schema.ground_strikes_attempts or 0,
                    )
                if basic_dto or sig_str_dto:
                    match_stats = PerMatchStatsDTO(basic=basic_dto, sig_str=sig_str_dto)

            fight_history.append(FightHistoryItemDTO(
                match_id=row["match_id"],
                result=row["result"] or "Unknown",
                method=row.get("method"),
                round=row.get("result_round"),
                time=row.get("time"),
                event_id=row.get("event_id"),
                event_name=row.get("event_name"),
                event_date=row.get("event_date"),
                weight_class=wc_name,
                is_main_event=row.get("is_main_event") or False,
                opponent=OpponentDTO(
                    id=row["opponent_id"],
                    name=row["opponent_name"],
                    nationality=row.get("opponent_nationality"),
                ),
                stats=match_stats,
            ))

        return FighterDetailResponseDTO(
            profile=profile,
            record=record,
            stats=stats,
            fight_history=fight_history,
        )

    except FighterNotFoundError:
        raise
    except FighterValidationError:
        raise
    except Exception as e:
        raise FighterQueryError("get_fighter_detail", {"fighter_id": fighter_id}, str(e))
