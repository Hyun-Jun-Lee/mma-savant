from typing import Optional, List

from pydantic import ConfigDict

from schemas.base import BaseSchema

class StrikeDetail(BaseSchema):
    fighter_match_id: int
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

    round: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)

class MatchStatistics(BaseSchema):
    fighter_match_id: int
    knockdowns: Optional[int] = 0
    control_time_seconds: Optional[int] = 0
    submission_attempts: Optional[int] = 0
    sig_str_landed: Optional[int] = 0
    sig_str_attempted: Optional[int] = 0
    total_str_landed: Optional[int] = 0
    total_str_attempted: Optional[int] = 0
    td_landed: Optional[int] = 0
    td_attempted: Optional[int] = 0

    round: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)

class Match(BaseSchema):
    # TODO : event_name is not used in the database, need to change to id
    event_name: str
    method: Optional[str] = None
    result_round: Optional[int] = 0
    is_main_event: bool = False

    statistics: List[MatchStatistics] = []
    strike_detail: List[StrikeDetail] = []
    
    model_config = ConfigDict(from_attributes=True)
