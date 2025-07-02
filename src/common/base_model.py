from datetime import datetime
from typing import Optional

from pydantic import BaseModel as PydanticModel, Field, ConfigDict
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime

DECLARATIVE_BASE = declarative_base()

class BaseModel(DECLARATIVE_BASE):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class BaseSchema(PydanticModel):
    id : Optional[int] = None
    created_at: Optional[datetime] = Field(default=datetime.now)
    updated_at: Optional[datetime] = Field(default=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

