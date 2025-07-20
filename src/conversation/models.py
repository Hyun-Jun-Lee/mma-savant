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
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseSchema):
    """새 메시지 생성 요청"""
    content: str
    role: str  # "user" or "assistant"
    session_id: str

    model_config = ConfigDict(from_attributes=True)


class ChatMessageResponse(BaseSchema):
    """채팅 메시지 응답"""
    id: str
    content: str
    role: str
    timestamp: datetime
    session_id: str

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

class ConversationModel(BaseModel):
    __tablename__ = "conversation"
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    session_id = Column(String, nullable=False, index=True)
    messages = Column(JSONB, nullable=False)
    tool_results = Column(JSONB, nullable=True)
    title = Column(Text, nullable=True)  # 채팅 세션 제목

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
    
    def to_session_response(self) -> ChatSessionResponse:
        """채팅 세션 응답으로 변환"""
        message_count = len(self.messages) if self.messages else 0
        last_message_at = None
        
        # 마지막 메시지 시간 추출
        if self.messages and message_count > 0:
            last_msg = self.messages[-1]
            if isinstance(last_msg, dict) and 'timestamp' in last_msg:
                last_message_at = datetime.fromisoformat(last_msg['timestamp'])
        
        return ChatSessionResponse(
            id=self.id,
            user_id=self.user_id,
            session_id=self.session_id,
            title=self.title,
            message_count=message_count,
            last_message_at=last_message_at or self.updated_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
    
    def get_messages_as_responses(self) -> List[ChatMessageResponse]:
        """메시지들을 ChatMessageResponse 형태로 변환"""
        if not self.messages:
            return []
        
        message_responses = []
        for msg in self.messages:
            if isinstance(msg, dict):
                message_responses.append(ChatMessageResponse(
                    id=msg.get('id', ''),
                    content=msg.get('content', ''),
                    role=msg.get('role', 'user'),
                    timestamp=datetime.fromisoformat(msg.get('timestamp', datetime.now().isoformat())),
                    session_id=self.session_id
                ))
        
        return message_responses