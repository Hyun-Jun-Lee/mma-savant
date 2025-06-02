from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from pydantic import ConfigDict

from models.base import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class UserSchmea(BaseSchema):
    email : str
    password_hash : str

    model_config = ConfigDict(from_attributes=True)


#############################
########## MODEL ###########
#############################

class UserModel(BaseModel):
    __tablename__ = "user"
    
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)

    conversations = relationship("ConversationModel", back_populates="user")

    @classmethod
    def from_schema(cls, user: UserSchmea) -> None:
        return cls(
            email=user.email,
            password_hash=user.password_hash
        )

    def to_schema(self) -> UserSchmea:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return UserSchmea(
            id=self.id,
            email=self.email,
            password_hash=self.password_hash,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )