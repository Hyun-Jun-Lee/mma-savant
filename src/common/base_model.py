from datetime import datetime
from typing import Optional

from pydantic import BaseModel as PydanticModel, Field, ConfigDict
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime

from common.utils import utc_now

DECLARATIVE_BASE = declarative_base()

class BaseModel(DECLARATIVE_BASE):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

class BaseSchema(PydanticModel):
    id : Optional[int] = None
    created_at: Optional[datetime] = Field(default_factory=utc_now)
    updated_at: Optional[datetime] = Field(default_factory=utc_now)
    
    model_config = ConfigDict(from_attributes=True)

