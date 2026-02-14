"""
Dashboard 도메인 DTO 클래스들
탭별 aggregate 응답 모델 정의
"""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, ConfigDict


# ===== Tab 1: Home =====

class SummaryDTO(BaseModel):
    total_fighters: int
    total_matches: int
    total_events: int

    model_config = ConfigDict(from_attributes=True)


class RecentEventDTO(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    event_date: Optional[date] = None
    total_fights: int
    main_event: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UpcomingEventDTO(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    event_date: Optional[date] = None
    days_until: int

    model_config = ConfigDict(from_attributes=True)


class RankingFighterDTO(BaseModel):
    ranking: int
    fighter_name: str
    wins: int
    losses: int
    draws: int

    model_config = ConfigDict(from_attributes=True)


class DivisionRankingDTO(BaseModel):
    weight_class_id: int
    weight_class: str
    fighters: List[RankingFighterDTO]

    model_config = ConfigDict(from_attributes=True)


class HomeResponseDTO(BaseModel):
    summary: SummaryDTO
    recent_events: List[RecentEventDTO]
    upcoming_events: List[UpcomingEventDTO]
    rankings: List[DivisionRankingDTO]

    model_config = ConfigDict(from_attributes=True)


# ===== Tab 2: Overview =====

class FinishMethodDTO(BaseModel):
    method_category: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class WeightClassActivityDTO(BaseModel):
    weight_class: str
    total_fights: int
    ko_count: int
    tko_count: int
    sub_count: int
    finish_rate: float
    ko_rate: float
    tko_rate: float
    sub_rate: float

    model_config = ConfigDict(from_attributes=True)


class EventTimelineDTO(BaseModel):
    year: int
    event_count: int

    model_config = ConfigDict(from_attributes=True)


class LeaderboardFighterDTO(BaseModel):
    name: str
    wins: int
    losses: int
    draws: int
    win_rate: float

    model_config = ConfigDict(from_attributes=True)


class LeaderboardDTO(BaseModel):
    wins: List[LeaderboardFighterDTO]
    winrate_min10: List[LeaderboardFighterDTO]
    winrate_min20: List[LeaderboardFighterDTO]
    winrate_min30: List[LeaderboardFighterDTO]

    model_config = ConfigDict(from_attributes=True)


class FightDurationRoundDTO(BaseModel):
    result_round: int
    fight_count: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class FightDurationDTO(BaseModel):
    rounds: List[FightDurationRoundDTO]
    avg_round: float

    model_config = ConfigDict(from_attributes=True)


class OverviewResponseDTO(BaseModel):
    finish_methods: List[FinishMethodDTO]
    weight_class_activity: List[WeightClassActivityDTO]
    events_timeline: List[EventTimelineDTO]
    leaderboard: LeaderboardDTO
    fight_duration: FightDurationDTO

    model_config = ConfigDict(from_attributes=True)


# ===== Tab 3: Striking =====

class StrikeTargetDTO(BaseModel):
    target: str
    landed: int

    model_config = ConfigDict(from_attributes=True)


class StrikingAccuracyDTO(BaseModel):
    name: str
    total_sig_landed: int
    total_sig_attempted: int
    accuracy: float

    model_config = ConfigDict(from_attributes=True)


class KoTkoLeaderDTO(BaseModel):
    name: str
    ko_finishes: int
    tko_finishes: int
    total_ko_tko: int

    model_config = ConfigDict(from_attributes=True)


class SigStrikesPerFightDTO(BaseModel):
    name: str
    sig_str_per_fight: float
    total_fights: int

    model_config = ConfigDict(from_attributes=True)


class StrikingResponseDTO(BaseModel):
    strike_targets: List[StrikeTargetDTO]
    striking_accuracy: List[StrikingAccuracyDTO]
    ko_tko_leaders: List[KoTkoLeaderDTO]
    sig_strikes_per_fight: List[SigStrikesPerFightDTO]

    model_config = ConfigDict(from_attributes=True)


# ===== Tab 4: Grappling =====

class TakedownAccuracyDTO(BaseModel):
    name: str
    total_td_landed: int
    total_td_attempted: int
    td_accuracy: float

    model_config = ConfigDict(from_attributes=True)


class SubmissionTechniqueDTO(BaseModel):
    technique: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class ControlTimeDTO(BaseModel):
    weight_class: str
    avg_control_seconds: int
    total_fights: int

    model_config = ConfigDict(from_attributes=True)


class GroundStrikesDTO(BaseModel):
    name: str
    total_ground_landed: int
    total_ground_attempted: int
    accuracy: float

    model_config = ConfigDict(from_attributes=True)


class SubmissionEfficiencyFighterDTO(BaseModel):
    name: str
    total_sub_attempts: int
    sub_finishes: int

    model_config = ConfigDict(from_attributes=True)


class SubmissionEfficiencyDTO(BaseModel):
    fighters: List[SubmissionEfficiencyFighterDTO]
    avg_efficiency_ratio: float

    model_config = ConfigDict(from_attributes=True)


class GrapplingResponseDTO(BaseModel):
    takedown_accuracy: List[TakedownAccuracyDTO]
    submission_techniques: List[SubmissionTechniqueDTO]
    control_time: List[ControlTimeDTO]
    ground_strikes: List[GroundStrikesDTO]
    submission_efficiency: SubmissionEfficiencyDTO

    model_config = ConfigDict(from_attributes=True)
