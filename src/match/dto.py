from typing import List, Optional
from pydantic import BaseModel, Field

from fighter.models import FighterSchema
from match.models import (
    MatchSchema,
    BasicMatchStatSchema,
    SigStrMatchStatSchema
)


class FighterResultDTO(BaseModel):
    """파이터와 경기 결과 정보"""
    fighter: FighterSchema
    result: Optional[str] = Field(None, description="경기 결과 (Win/Loss/Draw/NC)")


class MatchWithFightersDTO(BaseModel):
    """매치 정보와 참가 파이터들"""
    match: MatchSchema
    fighters: List[FighterResultDTO] = Field(default_factory=list)


class MatchWithResultDTO(BaseModel):
    """매치 정보와 승자/패자 정보"""
    match: MatchSchema
    fighters: List[FighterResultDTO] = Field(default_factory=list)
    winner: Optional[FighterResultDTO] = None
    loser: Optional[FighterResultDTO] = None
    draw_fighters: Optional[List[FighterResultDTO]] = None


class FighterMatchStatDTO(BaseModel):
    """개별 파이터의 경기 통계"""
    fighter_id: int
    result: Optional[str] = None
    basic_stats: Optional[BasicMatchStatSchema] = None
    sig_str_stats: Optional[SigStrMatchStatSchema] = None


class CombinedMatchStatsDTO(BaseModel):
    """경기 합산 통계"""
    total_strikes_attempted: int = 0
    total_strikes_landed: int = 0
    total_sig_str_attempted: int = 0
    total_sig_str_landed: int = 0
    total_takedowns_attempted: int = 0
    total_takedowns_landed: int = 0
    total_control_time: int = 0
    total_knockdowns: int = 0
    total_submission_attempts: int = 0


class MatchStatisticsDTO(BaseModel):
    """매치 전체 통계 정보"""
    match_id: int
    fighter_stats: List[FighterMatchStatDTO] = Field(default_factory=list)
    combined_stats: CombinedMatchStatsDTO = Field(default_factory=CombinedMatchStatsDTO)


class MatchDetailDTO(BaseModel):
    """매치 상세 정보 (참가자 + 통계)"""
    match: MatchSchema
    fighters: List[FighterResultDTO] = Field(default_factory=list)
    statistics: Optional[MatchStatisticsDTO] = None


class FighterBasicStatsAggregateDTO(BaseModel):
    """파이터 기본 통계 집계"""
    knockdowns: int = 0
    control_time_seconds: int = 0
    submission_attempts: int = 0
    sig_str_landed: int = 0
    sig_str_attempted: int = 0
    total_str_landed: int = 0
    total_str_attempted: int = 0
    td_landed: int = 0
    td_attempted: int = 0
    match_count: int = 0


class FighterSigStrStatsAggregateDTO(BaseModel):
    """파이터 유효 타격 통계 집계"""
    head_strikes_landed: int = 0
    head_strikes_attempts: int = 0
    body_strikes_landed: int = 0
    body_strikes_attempts: int = 0
    leg_strikes_landed: int = 0
    leg_strikes_attempts: int = 0
    takedowns_landed: int = 0
    takedowns_attempts: int = 0
    clinch_strikes_landed: int = 0
    clinch_strikes_attempts: int = 0
    ground_strikes_landed: int = 0
    ground_strikes_attempts: int = 0
    match_count: int = 0
