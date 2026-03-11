from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from fighter.models import FighterSchema


class FighterWithRankingsDTO(BaseModel):
    """Fighter 기본 정보 + 랭킹 정보 (가장 기본적인 조합)"""
    fighter: FighterSchema
    rankings: Dict[str, int] = Field(
        example={"Lightweight": 5, "Welterweight": 12}
    )


class RankedFighterDTO(BaseModel):
    """랭킹이 있는 파이터 정보"""
    ranking: int = Field(description="현재 랭킹 순위")
    fighter: FighterSchema = Field(description="파이터 기본 정보")


class WeightClassRankingsDTO(BaseModel):
    """특정 체급의 랭킹 리스트"""
    weight_class_name: Optional[str] = None
    rankings: List[RankedFighterDTO] = Field(
        example=[
            {"ranking": 1, "fighter": {"name": "Islam Makhachev"}},
            {"ranking": 2, "fighter": {"name": "Charles Oliveira"}}
        ]
    )


# ===========================
# Fighter Detail DTOs
# ===========================

class FighterProfileDTO(BaseModel):
    id: int
    name: str
    nickname: Optional[str] = None
    nationality: Optional[str] = None
    stance: Optional[str] = None
    belt: bool = False
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    reach_cm: Optional[float] = None
    birthdate: Optional[str] = None
    age: Optional[int] = None
    weight_class: Optional[str] = None
    rankings: Dict[str, int] = {}


class FinishBreakdownDTO(BaseModel):
    ko_tko: int = 0
    submission: int = 0
    decision: int = 0


class FighterRecordDTO(BaseModel):
    wins: int = 0
    losses: int = 0
    draws: int = 0
    win_rate: float = 0.0
    current_streak: Dict[str, Any] = {"type": "none", "count": 0}
    finish_breakdown: FinishBreakdownDTO = FinishBreakdownDTO()


class StrikingStatsDTO(BaseModel):
    sig_str_landed: int = 0
    sig_str_attempted: int = 0
    sig_str_accuracy: float = 0.0
    knockdowns: int = 0
    opp_knockdowns: int = 0
    head_landed: int = 0
    head_attempted: int = 0
    body_landed: int = 0
    body_attempted: int = 0
    leg_landed: int = 0
    leg_attempted: int = 0
    match_count: int = 0


class GrapplingStatsDTO(BaseModel):
    td_landed: int = 0
    td_attempted: int = 0
    td_accuracy: float = 0.0
    td_defense_rate: float = 0.0
    opp_td_landed: int = 0
    opp_td_attempted: int = 0
    control_time_seconds: int = 0
    avg_control_time_seconds: int = 0
    submission_attempts: int = 0
    top_submission: Optional[str] = None
    match_count: int = 0


class CareerStatsDTO(BaseModel):
    striking: StrikingStatsDTO = StrikingStatsDTO()
    grappling: GrapplingStatsDTO = GrapplingStatsDTO()


class OpponentDTO(BaseModel):
    id: int
    name: str
    nationality: Optional[str] = None


class PerMatchBasicStatsDTO(BaseModel):
    knockdowns: int = 0
    sig_str_landed: int = 0
    sig_str_attempted: int = 0
    total_str_landed: int = 0
    total_str_attempted: int = 0
    td_landed: int = 0
    td_attempted: int = 0
    control_time_seconds: int = 0
    submission_attempts: int = 0


class PerMatchSigStrDTO(BaseModel):
    head_landed: int = 0
    head_attempted: int = 0
    body_landed: int = 0
    body_attempted: int = 0
    leg_landed: int = 0
    leg_attempted: int = 0
    clinch_landed: int = 0
    clinch_attempted: int = 0
    ground_landed: int = 0
    ground_attempted: int = 0


class PerMatchStatsDTO(BaseModel):
    basic: Optional[PerMatchBasicStatsDTO] = None
    sig_str: Optional[PerMatchSigStrDTO] = None


class FightHistoryItemDTO(BaseModel):
    match_id: int
    result: str
    method: Optional[str] = None
    round: Optional[int] = None
    time: Optional[str] = None
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    event_date: Optional[date] = None
    weight_class: Optional[str] = None
    is_main_event: bool = False
    opponent: OpponentDTO
    stats: Optional[PerMatchStatsDTO] = None


class FighterDetailResponseDTO(BaseModel):
    profile: FighterProfileDTO
    record: FighterRecordDTO
    stats: Optional[CareerStatsDTO] = None
    fight_history: List[FightHistoryItemDTO] = []
