from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from conversation.models import (
    ConversationModel, ConversationSchema, MessageModel, MessageSchema,
    ChatSessionResponse, ChatMessageResponse, ChatHistoryResponse
)
from common.utils import kr_time_now

# 채팅 세션 관리 함수들

async def create_chat_session(
    session: AsyncSession, 
    user_id: int, 
    title: Optional[str] = None
) -> ChatSessionResponse:
    """
    새 채팅 세션 생성.
    """
    # 고유한 session_id 생성
    session_id = str(uuid.uuid4())
    
    # 제목이 없으면 기본 제목 생성
    if not title:
        title = f"채팅 {kr_time_now().strftime('%Y-%m-%d %H:%M')}"
    
    # 새로운 대화 세션 생성 (메시지는 별도 테이블에 저장)
    db_conversation = ConversationModel(
        user_id=user_id,
        session_id=session_id,
        title=title
    )
    
    session.add(db_conversation)
    await session.flush()
    session_response = db_conversation.to_session_response()
    await session.commit()
    
    return session_response


async def get_user_chat_sessions(
    session: AsyncSession, 
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[ChatSessionResponse]:
    """
    사용자의 채팅 세션 목록 조회 (최신순).
    """
    # 세션 목록과 마지막 메시지 시간 조회
    result = await session.execute(
        select(
            ConversationModel,
            func.max(MessageModel.created_at).label('last_message_at')
        )
        .outerjoin(MessageModel, ConversationModel.session_id == MessageModel.session_id)
        .where(ConversationModel.user_id == user_id)
        .group_by(ConversationModel.id)
        .order_by(desc(ConversationModel.updated_at))
        .offset(offset)
        .limit(limit)
    )
    
    sessions = []
    for row in result:
        conv, last_message_at = row
        sessions.append(conv.to_session_response(last_message_at=last_message_at))
    
    return sessions


async def get_chat_session_by_id(
    session: AsyncSession, 
    session_id: str, 
    user_id: int
) -> Optional[ChatSessionResponse]:
    """
    특정 채팅 세션 조회 (사용자 권한 확인 포함).
    """
    result = await session.execute(
        select(ConversationModel)
        .where(
            ConversationModel.session_id == session_id,
            ConversationModel.user_id == user_id
        )
    )
    
    conversation = result.scalar_one_or_none()
    return conversation.to_session_response() if conversation else None


async def delete_chat_session(
    session: AsyncSession,
    session_id: str,
    user_id: int
) -> bool:
    """
    채팅 세션 삭제 (사용자 권한 확인 포함).
    """
    result = await session.execute(
        select(ConversationModel)
        .where(
            ConversationModel.session_id == session_id,
            ConversationModel.user_id == user_id
        )
    )
    
    conversation = result.scalar_one_or_none()
    if not conversation:
        return False
    
    await session.delete(conversation)
    await session.flush()
    await session.commit()
    return True


async def update_chat_session_title(
    session: AsyncSession,
    session_id: str,
    user_id: int,
    new_title: str
) -> Optional[ChatSessionResponse]:
    """
    채팅 세션 제목 업데이트.
    """
    await session.execute(
        update(ConversationModel)
        .where(
            ConversationModel.session_id == session_id,
            ConversationModel.user_id == user_id
        )
        .values(
            title=new_title,
            updated_at=kr_time_now()
        )
    )
    
    await session.flush()
    await session.commit()
    
    # 업데이트된 세션 조회
    return await get_chat_session_by_id(session, session_id, user_id)


async def get_chat_history(
    session: AsyncSession,
    session_id: str,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> Optional[ChatHistoryResponse]:
    """
    채팅 히스토리 조회 (페이지네이션 지원, 새로운 Message 테이블 사용).
    """
    # 세션 존재 확인
    conv_result = await session.execute(
        select(ConversationModel)
        .where(
            ConversationModel.session_id == session_id,
            ConversationModel.user_id == user_id
        )
    )
    
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        return None
    
    # 전체 메시지 수 조회
    total_count_result = await session.execute(
        select(func.count(MessageModel.id))
        .where(MessageModel.session_id == session_id)
    )
    total_messages = total_count_result.scalar() or 0
    
    # 메시지 목록 조회 (페이지네이션 적용)
    messages_result = await session.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at)
        .offset(offset)
        .limit(limit)
    )
    
    messages = messages_result.scalars().all()
    message_responses = [msg.to_response() for msg in messages]
    
    has_more = offset + limit < total_messages
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=message_responses,
        total_messages=total_messages,
        has_more=has_more
    )


async def add_message_to_session(
    session: AsyncSession,
    session_id: str,
    user_id: int,
    content: str,
    role: str,
    tool_results: Optional[List[dict]] = None
) -> Optional[ChatMessageResponse]:
    """
    채팅 세션에 새 메시지 추가 (새로운 Message 테이블 사용).
    """
    # 세션 존재 확인
    result = await session.execute(
        select(ConversationModel)
        .where(
            ConversationModel.session_id == session_id,
            ConversationModel.user_id == user_id
        )
    )
    
    conversation = result.scalar_one_or_none()
    if not conversation:
        return None
    
    # 새 메시지 생성
    message_id = str(uuid.uuid4())
    new_message = MessageModel(
        message_id=message_id,
        session_id=session_id,
        content=content,
        role=role,
        tool_results=tool_results
    )
    
    session.add(new_message)
    
    # 대화 세션의 updated_at 갱신
    conversation.updated_at = kr_time_now()
    session.add(conversation)
    
    await session.flush()
    saved_message = new_message.to_response()
    await session.commit()
    
    return saved_message


async def get_user_chat_sessions_count(session: AsyncSession, user_id: int) -> int:
    """
    사용자의 총 채팅 세션 수 조회.
    """
    result = await session.execute(
        select(func.count(ConversationModel.id))
        .where(ConversationModel.user_id == user_id)
    )
    
    return result.scalar() or 0