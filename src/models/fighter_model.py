from datetime import date
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from models.base import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class FighterSchmea(BaseSchema):
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

    wins: int = 0
    losses: int = 0
    draws: int = 0

    model_config = ConfigDict(from_attributes=True)

class RankingSchmea(BaseSchema):
    fighter_id: int
    ranking: int = None
    weight_class: str = None
    
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

    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)

    fighter_matches = relationship("FighterMatchModel", back_populates="fighter")
    matches = relationship("MatchModel", secondary="fighter_match", viewonly=True)
    rankings = relationship("RankingModel", back_populates="fighter")

    @classmethod
    def from_schema(cls, fighter: FighterSchmea) -> None:
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
            birthdate=fighter.birthdate
        )   
        
    def to_schema(self) -> FighterSchmea:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return FighterSchmea(
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
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

class RankingModel(BaseModel):
    __tablename__ = "ranking"

    fighter_id = Column(Integer, ForeignKey("fighter.id"))
    ranking = Column(Integer)
    weight_class = Column(String)

    fighter = relationship("FighterModel", back_populates="rankings")

    @classmethod
    def from_schema(cls, ranking: RankingSchmea) -> None:
        return cls(
            fighter_id=ranking.fighter_id,
            ranking=ranking.ranking,
            weight_class=ranking.weight_class
        )
        
    def to_schema(self) -> RankingSchmea:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return RankingSchmea(
            id=self.id,
            fighter_id=self.fighter_id,
            ranking=self.ranking,
            weight_class=self.weight_class,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )