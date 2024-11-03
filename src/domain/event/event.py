from dataclasses import dataclass, field
from typing import List
from datetime import date
from src.domain.common.base_entity import BaseEntity

@dataclass
class Event(BaseEntity):
    name: str
    location: str
    date: date

    def get_match(self, match_id: int, match_repo):
        return match_repo.get_by_id(match_id)
    
    def get_all_matches(self, match_repo):
        return match_repo.get_all_by_event_id(self.id)

    def get_main_event(self, match_repo):
        return match_repo.get_main_event(self.id)