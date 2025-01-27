from dataclasses import dataclass

@dataclass
class Ranking:
    fighter_id : int
    ranking : int
    weight_class : str