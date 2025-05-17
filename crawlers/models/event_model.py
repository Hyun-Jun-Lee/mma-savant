from sqlalchemy import Column, String, Date
from sqlalchemy.orm import relationship

from models.base import BaseModel
from schemas import Event

class EventModel(BaseModel):
    __tablename__ = "event"

    name = Column(String, nullable=False)
    location = Column(String)
    event_date = Column(Date)
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
        
    def to_schema(self) -> Event:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return Event(
            id=self.id,
            name=self.name,
            location=self.location,
            event_date=self.event_date,
            url=self.url,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )