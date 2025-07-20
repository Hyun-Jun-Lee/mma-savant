from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from conversation.models import (
    ConversationModel, ConversationSchema, 
    ChatSessionResponse, ChatMessageResponse, ChatHistoryResponse
)
from user.models import UserModel

async def create_conversation(session: AsyncSession, conversation: ConversationSchema) -> ConversationSchema:
    """
    새 대화 세션을 생성하고 저장.
    """
    result = await session.execute(
        select(UserModel).where(UserModel.id == conversation.user_id)
    )
    if not result.scalar_one_or_none():
        raise ValueError(f"User {conversation.user_id} does not exist")
    
    db_conversation = ConversationModel.from_schema(conversation)
    session.add(db_conversation)
    await session.flush()
    return db_conversation.to_schema()

async def get_conversation_by_session_id(
    session: AsyncSession, session_id: str
) -> Optional[ConversationSchema]:
    """
    session_id로 대화 조회.
    """
    
    result = await session.execute(
        select(ConversationModel).where(ConversationModel.session_id == session_id)
    )
    db_conversation = result.scalar_one_or_none()
    if db_conversation:
        return db_conversation.to_schema()
    return None

async def append_message(
    session: AsyncSession, session_id: str, message: dict
) -> Optional[ConversationSchema]:
    """
    기존 대화에 새 메시지 추가.
    """
    result = await session.execute(
        select(ConversationModel).where(ConversationModel.session_id == session_id)
    )
    db_conversation = result.scalar_one_or_none()
    if not db_conversation:
        return None
    db_conversation.messages.append(message)
    session.add(db_conversation)
    await session.flush()
    return db_conversation.to_schema()

async def append_tool_result(
    session: AsyncSession, session_id: str, tool_result: dict
) -> Optional[ConversationSchema]:
    """
    기존 대화에 도구 결과 추가.
    """
    result = await session.execute(
        select(ConversationModel).where(ConversationModel.session_id == session_id)
    )
    db_conversation = result.scalar_one_or_none()
    if not db_conversation:
        return None
    if db_conversation.tool_results is None:
        db_conversation.tool_results = [tool_result]
    else:
        db_conversation.tool_results.append(tool_result)
    session.add(db_conversation)
    await session.flush()
    return db_conversation.to_schema()

async def get_conversations_by_user(
    session: AsyncSession, user_id: int
) -> List[ConversationSchema]:
    """
    사용자의 모든 대화 목록 조회.
    """
    result = await session.execute(
        select(ConversationModel).where(ConversationModel.user_id == user_id)
    )
    db_conversations = result.scalars().all()
    return [conv.to_schema() for conv in db_conversations]


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
        title = f"채팅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # 빈 메시지 배열로 대화 생성
    conversation_data = ConversationSchema(
        user_id=user_id,
        session_id=session_id,
        messages=[],
        tool_results=None
    )
    
    db_conversation = ConversationModel.from_schema(conversation_data)
    db_conversation.title = title
    
    session.add(db_conversation)
    await session.flush()
    
    return db_conversation.to_session_response()


async def get_user_chat_sessions(
    session: AsyncSession, 
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[ChatSessionResponse]:
    """
    사용자의 채팅 세션 목록 조회 (최신순).
    """
    result = await session.execute(
        select(ConversationModel)
        .where(ConversationModel.user_id == user_id)
        .order_by(desc(ConversationModel.updated_at))
        .offset(offset)
        .limit(limit)
    )
    
    conversations = result.scalars().all()
    return [conv.to_session_response() for conv in conversations]


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
            updated_at=datetime.now()
        )
    )
    
    await session.flush()
    
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
    채팅 히스토리 조회 (페이지네이션 지원).
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
        return None
    
    # 메시지 목록 처리
    all_messages = conversation.get_messages_as_responses()
    total_messages = len(all_messages)
    
    # 페이지네이션 적용
    paginated_messages = all_messages[offset:offset + limit]
    has_more = offset + limit < total_messages
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=paginated_messages,
        total_messages=total_messages,
        has_more=has_more
    )


async def add_message_to_session(
    session: AsyncSession,
    session_id: str,
    user_id: int,
    content: str,
    role: str
) -> Optional[ChatMessageResponse]:
    """
    채팅 세션에 새 메시지 추가.
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
        return None
    
    # 새 메시지 생성
    message_id = str(uuid.uuid4())
    new_message = {
        "id": message_id,
        "content": content,
        "role": role,
        "timestamp": datetime.now().isoformat()
    }
    
    # 메시지 배열에 추가
    if conversation.messages is None:
        conversation.messages = []
    
    conversation.messages = conversation.messages + [new_message]
    conversation.updated_at = datetime.now()
    
    session.add(conversation)
    await session.flush()
    
    return ChatMessageResponse(
        id=message_id,
        content=content,
        role=role,
        timestamp=datetime.now(),
        session_id=session_id
    )


async def get_user_chat_sessions_count(session: AsyncSession, user_id: int) -> int:
    """
    사용자의 총 채팅 세션 수 조회.
    """
    result = await session.execute(
        select(func.count(ConversationModel.id))
        .where(ConversationModel.user_id == user_id)
    )
    
    return result.scalar() or 0