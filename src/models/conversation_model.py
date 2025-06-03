from typing import List, Optional, Dict

from pydantic import ConfigDict
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import relationship
from models.base import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class ConversationSchema(BaseSchema):
    user_id : int
    session_id : str
    messages : List[Dict]
    tool_results : Optional[List[Dict]] = None

    model_config = ConfigDict(from_attributes=True)


#############################
########## MODEL ###########
#############################

class ConversationModel(BaseModel):
    __tablename__ = "conversation"
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    session_id = Column(String, nullable=False)
    messages = Column(JSONB, nullable=False)
    tool_results = Column(JSONB, nullable=True)

    user = relationship("UserModel", back_populates="conversations")
    

    @classmethod
    def from_schema(cls, conversation: ConversationSchema) -> None:
        return cls(
            user_id=conversation.user_id,
            session_id=conversation.session_id,
            messages=conversation.messages,
            tool_results=conversation.tool_results
        )

    def to_schema(self) -> ConversationSchema:
        """SQLAlchemy 모델을 Pydantic 스키마로 변환"""
        return ConversationSchema(
            id=self.id,
            user_id=self.user_id,
            session_id=self.session_id,
            messages=self.messages,
            tool_results=self.tool_results,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )