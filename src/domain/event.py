from dataclasses import dataclass, field
from typing import Dict
from datetime import date
from src.domain.common.base_entity import BaseEntity

@dataclass
class Event(BaseEntity):
    name: str
    location: str
    date: date

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            id=data["id"],
            name=data["name"],
            location=data["location"],
            date=data["date"],
        )
