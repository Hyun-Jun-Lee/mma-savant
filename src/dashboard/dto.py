"""
Dashboard 도메인 DTO 클래스들
탭별 aggregate 응답 모델 정의
"""
from typing import Dict, List, Optional
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
    fighter_id: int
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


class CategoryLeaderDTO(BaseModel):
    category: str
    label: str
    fighter_id: int
    name: str
    value: float
    unit: str

    model_config = ConfigDict(from_attributes=True)


class EventMapDTO(BaseModel):
    location: str
    latitude: float
    longitude: float
    event_count: int
    last_event_date: Optional[date] = None
    last_event_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NationalityDistributionDTO(BaseModel):
    nationality: str
    fighter_count: int

    model_config = ConfigDict(from_attributes=True)


class HomeResponseDTO(BaseModel):
    summary: SummaryDTO
    recent_events: List[RecentEventDTO]
    upcoming_events: List[UpcomingEventDTO]
    rankings: List[DivisionRankingDTO]
    category_leaders: List[CategoryLeaderDTO] = []
    event_map: List[EventMapDTO] = []
    nationality_distribution: List[NationalityDistributionDTO] = []

    model_config = ConfigDict(from_attributes=True)


# ===== Tab 2: Overview =====

class FinishMethodDTO(BaseModel):
    method_category: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class WeightClassActivityDTO(BaseModel):
    weight_class: str
    total_fights: int
    ko_tko_count: int
    sub_count: int
    finish_rate: float
    ko_tko_rate: float
    sub_rate: float

    model_config = ConfigDict(from_attributes=True)


class EventTimelineDTO(BaseModel):
    year: int
    event_count: int

    model_config = ConfigDict(from_attributes=True)


class LeaderboardFighterDTO(BaseModel):
    fighter_id: int
    name: str
    wins: int
    losses: int
    draws: int
    ko_tko_wins: int = 0
    sub_wins: int = 0
    dec_wins: int = 0

    model_config = ConfigDict(from_attributes=True)


class WinStreakFighterDTO(BaseModel):
    fighter_id: int
    name: str
    win_streak: int
    wins: int
    losses: int
    draws: int

    model_config = ConfigDict(from_attributes=True)


class LoseStreakFighterDTO(BaseModel):
    fighter_id: int
    name: str
    lose_streak: int
    wins: int
    losses: int
    draws: int

    model_config = ConfigDict(from_attributes=True)


class LeaderboardDTO(BaseModel):
    wins: List[LeaderboardFighterDTO]
    win_streak: List[WinStreakFighterDTO] = []
    lose_streak: List[LoseStreakFighterDTO] = []

    model_config = ConfigDict(from_attributes=True)


class FightDurationRoundDTO(BaseModel):
    result_round: int
    fight_count: int
    percentage: float
    ko_tko: int = 0
    submission: int = 0
    decision_other: int = 0

    model_config = ConfigDict(from_attributes=True)


class FightDurationDTO(BaseModel):
    rounds: List[FightDurationRoundDTO]
    avg_round: float
    avg_time_seconds: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class FinishRateTrendDTO(BaseModel):
    year: int
    total_fights: int
    ko_tko_rate: float
    sub_rate: float
    dec_rate: float

    model_config = ConfigDict(from_attributes=True)


class OverviewResponseDTO(BaseModel):
    finish_methods: List[FinishMethodDTO]
    weight_class_activity: List[WeightClassActivityDTO]
    events_timeline: List[EventTimelineDTO]
    leaderboard: LeaderboardDTO
    fight_duration: FightDurationDTO
    finish_rate_trend: List[FinishRateTrendDTO] = []

    model_config = ConfigDict(from_attributes=True)


# ===== Tab 3: Striking =====

class StrikeTargetDTO(BaseModel):
    target: str
    landed: int

    model_config = ConfigDict(from_attributes=True)


class StrikingAccuracyDTO(BaseModel):
    fighter_id: int
    name: str
    total_sig_landed: int
    total_sig_attempted: int
    accuracy: float

    model_config = ConfigDict(from_attributes=True)


class KoTkoLeaderDTO(BaseModel):
    fighter_id: int
    name: str
    ko_tko_finishes: int

    model_config = ConfigDict(from_attributes=True)


class SigStrikesPerFightDTO(BaseModel):
    fighter_id: int
    name: str
    sig_str_per_fight: float
    total_fights: int

    model_config = ConfigDict(from_attributes=True)


class StrikingAccuracyLeaderboardDTO(BaseModel):
    min10: List[StrikingAccuracyDTO]
    min15: List[StrikingAccuracyDTO]
    min20: List[StrikingAccuracyDTO]

    model_config = ConfigDict(from_attributes=True)


class SigStrikesLeaderboardDTO(BaseModel):
    min10: List[SigStrikesPerFightDTO]
    min15: List[SigStrikesPerFightDTO]
    min20: List[SigStrikesPerFightDTO]

    model_config = ConfigDict(from_attributes=True)


class KnockdownLeaderDTO(BaseModel):
    fighter_id: int
    name: str
    total_knockdowns: int
    total_fights: int
    kd_per_fight: float

    model_config = ConfigDict(from_attributes=True)


class SigStrikesByWeightClassDTO(BaseModel):
    weight_class: str
    avg_sig_str_per_fight: float
    total_fights: int

    model_config = ConfigDict(from_attributes=True)


class StrikeExchangeDTO(BaseModel):
    fighter_id: int
    name: str
    total_fights: int
    sig_landed_per_fight: float
    sig_absorbed_per_fight: float
    differential_per_fight: float

    model_config = ConfigDict(from_attributes=True)


class StrikeExchangeLeaderboardDTO(BaseModel):
    min10: List[StrikeExchangeDTO]
    min15: List[StrikeExchangeDTO]
    min20: List[StrikeExchangeDTO]

    model_config = ConfigDict(from_attributes=True)


class StanceWinrateDTO(BaseModel):
    winner_stance: str
    loser_stance: str
    wins: int
    win_rate: float

    model_config = ConfigDict(from_attributes=True)


class StrikingResponseDTO(BaseModel):
    strike_targets: List[StrikeTargetDTO]
    striking_accuracy: StrikingAccuracyLeaderboardDTO
    ko_tko_leaders: List[KoTkoLeaderDTO]
    sig_strikes_per_fight: SigStrikesLeaderboardDTO
    knockdown_leaders: List[KnockdownLeaderDTO] = []
    sig_strikes_by_weight_class: List[SigStrikesByWeightClassDTO] = []
    strike_exchange: StrikeExchangeLeaderboardDTO = None
    stance_winrate: List[StanceWinrateDTO] = []

    model_config = ConfigDict(from_attributes=True)


# ===== Tab 4: Grappling =====

class TakedownAccuracyDTO(BaseModel):
    fighter_id: int
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
    fighter_id: int
    name: str
    total_ground_landed: int
    total_ground_attempted: int
    accuracy: float

    model_config = ConfigDict(from_attributes=True)


class SubmissionEfficiencyFighterDTO(BaseModel):
    fighter_id: int
    name: str
    total_sub_attempts: int
    sub_finishes: int

    model_config = ConfigDict(from_attributes=True)


class SubmissionEfficiencyDTO(BaseModel):
    fighters: List[SubmissionEfficiencyFighterDTO]
    avg_efficiency_ratio: float

    model_config = ConfigDict(from_attributes=True)


class TakedownLeaderboardDTO(BaseModel):
    min10: List[TakedownAccuracyDTO]
    min15: List[TakedownAccuracyDTO]
    min20: List[TakedownAccuracyDTO]

    model_config = ConfigDict(from_attributes=True)


class TdAttemptsLeaderDTO(BaseModel):
    fighter_id: int
    name: str
    td_attempts_per_fight: float
    total_td_attempted: int
    total_td_landed: int
    total_fights: int

    model_config = ConfigDict(from_attributes=True)


class TdAttemptsLeaderboardDTO(BaseModel):
    min10: List[TdAttemptsLeaderDTO]
    min15: List[TdAttemptsLeaderDTO]
    min20: List[TdAttemptsLeaderDTO]
    avg_td_attempts: float

    model_config = ConfigDict(from_attributes=True)


class TdSubCorrelationFighterDTO(BaseModel):
    fighter_id: int
    name: str
    total_td_landed: int
    sub_finishes: int
    total_fights: int
    td_per_fight: float
    sub_per_fight: float

    model_config = ConfigDict(from_attributes=True)


class TdSubQuadrantDTO(BaseModel):
    fighters: List[TdSubCorrelationFighterDTO]
    count: int

    model_config = ConfigDict(from_attributes=True)


class TdSubCorrelationDTO(BaseModel):
    quadrants: Dict[str, TdSubQuadrantDTO]
    avg_td: float
    avg_sub: float

    model_config = ConfigDict(from_attributes=True)


class TdDefenseLeaderDTO(BaseModel):
    fighter_id: int
    name: str
    opp_td_attempted: int
    opp_td_landed: int
    td_defended: int
    td_defense_rate: float

    model_config = ConfigDict(from_attributes=True)


class TdDefenseLeaderboardDTO(BaseModel):
    min10: List[TdDefenseLeaderDTO]
    min15: List[TdDefenseLeaderDTO]
    min20: List[TdDefenseLeaderDTO]

    model_config = ConfigDict(from_attributes=True)


class GrapplingResponseDTO(BaseModel):
    takedown_accuracy: TakedownLeaderboardDTO
    submission_techniques: List[SubmissionTechniqueDTO]
    control_time: List[ControlTimeDTO]
    ground_strikes: List[GroundStrikesDTO]
    submission_efficiency: SubmissionEfficiencyDTO
    td_attempts_leaders: TdAttemptsLeaderboardDTO = None
    td_sub_correlation: TdSubCorrelationDTO = None
    td_defense_leaders: TdDefenseLeaderboardDTO = None

    model_config = ConfigDict(from_attributes=True)
