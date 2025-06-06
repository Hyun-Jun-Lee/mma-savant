from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conversation.models import ConversationModel, ConversationSchema
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