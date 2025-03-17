from datetime import date, datetime
from typing import Optional

from pydantic import ConfigDict

from schemas.base import BaseSchema


class Fighter(BaseSchema):
    name: str
    nickname: Optional[str] = None
    height: Optional[float] = 0
    height_cm: Optional[float] = 0
    weight: Optional[float] = 0
    weight_kg: Optional[float] = 0
    reach: Optional[float] = 0
    reach_cm: Optional[float] = 0
    stance: Optional[str] = None
    belt: bool = False
    birthdate: Optional[date] = None
    url_id: Optional[str] = None

    wins: int = 0
    losses: int = 0
    draws: int = 0
    
    model_config = ConfigDict(from_attributes=True)