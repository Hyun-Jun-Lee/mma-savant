from datetime import datetime
from typing import Optional

from pydantic import BaseModel as PydanticModel, Field, ConfigDict
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime

from common.utils import kr_time_now

DECLARATIVE_BASE = declarative_base()

class BaseModel(DECLARATIVE_BASE):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=kr_time_now)
    updated_at = Column(DateTime, default=kr_time_now, onupdate=kr_time_now)

class BaseSchema(PydanticModel):
    id : Optional[int] = None
    created_at: Optional[datetime] = Field(default_factory=kr_time_now)
    updated_at: Optional[datetime] = Field(default_factory=kr_time_now)
    
    model_config = ConfigDict(from_attributes=True)

