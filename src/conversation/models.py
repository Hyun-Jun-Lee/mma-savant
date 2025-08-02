from typing import List, Optional, Dict
from datetime import datetime

from pydantic import ConfigDict
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import relationship
from common.base_model import BaseModel, BaseSchema

#############################
########## SCHEMA ###########
#############################

class ConversationSchema(BaseSchema):
    user_id : int
    session_id : str
    messages : List[Dict]
    tool_results : Optional[List[Dict]] = None

    model_config = ConfigDict(from_attributes=True)


# 채팅 세션 관리용 스키마들

class ChatSessionCreate(BaseSchema):
    """새 채팅 세션 생성 요청"""
    title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseSchema):
    """채팅 세션 응답"""
    id: int
    user_id: int
    session_id: str
    title: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseSchema):
    """새 메시지 생성 요청"""
    content: str
    role: str  # "user" or "assistant"
    session_id: str
    tool_results: Optional[List[Dict]] = None

    model_config = ConfigDict(from_attributes=True)


class MessageSchema(BaseSchema):
    """메시지 스키마"""
    message_id: str
    session_id: str
    content: str
    role: str
    tool_results: Optional[List[Dict]] = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageResponse(BaseSchema):
    """채팅 메시지 응답"""
    id: str
    content: str
    role: str
    timestamp: datetime
    session_id: str
    tool_results: Optional[List[Dict]] = None

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseSchema):
    """채팅 히스토리 응답"""
    session_id: str
    messages: List[ChatMessageResponse]
    total_messages: int
    has_more: bool

    model_config = ConfigDict(from_attributes=True)


class ChatSessionListResponse(BaseSchema):
    """채팅 세션 목록 응답"""
    sessions: List[ChatSessionResponse]
    total_sessions: int

    model_config = ConfigDict(from_attributes=True)


#############################
########## MODEL ###########
#############################

class MessageModel(BaseModel):
    """개별 메시지 모델"""
    __tablename__ = "message"
    
    message_id = Column(String, nullable=False, unique=True, index=True)  # UUID
    session_id = Column(String, ForeignKey("conversation.session_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    tool_results = Column(JSONB, nullable=True)  # tool 결과 저장
    
    # 관계 설정
    session = relationship("ConversationModel", back_populates="message_records")
    
    def to_response(self) -> ChatMessageResponse:
        """ChatMessageResponse로 변환"""
        return ChatMessageResponse(
            id=self.message_id,
            content=self.content,
            role=self.role,
            timestamp=self.created_at,
            session_id=self.session_id,
            tool_results=self.tool_results
        )


class ConversationModel(BaseModel):
    __tablename__ = "conversation"
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    session_id = Column(String, nullable=False, unique=True, index=True)
    title = Column(Text, nullable=True)  # 채팅 세션 제목

    # 관계 설정
    user = relationship("UserModel", back_populates="conversations")
    message_records = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    

    @classmethod
    def from_schema(cls, conversation: ConversationSchema):
        return cls(
            user_id=conversation.user_id,
            session_id=conversation.session_id,
            title=getattr(conversation, 'title', None)
        )
    
    def to_session_response(self, last_message_at: Optional[datetime] = None) -> ChatSessionResponse:
        """채팅 세션 응답으로 변환"""
        return ChatSessionResponse(
            id=self.id,
            user_id=self.user_id,
            session_id=self.session_id,
            title=self.title,
            last_message_at=last_message_at or self.updated_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
    
    def get_messages_as_responses(self) -> List[ChatMessageResponse]:
        """메시지들을 ChatMessageResponse 형태로 변환"""
        if not self.message_records:
            return []
        
        return [msg.to_response() for msg in self.message_records]