from typing import Optional, List
from dataclasses import dataclass, field, asdict

from domain.common.base_entity import BaseEntity

@dataclass
class MatchStatistics(BaseEntity):
    match_id: int
    fighter_id: int

    head_strikes_landed : Optional[int] = None
    head_strikes_attempts : Optional[int] = None
    body_strikes_landed : Optional[int] = None
    body_strikes_attempts : Optional[int] = None
    leg_strikes_landed : Optional[int] = None
    leg_strikes_attempts : Optional[int] = None

    takedowns_landed : Optional[int] = None
    takedowns_attempts : Optional[int] = None
    clinch_strikes_landed : Optional[int] = None
    clinch_strikes_attempts : Optional[int] = None
    ground_strikes_landed : Optional[int] = None
    ground_strikes_attempts : Optional[int] = None

    def get_total_strike_landed(self) -> int:
        return sum(filter(lambda x: x is not None, [self.head_strikes_landed, self.body_strikes_landed, self.leg_strikes_landed]))
    
    def get_total_strike_attempted(self) -> int:
        return sum(filter(lambda x: x is not None, [self.head_strikes_attempts, self.body_strikes_attempts, self.leg_strikes_attempts]))
    
    def get_total_takedown_landed(self) -> int:
        return sum(filter(lambda x: x is not None, [self.takedowns_landed]))
    
    def get_total_takedown_attempted(self) -> int:
        return sum(filter(lambda x: x is not None, [self.takedowns_attempts]))

@dataclass
class Match(BaseEntity):
    event_id: int
    winner_fighter_id: Optional[int] = None
    loser_fighter_id: Optional[int] = None
    method: Optional[str] = None
    rounds: Optional[int] = None
    statistics: List[MatchStatistics] = field(default_factory=list)

    is_main_event: bool = False