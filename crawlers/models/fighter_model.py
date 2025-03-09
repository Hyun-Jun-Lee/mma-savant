from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from models.base import BaseModel
from schemas import Fighter, Ranking

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

    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)

    fighter_matches = relationship("FighterMatchModel", back_populates="fighter")
    matches = relationship("MatchModel", secondary="fighter_match", viewonly=True)

    @classmethod
    def from_schema(cls, fighter: Fighter) -> None:
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
            belt=fighter.belt
        )

class RankingModel(BaseModel):
    __tablename__ = "ranking"

    fighter_id = Column(Integer, ForeignKey("fighter.id"))
    ranking = Column(Integer)
    weight_class = Column(String)

    fighter = relationship("FighterModel", back_populates="rankings")

    @classmethod
    def from_schema(cls, ranking: Ranking) -> None:
        return cls(
            fighter_id=ranking.fighter_id,
            ranking=ranking.ranking,
            weight_class=ranking.weight_class
        )