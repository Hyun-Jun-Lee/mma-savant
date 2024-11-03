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
    
    def get_match(self, match_id: int, match_repo):
        return match_repo.get_by_id(match_id)