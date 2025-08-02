"""
채팅 세션 관리 API 라우터
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from traceback import print_exc

from database.session import get_async_db
from api.auth.dependencies import get_current_user
from user.models import UserModel
from conversation.models import (
    ChatSessionCreate, ChatSessionResponse, ChatMessageCreate,
    ChatMessageResponse, ChatHistoryResponse, ChatSessionListResponse
)
from conversation.services import ChatSessionService


router = APIRouter(prefix="/api/chat", tags=["Chat Session Management"])


@router.post("/session", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    새 채팅 세션 생성
    """
    try:
        session_response = await ChatSessionService.create_new_session(
            db=db,
            user_id=current_user.id,
            session_data=session_data
        )
        return session_response
        
    except Exception as e:
        print(f"Error creating session: {e}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions", response_model=ChatSessionListResponse)
async def get_user_chat_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    사용자의 채팅 세션 목록 조회
    """
    try:
        print(f"🔍 Getting sessions for user: {current_user.id}")
        sessions_response = await ChatSessionService.get_user_sessions(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        print(f"✅ Sessions retrieved successfully: {len(sessions_response.sessions) if sessions_response else 0}")
        return sessions_response
        
    except Exception as e:
        print(f"❌ Error getting sessions: {str(e)}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    특정 채팅 세션 조회
    """
    try:
        session_response = await ChatSessionService.get_session_by_id(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return session_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting session: {str(e)}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    채팅 세션 삭제
    """
    try:
        deleted = await ChatSessionService.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return {"success": True, "message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting session: {str(e)}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.put("/session/{session_id}/title", response_model=ChatSessionResponse)
async def update_session_title(
    session_id: str,
    title_data: dict,  # {"title": "new title"}
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    채팅 세션 제목 업데이트
    """
    try:
        new_title = title_data.get("title")
        if not new_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title is required"
            )
        
        updated_session = await ChatSessionService.update_session_title(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            new_title=new_title
        )
        
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return updated_session
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating session title: {str(e)}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session title: {str(e)}"
        )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str = Query(..., description="Session ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    채팅 히스토리 조회
    """
    try:
        history_response = await ChatSessionService.get_session_history(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        if not history_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return history_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting chat history: {str(e)}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.post("/message", response_model=ChatMessageResponse)
async def save_chat_message(
    message_data: ChatMessageCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    채팅 메시지 저장 (백업용)
    실제 채팅은 WebSocket을 통해 처리되고, 이 API는 메시지 저장용
    """
    try:
        # 세션 접근 권한 확인
        has_access = await ChatSessionService.validate_session_access(
            db=db,
            session_id=message_data.session_id,
            user_id=current_user.id
        )
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        message_response = await ChatSessionService.add_message(
            db=db,
            session_id=message_data.session_id,
            user_id=current_user.id,
            message_data=message_data
        )
        
        if not message_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return message_response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving message: {str(e)}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save message: {str(e)}"
        )


@router.get("/session/{session_id}/validate")
async def validate_session_access(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    세션 접근 권한 확인
    """
    try:
        has_access = await ChatSessionService.validate_session_access(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        return {
            "session_id": session_id,
            "has_access": has_access,
            "user_id": current_user.id
        }
        
    except Exception as e:
        print(f"❌ Error validating session access: {str(e)}")
        print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate session access: {str(e)}"
        )