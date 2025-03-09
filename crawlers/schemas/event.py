from datetime import date
from pydantic import  ConfigDict

from schemas.base import BaseSchema


class Event(BaseSchema):
    name: str = None
    location: str = None
    event_date: date = None
    url: str = None
    
    model_config = ConfigDict(from_attributes=True)
