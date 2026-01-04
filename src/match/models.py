from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import ConfigDict
from typing import Optional

from common.base_model import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class SigStrMatchStatSchema(BaseSchema):
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

class BasicMatchStatSchema(BaseSchema):
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

class MatchSchema(BaseSchema):
    event_id: int
    weight_class_id: Optional[int] = None
    method: Optional[str] = None
    result_round: Optional[int] = 0
    time: Optional[str] = None
    order: Optional[int] = 0
    is_main_event: bool = False
    detail_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class FighterMatchSchema(BaseSchema):
    fighter_id: int
    match_id: int
    result: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

#############################
########## MODEL ###########
#############################

class MatchModel(BaseModel):
    __tablename__ = "match"

    event_id = Column(Integer, ForeignKey("event.id"))
    weight_class_id = Column(Integer, ForeignKey("weight_class.id"))
    method = Column(String)
    result_round = Column(Integer)
    time = Column(String)
    order = Column(Integer)
    is_main_event = Column(Boolean)
    detail_url = Column(String)

    weight_class = relationship("WeightClassModel", back_populates="matches")
    fighter_matches = relationship("FighterMatchModel", back_populates="match")
    event = relationship("EventModel", back_populates="matches")

    @classmethod
    def from_schema(cls, match: MatchSchema) -> None:
        return cls(
            event_id=match.event_id,
            weight_class_id=match.weight_class_id,
            method=match.method,
            result_round=match.result_round,
            time=match.time,
            order=match.order,
            is_main_event=match.is_main_event,
            detail_url=match.detail_url
        )
        
    def to_schema(self) -> MatchSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return MatchSchema(
            id=self.id,
            event_id=self.event_id,
            weight_class_id=self.weight_class_id,
            method=self.method,
            result_round=self.result_round,
            time=self.time,
            order=self.order,
            is_main_event=self.is_main_event,
            detail_url=self.detail_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

class FighterMatchModel(BaseModel):
    __tablename__ = "fighter_match"
    
    fighter_id = Column(Integer, ForeignKey("fighter.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("match.id"), nullable=False)
    
    result = Column(String)
    
    fighter = relationship("FighterModel", back_populates="fighter_matches")
    match = relationship("MatchModel", back_populates="fighter_matches")
    
    strike_detail = relationship("SigStrMatchStatModel", back_populates="fighter_match", uselist=False)
    match_statistics = relationship("BasicMatchStatModel", back_populates="fighter_match", uselist=False)

    @classmethod
    def from_schema(cls, fighter_id: int, match_id: int, result: str, strike_detail: SigStrMatchStatSchema, match_statistics: BasicMatchStatSchema) -> None:
        return cls(
            fighter_id=fighter_id,
            match_id=match_id,
            result=result,
            strike_detail=strike_detail,
            match_statistics=match_statistics
        )
        
    def to_schema(self) -> FighterMatchSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return FighterMatchSchema(
            id=self.id,
            fighter_id=self.fighter_id,
            match_id=self.match_id,
            result=self.result,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

class SigStrMatchStatModel(BaseModel):
    __tablename__ = "strike_detail"
    
    fighter_match_id = Column(Integer, ForeignKey("fighter_match.id"))
    round = Column(Integer, default=0)

    head_strikes_landed = Column(Integer, default=0)
    head_strikes_attempts = Column(Integer, default=0)
    body_strikes_landed = Column(Integer, default=0)
    body_strikes_attempts = Column(Integer, default=0)
    leg_strikes_landed = Column(Integer, default=0)
    leg_strikes_attempts = Column(Integer, default=0)
    takedowns_landed = Column(Integer, default=0)
    takedowns_attempts = Column(Integer, default=0)
    clinch_strikes_landed = Column(Integer, default=0)
    clinch_strikes_attempts = Column(Integer, default=0)
    ground_strikes_landed = Column(Integer, default=0)
    ground_strikes_attempts = Column(Integer, default=0)
    
    fighter_match = relationship("FighterMatchModel", back_populates="strike_detail")
    
    @classmethod
    def from_schema(cls, strike_detail: SigStrMatchStatSchema) -> None:
        return cls(
            fighter_match_id=strike_detail.fighter_match_id,
            round=strike_detail.round,
            head_strikes_landed=strike_detail.head_strikes_landed,
            head_strikes_attempts=strike_detail.head_strikes_attempts,
            body_strikes_landed=strike_detail.body_strikes_landed,
            body_strikes_attempts=strike_detail.body_strikes_attempts,
            leg_strikes_landed=strike_detail.leg_strikes_landed,
            leg_strikes_attempts=strike_detail.leg_strikes_attempts,
            takedowns_landed=strike_detail.takedowns_landed,
            takedowns_attempts=strike_detail.takedowns_attempts,
            clinch_strikes_landed=strike_detail.clinch_strikes_landed,
            clinch_strikes_attempts=strike_detail.clinch_strikes_attempts,
            ground_strikes_landed=strike_detail.ground_strikes_landed,
            ground_strikes_attempts=strike_detail.ground_strikes_attempts
        )
        
    def to_schema(self) -> SigStrMatchStatSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return SigStrMatchStatSchema(
            id=self.id,
            fighter_match_id=self.fighter_match_id,
            round=self.round,
            head_strikes_landed=self.head_strikes_landed,
            head_strikes_attempts=self.head_strikes_attempts,
            body_strikes_landed=self.body_strikes_landed,
            body_strikes_attempts=self.body_strikes_attempts,
            leg_strikes_landed=self.leg_strikes_landed,
            leg_strikes_attempts=self.leg_strikes_attempts,
            takedowns_landed=self.takedowns_landed,
            takedowns_attempts=self.takedowns_attempts,
            clinch_strikes_landed=self.clinch_strikes_landed,
            clinch_strikes_attempts=self.clinch_strikes_attempts,
            ground_strikes_landed=self.ground_strikes_landed,
            ground_strikes_attempts=self.ground_strikes_attempts,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

class BasicMatchStatModel(BaseModel):
    __tablename__ = "match_statistics"
    
    fighter_match_id = Column(Integer, ForeignKey("fighter_match.id"))
    round = Column(Integer, default=0)
    
    knockdowns = Column(Integer, default=0)
    control_time_seconds = Column(Integer, default=0)
    submission_attempts = Column(Integer, default=0)
    sig_str_landed = Column(Integer, default=0)
    sig_str_attempted = Column(Integer, default=0)
    total_str_landed = Column(Integer, default=0)
    total_str_attempted = Column(Integer, default=0)
    td_landed = Column(Integer, default=0)
    td_attempted = Column(Integer, default=0)

    
    fighter_match = relationship("FighterMatchModel", back_populates="match_statistics")
    
    @classmethod
    def from_schema(cls, match_statistics: BasicMatchStatSchema) -> None:
        return cls(
            fighter_match_id=match_statistics.fighter_match_id,
            round=match_statistics.round,
            knockdowns=match_statistics.knockdowns,
            control_time_seconds=match_statistics.control_time_seconds,
            submission_attempts=match_statistics.submission_attempts,
            sig_str_landed=match_statistics.sig_str_landed,
            sig_str_attempted=match_statistics.sig_str_attempted,
            total_str_landed=match_statistics.total_str_landed,
            total_str_attempted=match_statistics.total_str_attempted,
            td_landed=match_statistics.td_landed,
            td_attempted=match_statistics.td_attempted
        )
        
    def to_schema(self) -> BasicMatchStatSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return BasicMatchStatSchema(
            id=self.id,
            fighter_match_id=self.fighter_match_id,
            round=self.round,
            knockdowns=self.knockdowns,
            control_time_seconds=self.control_time_seconds,
            submission_attempts=self.submission_attempts,
            sig_str_landed=self.sig_str_landed,
            sig_str_attempted=self.sig_str_attempted,
            total_str_landed=self.total_str_landed,
            total_str_attempted=self.total_str_attempted,
            td_landed=self.td_landed,
            td_attempted=self.td_attempted,
            created_at=self.created_at,
            updated_at=self.updated_at
        )