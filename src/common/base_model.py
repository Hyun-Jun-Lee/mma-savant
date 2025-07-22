from datetime import datetime, timezone
from typing import Optional, Callable

from pydantic import BaseModel as PydanticModel, Field, ConfigDict
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

DECLARATIVE_BASE = declarative_base()

def utc_now() -> datetime:
    """UTC 시간 반환 함수 (timezone-naive)"""
    return datetime.utcnow()

class BaseModel(DECLARATIVE_BASE):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class BaseSchema(PydanticModel):
    id : Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

