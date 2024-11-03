from dataclasses import dataclass

from domain.common.weightclass import WeightClass
from domain.common.base_entity import BaseEntity

@dataclass
class Ranking(BaseEntity):
    fighter_id : int
    ranking : int
    weight_class : WeightClass