from dataclasses import dataclass, field
from typing import Dict
from datetime import date

@dataclass
class Event:
    name: str
    location: str
    date: date
    url : str

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            name=data.get("name"),
            location=data.get("location"),
            date=data.get("date"),
            url=data.get("url"),
        )