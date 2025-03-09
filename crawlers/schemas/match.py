from typing import Optional, List

from pydantic import ConfigDict

from schemas.base import BaseSchema

class MatchStatistics(BaseSchema):
    fighter_name: str
    head_strikes_landed: Optional[int] = 0
    head_strikes_attempts: Optional[int] = 0
    body_strikes_landed: Optional[int] = 0
    body_strikes_attempts: Optional[int] = 0
    leg_strikes_landed: Optional[int] = 0
    leg_strikes_attempts: Optional[int] = 0
    takedowns_landed: Optional[int] = 0
    takedowns_attempts: Optional[int] = 0
    clinch_strikes_landed: Optional[int] = 0
    clinch_strikes_attempts: Optional[int] = 0
    ground_strikes_landed: Optional[int] = 0
    ground_strikes_attempts: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)

class Match(BaseSchema):
    event_name: str
    winner_name: Optional[str] = None
    loser_name: Optional[str] = None
    method: Optional[str] = None
    rounds: Optional[int] = 0
    is_main_event: bool = False
    statistics: List[MatchStatistics] = []

    
    model_config = ConfigDict(from_attributes=True)
