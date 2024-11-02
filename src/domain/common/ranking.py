from dataclasses import dataclass

from common.weightclass import WeightClass

@dataclass
class Ranking:
    id : int
    fighter_id : int
    ranking : int
    weight_class : WeightClass