from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime

DECLARTIVE_BASE = declarative_base()

class BaseModel(DECLARTIVE_BASE):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class BaseSchema(BaseModel):
    id : Optional[int] = None
    created_at: Optional[datetime] = Field(default=datetime.now)
    updated_at: Optional[datetime] = Field(default=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

