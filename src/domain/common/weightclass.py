from dataclasses import dataclass

from domain.common.base_entity import BaseEntity

@dataclass
class WeightClass(BaseEntity):
    name : str
    max_weight : float
    min_weight : float
