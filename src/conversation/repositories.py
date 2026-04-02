from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import select, update, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from conversation.models import (
    ConversationModel, MessageModel,
    ChatSessionResponse, ChatMessageResponse, ChatHistoryResponse
)
from common.utils import utc_now

# 채팅 세션 관리 함수들

async def create_chat_session(
    session: AsyncSession,
    user_id: int,
    title: Optional[str] = None
) -> ChatSessionResponse:
    """
    새 채팅 세션 생성.
    """
    # 제목이 없으면 기본 제목 생성
    if not title:
        title = f"채팅 {utc_now().strftime('%Y-%m-%d %H:%M')}"

    # 새로운 대화 세션 생성 (메시지는 별도 테이블에 저장)
    db_conversation = ConversationModel(
        user_id=user_id,
        title=title
    )

    session.add(db_conversation)
    await session.flush()
    session_response = db_conversation.to_session_response()

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
        .outerjoin(MessageModel, ConversationModel.id == MessageModel.conversation_id)
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
    conversation_id: int,
    user_id: int
) -> Optional[ChatSessionResponse]:
    """
    특정 채팅 세션 조회 (사용자 권한 확인 포함).
    """
    result = await session.execute(
        select(ConversationModel)
        .where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id
        )
    )

    conversation = result.scalar_one_or_none()
    return conversation.to_session_response() if conversation else None


async def delete_chat_session(
    session: AsyncSession,
    conversation_id: int,
    user_id: int
) -> bool:
    """
    채팅 세션 삭제 (사용자 권한 확인 포함).
    """
    result = await session.execute(
        select(ConversationModel)
        .where(
            ConversationModel.id == conversation_id,
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
    conversation_id: int,
    user_id: int,
    new_title: str
) -> Optional[ChatSessionResponse]:
    """
    채팅 세션 제목 업데이트.
    """
    await session.execute(
        update(ConversationModel)
        .where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id
        )
        .values(
            title=new_title,
            updated_at=utc_now()
        )
    )

    await session.flush()

    # 업데이트된 세션 조회
    return await get_chat_session_by_id(session, conversation_id, user_id)


async def get_chat_history(
    session: AsyncSession,
    conversation_id: int,
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
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id
        )
    )

    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        return None

    # 전체 메시지 수 조회
    total_count_result = await session.execute(
        select(func.count(MessageModel.id))
        .where(MessageModel.conversation_id == conversation_id)
    )
    total_messages = total_count_result.scalar() or 0

    # 메시지 목록 조회 (페이지네이션 적용)
    messages_result = await session.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == conversation_id)
        .order_by(MessageModel.created_at)
        .offset(offset)
        .limit(limit)
    )

    messages = messages_result.scalars().all()
    message_responses = [msg.to_response() for msg in messages]

    has_more = offset + limit < total_messages

    return ChatHistoryResponse(
        conversation_id=conversation_id,
        messages=message_responses,
        total_messages=total_messages,
        has_more=has_more
    )


async def add_message_to_session(
    session: AsyncSession,
    conversation_id: int,
    user_id: int,
    content: str,
    role: str,
    tool_results: Optional[List[dict]] = None,
    visualization: Optional[List[dict]] = None,
) -> Optional[ChatMessageResponse]:
    """
    채팅 세션에 새 메시지 추가 (새로운 Message 테이블 사용).
    """
    # 세션 존재 확인
    result = await session.execute(
        select(ConversationModel)
        .where(
            ConversationModel.id == conversation_id,
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
        conversation_id=conversation_id,
        content=content,
        role=role,
        tool_results=tool_results,
        visualization=visualization,
    )
    
    session.add(new_message)
    
    # 대화 세션의 updated_at 갱신
    conversation.updated_at = utc_now()
    session.add(conversation)
    
    await session.flush()
    saved_message = new_message.to_response()

    return saved_message


async def get_recent_messages(
    session: AsyncSession,
    conversation_id: int,
    limit: int = 10,
) -> List[MessageModel]:
    """
    LLM 컨텍스트용: 최신 N개 메시지를 시간순(ASC)으로 반환.
    WebSocket에서 이미 인증된 내부 호출 전용 — user_id 검증 없음.
    """
    result = await session.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == conversation_id)
        .order_by(MessageModel.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()
    return messages


async def add_message_direct(
    session: AsyncSession,
    conversation_id: int,
    content: str,
    role: str,
    tool_results: Optional[List[dict]] = None,
    visualization: Optional[List[dict]] = None,
) -> ChatMessageResponse:
    """
    내부용: 세션 존재 확인 없이 메시지 직접 INSERT.
    WebSocket 핸들러처럼 이미 conversation_id 유효성이 보장된 경우 사용.
    """
    message = MessageModel(
        message_id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        content=content,
        role=role,
        tool_results=tool_results,
        visualization=visualization,
    )
    session.add(message)

    # 대화 세션의 updated_at 갱신
    await session.execute(
        update(ConversationModel)
        .where(ConversationModel.id == conversation_id)
        .values(updated_at=utc_now())
    )

    await session.flush()
    saved = message.to_response()
    return saved


async def get_user_chat_sessions_count(session: AsyncSession, user_id: int) -> int:
    """
    사용자의 총 채팅 세션 수 조회.
    """
    result = await session.execute(
        select(func.count(ConversationModel.id))
        .where(ConversationModel.user_id == user_id)
    )

    return result.scalar() or 0


async def get_total_conversations_count(session: AsyncSession) -> int:
    """
    전체 채팅 세션 수 조회 (관리자용).
    """
    result = await session.execute(
        select(func.count(ConversationModel.id))
    )

    return result.scalar() or 0


# =========================================================================
# 대화 압축 영속화 (Persistent Conversation Compression)
# =========================================================================

async def get_messages_after(
    session: AsyncSession,
    conversation_id: int,
    after_message_id: str,
) -> List[MessageModel]:
    """
    boundary message_id 이후의 메시지를 시간순(ASC) 반환.
    boundary가 없으면 get_recent_messages(limit=10) 폴백.
    """
    # boundary 메시지의 created_at 조회
    boundary_result = await session.execute(
        select(MessageModel.created_at)
        .where(
            MessageModel.conversation_id == conversation_id,
            MessageModel.message_id == after_message_id,
        )
    )
    boundary_time = boundary_result.scalar_one_or_none()

    if boundary_time is None:
        return await get_recent_messages(session, conversation_id, limit=10)

    result = await session.execute(
        select(MessageModel)
        .where(
            MessageModel.conversation_id == conversation_id,
            MessageModel.created_at > boundary_time,
        )
        .order_by(asc(MessageModel.created_at))
    )
    return list(result.scalars().all())


async def get_conversation_compression(
    session: AsyncSession,
    conversation_id: int,
) -> Optional[dict]:
    """
    conversation의 압축 메타데이터 반환.
    압축 없으면 None.
    """
    result = await session.execute(
        select(
            ConversationModel.compressed_context,
            ConversationModel.compressed_sql_context,
            ConversationModel.compressed_until_message_id,
        )
        .where(ConversationModel.id == conversation_id)
    )
    row = result.one_or_none()
    if row is None:
        return None

    compressed_context, compressed_sql_context, compressed_until_message_id = row
    if not compressed_until_message_id:
        return None

    return {
        "compressed_context": compressed_context,
        "compressed_sql_context": compressed_sql_context,
        "compressed_until_message_id": compressed_until_message_id,
    }


async def update_conversation_compression(
    session: AsyncSession,
    conversation_id: int,
    compressed_context: str,
    compressed_sql_context: Optional[list],
    compressed_until_message_id: str,
) -> None:
    """압축 필드 3개 업데이트."""
    await session.execute(
        update(ConversationModel)
        .where(ConversationModel.id == conversation_id)
        .values(
            compressed_context=compressed_context,
            compressed_sql_context=compressed_sql_context,
            compressed_until_message_id=compressed_until_message_id,
            updated_at=utc_now(),
        )
    )
    await session.flush()


async def get_message_count_after(
    session: AsyncSession,
    conversation_id: int,
    after_message_id: Optional[str] = None,
) -> int:
    """
    boundary 이후 메시지 수 카운트.
    boundary가 None이면 전체 메시지 수 반환.
    """
    if after_message_id is None:
        result = await session.execute(
            select(func.count(MessageModel.id))
            .where(MessageModel.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    boundary_result = await session.execute(
        select(MessageModel.created_at)
        .where(
            MessageModel.conversation_id == conversation_id,
            MessageModel.message_id == after_message_id,
        )
    )
    boundary_time = boundary_result.scalar_one_or_none()

    if boundary_time is None:
        result = await session.execute(
            select(func.count(MessageModel.id))
            .where(MessageModel.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    result = await session.execute(
        select(func.count(MessageModel.id))
        .where(
            MessageModel.conversation_id == conversation_id,
            MessageModel.created_at > boundary_time,
        )
    )
    return result.scalar() or 0