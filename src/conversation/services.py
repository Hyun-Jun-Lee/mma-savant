"""
채팅 세션 관리 서비스 로직
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from conversation import repositories as conv_repo
from conversation.models import (
    ChatSessionCreate, ChatSessionResponse, ChatMessageCreate, 
    ChatMessageResponse, ChatHistoryResponse, ChatSessionListResponse
)


class ChatSessionService:
    """채팅 세션 관리 서비스"""
    
    @staticmethod
    async def create_new_session(
        db: AsyncSession,
        user_id: int,
        session_data: ChatSessionCreate
    ) -> ChatSessionResponse:
        """
        새 채팅 세션 생성
        """
        return await conv_repo.create_chat_session(
            session=db,
            user_id=user_id,
            title=session_data.title
        )
    
    @staticmethod
    async def get_user_sessions(
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> ChatSessionListResponse:
        """
        사용자의 채팅 세션 목록 조회
        """
        try:
            sessions = await conv_repo.get_user_chat_sessions(
                session=db,
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            total_count = await conv_repo.get_user_chat_sessions_count(db, user_id)
            
            return ChatSessionListResponse(
                sessions=sessions,
                total_sessions=total_count
            )
        except Exception as e:
            print(f"❌ ChatSessionService error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    async def get_session_by_id(
        db: AsyncSession,
        session_id: str,
        user_id: int
    ) -> Optional[ChatSessionResponse]:
        """
        특정 채팅 세션 조회
        """
        return await conv_repo.get_chat_session_by_id(
            session=db,
            session_id=session_id,
            user_id=user_id
        )
    
    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session_id: str,
        user_id: int
    ) -> bool:
        """
        채팅 세션 삭제
        """
        return await conv_repo.delete_chat_session(
            session=db,
            session_id=session_id,
            user_id=user_id
        )
    
    @staticmethod
    async def update_session_title(
        db: AsyncSession,
        session_id: str,
        user_id: int,
        new_title: str
    ) -> Optional[ChatSessionResponse]:
        """
        채팅 세션 제목 업데이트
        """
        return await conv_repo.update_chat_session_title(
            session=db,
            session_id=session_id,
            user_id=user_id,
            new_title=new_title
        )
    
    @staticmethod
    async def get_session_history(
        db: AsyncSession,
        session_id: str,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Optional[ChatHistoryResponse]:
        """
        채팅 히스토리 조회
        """
        return await conv_repo.get_chat_history(
            session=db,
            session_id=session_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
    
    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: str,
        user_id: int,
        message_data: ChatMessageCreate
    ) -> Optional[ChatMessageResponse]:
        """
        채팅 세션에 메시지 추가
        """
        return await conv_repo.add_message_to_session(
            session=db,
            session_id=session_id,
            user_id=user_id,
            content=message_data.content,
            role=message_data.role
        )
    
    @staticmethod
    async def validate_session_access(
        db: AsyncSession,
        session_id: str,
        user_id: int
    ) -> bool:
        """
        사용자가 해당 세션에 접근 권한이 있는지 확인
        """
        session_data = await conv_repo.get_chat_session_by_id(
            session=db,
            session_id=session_id,
            user_id=user_id
        )
        return session_data is not None


# 편의 함수들

async def create_session_with_first_message(
    db: AsyncSession,
    user_id: int,
    first_message: str,
    title: Optional[str] = None
) -> tuple[ChatSessionResponse, ChatMessageResponse]:
    """
    첫 메시지와 함께 새 세션 생성
    """
    # 세션 생성
    session_create = ChatSessionCreate(title=title)
    session_response = await ChatSessionService.create_new_session(
        db=db,
        user_id=user_id,
        session_data=session_create
    )
    
    # 첫 메시지 추가
    message_create = ChatMessageCreate(
        content=first_message,
        role="user",
        session_id=session_response.session_id
    )
    
    message_response = await ChatSessionService.add_message(
        db=db,
        session_id=session_response.session_id,
        user_id=user_id,
        message_data=message_create
    )
    
    return session_response, message_response


async def get_or_create_session(
    db: AsyncSession,
    user_id: int,
    session_id: Optional[str] = None
) -> ChatSessionResponse:
    """
    세션 ID가 있으면 조회, 없으면 새로 생성
    """
    if session_id:
        # 기존 세션 조회
        existing_session = await ChatSessionService.get_session_by_id(
            db=db,
            session_id=session_id,
            user_id=user_id
        )
        
        if existing_session:
            return existing_session
    
    # 새 세션 생성
    session_create = ChatSessionCreate()
    return await ChatSessionService.create_new_session(
        db=db,
        user_id=user_id,
        session_data=session_create
    )


async def add_assistant_response(
    db: AsyncSession,
    session_id: str,
    user_id: int,
    response_content: str
) -> Optional[ChatMessageResponse]:
    """
    AI 어시스턴트 응답 메시지 추가
    """
    message_create = ChatMessageCreate(
        content=response_content,
        role="assistant",
        session_id=session_id
    )
    
    return await ChatSessionService.add_message(
        db=db,
        session_id=session_id,
        user_id=user_id,
        message_data=message_create
    )