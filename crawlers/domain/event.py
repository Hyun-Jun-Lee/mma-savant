from dataclasses import dataclass, field
from typing import Dict
from datetime import date

@dataclass
class Event:
    name: str
    location: str
    date: date

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            name=data["name"],
            location=data["location"],
            date=data["date"],
        )