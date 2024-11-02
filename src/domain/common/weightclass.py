from dataclasses import dataclass

@dataclass
class WeightClass:
    id : int
    name : str
    max_weight : float
    min_weight : float
