"""
WebSocket API 라우터
실시간 채팅을 위한 WebSocket 엔드포인트
"""
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_async_db
from api.auth.jwt_handler import jwt_handler
from user import repositories as user_repo
from user.models import UserModel
from .manager import connection_manager


router = APIRouter(prefix="/ws", tags=["WebSocket"])


async def get_user_from_token(token: str, db: AsyncSession) -> UserModel:
    """
    JWT 토큰에서 사용자 정보 추출 (WebSocket용)
    """
    try:
        # JWT 토큰 디코딩
        token_data = jwt_handler.decode_token(token)
        
        # 토큰 만료 확인
        if not jwt_handler.verify_token_expiry(token_data):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # 사용자 조회
        if token_data.email:
            user_schema = await user_repo.get_user_by_email(db, token_data.email)
            
            if not user_schema:
                # OAuth 사용자가 처음 로그인하는 경우 자동 생성
                user_schema = await user_repo.create_oauth_user(
                    session=db,
                    email=token_data.email,
                    name=token_data.name,
                    picture=token_data.picture,
                    provider_id=token_data.sub
                )
            
            # UserSchema를 UserModel로 변환
            user = UserModel.from_schema(user_schema)
            
        else:
            # 이메일이 없는 경우 sub(provider ID)로 조회
            user_schema = await user_repo.get_user_by_provider_id(db, token_data.sub)
            
            if not user_schema:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # UserSchema를 UserModel로 변환
            user = UserModel.from_schema(user_schema)
        
        # 사용자 활성 상태 확인
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    채팅을 위한 WebSocket 엔드포인트
    
    연결 방법:
    ws://localhost:8000/ws/chat?token={jwt_token}&session_id={session_id}
    """
    connection_id = None
    
    try:
        # 토큰 검증
        if not token:
            await websocket.close(code=4001, reason="Token required")
            return
        
        # 사용자 인증
        try:
            user = await get_user_from_token(token, db)
        except HTTPException as e:
            await websocket.close(code=4001, reason=f"Authentication failed: {e.detail}")
            return
        
        # WebSocket 연결 수락 및 등록
        connection_id = await connection_manager.connect(
            websocket=websocket,
            user=user,
            session_id=session_id
        )
        
        # 환영 메시지 전송
        if not session_id:
            # 새 세션인 경우 환영 메시지
            welcome_message = connection_manager.llm_service.get_conversation_starter()
            await connection_manager.send_to_connection(connection_id, {
                "type": "welcome",
                "content": welcome_message,
                "timestamp": "2024-01-01T00:00:00.000Z"
            })
        
        # 메시지 수신 루프
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # 메시지 타입별 처리
                message_type = message_data.get("type", "message")
                
                if message_type == "message":
                    # 사용자 메시지 처리
                    await connection_manager.handle_user_message(
                        connection_id=connection_id,
                        message_data=message_data,
                        db=db
                    )
                
                elif message_type == "ping":
                    # 핑-퐁 처리 (연결 상태 확인)
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "pong",
                        "timestamp": "2024-01-01T00:00:00.000Z"
                    })
                
                elif message_type == "typing":
                    # 타이핑 상태 브로드캐스트 (필요시)
                    is_typing = message_data.get("is_typing", False)
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "typing_echo",
                        "is_typing": is_typing,
                        "timestamp": "2024-01-01T00:00:00.000Z"
                    })
                
                else:
                    # 알 수 없는 메시지 타입
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "error",
                        "error": f"Unknown message type: {message_type}",
                        "timestamp": "2024-01-01T00:00:00.000Z"
                    })
                    
            except json.JSONDecodeError:
                await connection_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "error": "Invalid JSON format",
                    "timestamp": "2024-01-01T00:00:00.000Z"
                })
            
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                await connection_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "error": f"Failed to process message: {str(e)}",
                    "timestamp": "2024-01-01T00:00:00.000Z"
                })
    
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {connection_id}")
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    
    finally:
        # 연결 정리
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.get("/stats")
async def get_websocket_stats():
    """
    WebSocket 연결 통계 조회
    """
    return connection_manager.get_stats()


@router.get("/health")
async def websocket_health_check():
    """
    WebSocket 서비스 상태 확인
    """
    stats = connection_manager.get_stats()
    return {
        "status": "healthy",
        "service": "websocket",
        "stats": stats,
        "timestamp": "2024-01-01T00:00:00.000Z"
    }