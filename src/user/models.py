from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from pydantic import ConfigDict
from typing import Optional
from datetime import datetime

from common.base_model import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class UserSchema(BaseSchema):
    username: str
    password_hash: str
    total_requests: int = 0
    daily_requests: int = 0
    last_request_date: Optional[datetime] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


#############################
########## MODEL ###########
#############################

class UserModel(BaseModel):
    __tablename__ = "user"
    
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    total_requests = Column(Integer, default=0, nullable=False)
    daily_requests = Column(Integer, default=0, nullable=False)
    last_request_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    conversations = relationship("ConversationModel", back_populates="user")

    @classmethod
    def from_schema(cls, user: UserSchema):
        return cls(
            username=user.username,
            password_hash=user.password_hash,
            total_requests=user.total_requests,
            daily_requests=user.daily_requests,
            last_request_date=user.last_request_date,
            is_active=user.is_active
        )

    def to_schema(self) -> UserSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return UserSchema(
            id=self.id,
            username=self.username,
            password_hash=self.password_hash,
            total_requests=self.total_requests,
            daily_requests=self.daily_requests,
            last_request_date=self.last_request_date,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )