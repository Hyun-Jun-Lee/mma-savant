from datetime import date
from typing import Optional
from pydantic import  ConfigDict

from schemas.base import BaseSchema


class Event(BaseSchema):
    name: str = None
    location: str = None
    event_date: Optional[date] = None
    url: str = None
    
    model_config = ConfigDict(from_attributes=True)
