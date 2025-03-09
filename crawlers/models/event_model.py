from sqlalchemy import Column, String, Float, Integer, Boolean
from sqlalchemy.orm import relationship

from models.base import BaseModel
from schemas import Event

class EventModel(BaseModel):
    __tablename__ = "event"

    name = Column(String, nullable=False)
    location = Column(String)
    event_date = Column(String)
    url = Column(String)

    matches = relationship("MatchModel", back_populates="event")

    @classmethod
    def from_schema(cls, event: Event) -> None:
        return cls(
            name=event.name,
            location=event.location,
            event_date=event.event_date,
            url=event.url
        )