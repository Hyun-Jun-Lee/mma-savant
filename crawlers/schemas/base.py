from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    id : Optional[int] = None
    created_at: Optional[datetime] = Field(default=datetime.now)
    updated_at: Optional[datetime] = Field(default=datetime.now)
    
    model_config = ConfigDict(from_attributes=True)

