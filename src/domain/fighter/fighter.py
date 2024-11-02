from dataclasses import dataclass
from datetime import date

from common.weightclass import WeightClass
from common.ranking import Ranking

@dataclass
class Fighter:
    id : int
    name : str
    nickname : str
    birthdate : date
    height : int
    reach : int
    weight_classes : list[WeightClass]
    rankings : list[Ranking]
    match_ids : list[int]

    @property
    def age(self) -> int:
        """현재 나이를 계산합니다."""
        today = date.today()
        return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))