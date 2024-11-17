from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List

from common.weightclass import WeightClass
from common.ranking import Ranking
from common.base_entity import BaseEntity

@dataclass
class FighterStatistics:
    fighter_id: int
    win_count: int
    loss_count: int
    draw_count: int

    weight_classes : list[WeightClass]
    rankings : list[Ranking]

    @classmethod
    def from_dict(cls, data: Dict):
        """DB에서 조회된 데이터를 FighterStatistics 객체로 변환"""
        return cls(
            fighter_id=data["id"],
            win_count=data["win_count"],
            loss_count=data["loss_count"],
            draw_count=data["draw_count"],
            weight_classes=data["weight_classes"],
            rankings=data["rankings"]
        )

@dataclass
class Fighter(BaseEntity):
    name : str
    nickname : str
    birthdate : date
    height : int
    reach : int

    statistics : List[FighterStatistics]


    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
    
    @classmethod
    def from_dict(cls, data: Dict):
        """DB에서 조회된 데이터를 Fighter 객체로 변환"""
        return cls(
            id=data["id"],
            name=data["name"],
            nickname=data["nickname"],
            birthdate=data["birthdate"],
            height=data["height"],
            reach=data["reach"],
        )