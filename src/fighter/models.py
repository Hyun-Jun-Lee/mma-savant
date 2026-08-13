from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from pydantic import ConfigDict

from common.base_model import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class FighterSchema(BaseSchema):
    name: str
    nickname: Optional[str] = None
    height: Optional[float] = 0
    height_cm: Optional[float] = 0
    weight: Optional[float] = 0
    weight_kg: Optional[float] = 0
    reach: Optional[float] = 0
    reach_cm: Optional[float] = 0
    stance: Optional[str] = None
    belt: bool = False
    birthdate: Optional[date] = None
    detail_url: Optional[str] = None
    nationality: Optional[str] = None
    tapology_url: Optional[str] = None
    born: Optional[str] = None
    fighting_out_of: Optional[str] = None
    affiliation: Optional[str] = None
    gym: Optional[str] = None
    current_streak: Optional[str] = None
    last_fight_name: Optional[str] = None
    last_fight_date: Optional[date] = None
    last_fight_promotion: Optional[str] = None
    tapology_last_scraped_at: Optional[datetime] = None
    tapology_attempt_status: Optional[str] = None
    tapology_last_attempt_at: Optional[datetime] = None
    tapology_failure_stage: Optional[str] = None
    tapology_failure_reason: Optional[str] = None

    wins: int = 0
    losses: int = 0
    draws: int = 0

    model_config = ConfigDict(from_attributes=True)


class FighterPromotionRecordSchema(BaseSchema):
    fighter_id: int
    promotion_name: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    no_contests: int = 0

    model_config = ConfigDict(from_attributes=True)


class FighterMethodRecordSchema(BaseSchema):
    fighter_id: int
    scope: str = "all_career"
    result: str
    method_category: str
    count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RankingSchema(BaseSchema):
    fighter_id: int
    ranking: int = None
    weight_class_id: int = None
    
    model_config = ConfigDict(from_attributes=True)

#############################
########## MODEL ###########
#############################

class FighterModel(BaseModel):
    __tablename__ = "fighter"

    name = Column(String, nullable=False)
    nickname = Column(String)
    height = Column(Float)
    height_cm = Column(Float)
    weight = Column(Float)
    weight_kg = Column(Float)
    reach = Column(Float)
    reach_cm = Column(Float)
    stance = Column(String)
    birthdate = Column(String)
    belt = Column(Boolean, default=False)
    detail_url = Column(String)
    nationality = Column(String)
    tapology_url = Column(String)
    born = Column(String)
    fighting_out_of = Column(String)
    affiliation = Column(String)
    gym = Column(String)
    current_streak = Column(String)
    last_fight_name = Column(String)
    last_fight_date = Column(Date)
    last_fight_promotion = Column(String)
    tapology_last_scraped_at = Column(DateTime)
    tapology_attempt_status = Column(String)
    tapology_last_attempt_at = Column(DateTime)
    tapology_failure_stage = Column(String)
    tapology_failure_reason = Column(String)

    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)

    fighter_matches = relationship("FighterMatchModel", back_populates="fighter")
    matches = relationship("MatchModel", secondary="fighter_match", viewonly=True)
    rankings = relationship("RankingModel", back_populates="fighter")
    promotion_records = relationship("FighterPromotionRecordModel", back_populates="fighter")
    method_records = relationship("FighterMethodRecordModel", back_populates="fighter")

    @classmethod
    def from_schema(cls, fighter: FighterSchema) -> None:
        return cls(
            name=fighter.name,
            nickname=fighter.nickname,
            height=fighter.height,
            height_cm=fighter.height_cm,
            weight=fighter.weight,
            weight_kg=fighter.weight_kg,
            reach=fighter.reach,
            reach_cm=fighter.reach_cm,
            stance=fighter.stance,
            wins=fighter.wins,
            losses=fighter.losses,
            draws=fighter.draws,
            belt=fighter.belt,
            detail_url=fighter.detail_url,
            birthdate=fighter.birthdate,
            nationality=fighter.nationality,
            tapology_url=fighter.tapology_url,
            born=fighter.born,
            fighting_out_of=fighter.fighting_out_of,
            affiliation=fighter.affiliation,
            gym=fighter.gym,
            current_streak=fighter.current_streak,
            last_fight_name=fighter.last_fight_name,
            last_fight_date=fighter.last_fight_date,
            last_fight_promotion=fighter.last_fight_promotion,
            tapology_last_scraped_at=fighter.tapology_last_scraped_at,
            tapology_attempt_status=fighter.tapology_attempt_status,
            tapology_last_attempt_at=fighter.tapology_last_attempt_at,
            tapology_failure_stage=fighter.tapology_failure_stage,
            tapology_failure_reason=fighter.tapology_failure_reason,
        )   
        
    def to_schema(self) -> FighterSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return FighterSchema(
            id=self.id,
            name=self.name,
            nickname=self.nickname,
            height=self.height,
            height_cm=self.height_cm,
            weight=self.weight,
            weight_kg=self.weight_kg,
            reach=self.reach,
            reach_cm=self.reach_cm,
            stance=self.stance,
            wins=self.wins,
            losses=self.losses,
            draws=self.draws,
            belt=self.belt,
            detail_url=self.detail_url,
            birthdate=self.birthdate,
            nationality=self.nationality,
            tapology_url=self.tapology_url,
            born=self.born,
            fighting_out_of=self.fighting_out_of,
            affiliation=self.affiliation,
            gym=self.gym,
            current_streak=self.current_streak,
            last_fight_name=self.last_fight_name,
            last_fight_date=self.last_fight_date,
            last_fight_promotion=self.last_fight_promotion,
            tapology_last_scraped_at=self.tapology_last_scraped_at,
            tapology_attempt_status=self.tapology_attempt_status,
            tapology_last_attempt_at=self.tapology_last_attempt_at,
            tapology_failure_stage=self.tapology_failure_stage,
            tapology_failure_reason=self.tapology_failure_reason,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class FighterPromotionRecordModel(BaseModel):
    __tablename__ = "fighter_promotion_record"
    __table_args__ = (
        UniqueConstraint("fighter_id", "promotion_name", name="uq_fighter_promotion_record_key"),
    )

    fighter_id = Column(Integer, ForeignKey("fighter.id"), nullable=False)
    promotion_name = Column(String, nullable=False)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    no_contests = Column(Integer, default=0)

    fighter = relationship("FighterModel", back_populates="promotion_records")

    @classmethod
    def from_schema(cls, record: FighterPromotionRecordSchema) -> "FighterPromotionRecordModel":
        return cls(
            fighter_id=record.fighter_id,
            promotion_name=record.promotion_name,
            wins=record.wins,
            losses=record.losses,
            draws=record.draws,
            no_contests=record.no_contests,
        )

    def to_schema(self) -> FighterPromotionRecordSchema:
        return FighterPromotionRecordSchema(
            id=self.id,
            fighter_id=self.fighter_id,
            promotion_name=self.promotion_name,
            wins=self.wins,
            losses=self.losses,
            draws=self.draws,
            no_contests=self.no_contests,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class FighterMethodRecordModel(BaseModel):
    __tablename__ = "fighter_method_record"
    __table_args__ = (
        UniqueConstraint("fighter_id", "scope", "result", "method_category", name="uq_fighter_method_record_key"),
    )

    fighter_id = Column(Integer, ForeignKey("fighter.id"), nullable=False)
    scope = Column(String, nullable=False, default="all_career")
    result = Column(String, nullable=False)
    method_category = Column(String, nullable=False)
    count = Column(Integer, default=0)

    fighter = relationship("FighterModel", back_populates="method_records")

    @classmethod
    def from_schema(cls, record: FighterMethodRecordSchema) -> "FighterMethodRecordModel":
        return cls(
            fighter_id=record.fighter_id,
            scope=record.scope,
            result=record.result,
            method_category=record.method_category,
            count=record.count,
        )

    def to_schema(self) -> FighterMethodRecordSchema:
        return FighterMethodRecordSchema(
            id=self.id,
            fighter_id=self.fighter_id,
            scope=self.scope,
            result=self.result,
            method_category=self.method_category,
            count=self.count,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class RankingModel(BaseModel):
    __tablename__ = "ranking"

    fighter_id = Column(Integer, ForeignKey("fighter.id"))
    weight_class_id = Column(Integer, ForeignKey("weight_class.id"))
    ranking = Column(Integer)

    fighter = relationship("FighterModel", back_populates="rankings")
    weight_class = relationship("WeightClassModel", back_populates="rankings")

    @classmethod
    def from_schema(cls, ranking: RankingSchema) -> None:
        return cls(
            fighter_id=ranking.fighter_id,
            weight_class_id=ranking.weight_class_id,
            ranking=ranking.ranking,
        )
        
    def to_schema(self) -> RankingSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return RankingSchema(
            id=self.id,
            fighter_id=self.fighter_id,
            weight_class_id=self.weight_class_id,
            ranking=self.ranking,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
