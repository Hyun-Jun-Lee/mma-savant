from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MatchStatistics:
    fighter_name: str  # Fighter의 이름으로 매칭
    head_strikes_landed: Optional[int] = None
    head_strikes_attempts: Optional[int] = None
    body_strikes_landed: Optional[int] = None
    body_strikes_attempts: Optional[int] = None
    leg_strikes_landed: Optional[int] = None
    leg_strikes_attempts: Optional[int] = None
    takedowns_landed: Optional[int] = None
    takedowns_attempts: Optional[int] = None
    clinch_strikes_landed: Optional[int] = None
    clinch_strikes_attempts: Optional[int] = None
    ground_strikes_landed: Optional[int] = None
    ground_strikes_attempts: Optional[int] = None

    def get_total_strike_landed(self) -> int:
        return sum(filter(lambda x: x is not None, [
            self.head_strikes_landed,
            self.body_strikes_landed,
            self.leg_strikes_landed
        ]))
    
    def get_total_strike_attempted(self) -> int:
        return sum(filter(lambda x: x is not None, [
            self.head_strikes_attempts,
            self.body_strikes_attempts,
            self.leg_strikes_attempts
        ]))
    
    def get_total_takedown_landed(self) -> int:
        return sum(filter(lambda x: x is not None, [self.takedowns_landed]))
    
    def get_total_takedown_attempted(self) -> int:
        return sum(filter(lambda x: x is not None, [self.takedowns_attempts]))

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            fighter_name=data.get("fighter_name"),
            head_strikes_landed=data.get("head_strikes_landed"),
            head_strikes_attempts=data.get("head_strikes_attempts"),
            body_strikes_landed=data.get("body_strikes_landed"),
            body_strikes_attempts=data.get("body_strikes_attempts"),
            leg_strikes_landed=data.get("leg_strikes_landed"),
            leg_strikes_attempts=data.get("leg_strikes_attempts"),
            takedowns_landed=data.get("takedowns_landed"),
            takedowns_attempts=data.get("takedowns_attempts"),
            clinch_strikes_landed=data.get("clinch_strikes_landed"),
            clinch_strikes_attempts=data.get("clinch_strikes_attempts"),
            ground_strikes_landed=data.get("ground_strikes_landed"),
            ground_strikes_attempts=data.get("ground_strikes_attempts")
        )

    def to_dict(self) -> Dict:
        return {
            "fighter_name": self.fighter_name,
            "head_strikes_landed": self.head_strikes_landed,
            "head_strikes_attempts": self.head_strikes_attempts,
            "body_strikes_landed": self.body_strikes_landed,
            "body_strikes_attempts": self.body_strikes_attempts,
            "leg_strikes_landed": self.leg_strikes_landed,
            "leg_strikes_attempts": self.leg_strikes_attempts,
            "takedowns_landed": self.takedowns_landed,
            "takedowns_attempts": self.takedowns_attempts,
            "clinch_strikes_landed": self.clinch_strikes_landed,
            "clinch_strikes_attempts": self.clinch_strikes_attempts,
            "ground_strikes_landed": self.ground_strikes_landed,
            "ground_strikes_attempts": self.ground_strikes_attempts
        }

@dataclass
class Match:
    event_name: str  
    winner_name: Optional[str] = None  
    loser_name: Optional[str] = None   
    method: Optional[str] = None
    rounds: Optional[int] = None
    is_main_event: bool = False
    statistics: List[MatchStatistics] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            event_name=data.get("event_name"),
            winner_name=data.get("winner_name"),
            loser_name=data.get("loser_name"),
            method=data.get("method"),
            rounds=data.get("rounds"),
            is_main_event=data.get("is_main_event", False),
            statistics=[MatchStatistics.from_dict(stat) for stat in data.get("statistics", [])],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

    def to_dict(self) -> Dict:
        return {
            "event_name": self.event_name,
            "winner_name": self.winner_name,
            "loser_name": self.loser_name,
            "method": self.method,
            "rounds": self.rounds,
            "is_main_event": self.is_main_event,
            "statistics": [stat.to_dict() for stat in self.statistics],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }