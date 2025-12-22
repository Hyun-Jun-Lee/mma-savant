"""
WebSocket API 라우터
실시간 채팅을 위한 WebSocket 엔드포인트
"""
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection.postgres_conn import get_async_db
from api.auth.jwt_handler import jwt_handler
from user import repositories as user_repo
from user.models import UserModel
from api.websocket.manager import connection_manager
from common.utils import kr_time_now


router = APIRouter(prefix="/ws", tags=["WebSocket"])


async def get_user_from_token(token: str, db: AsyncSession) -> UserModel:
    """
    JWT 토큰에서 사용자 정보 추출 (WebSocket용)
    - 일반 로그인: user_id로 조회
    - OAuth 로그인: email로 조회/생성
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

        user_schema = None

        # 1. 일반 로그인 (user_id가 있는 경우)
        if token_data.user_id:
            user_schema = await user_repo.get_user_by_id(db, token_data.user_id)

            if not user_schema:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

        # 2. OAuth 로그인 (이메일이 있는 경우)
        elif token_data.email:
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

        # 3. provider_id로 조회 (fallback)
        else:
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    conversation_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    채팅을 위한 WebSocket 엔드포인트

    연결 방법:
    ws://localhost:8000/ws/chat?token={jwt_token}&conversation_id={conversation_id}
    """
    connection_id = None
    
    try:
        # 토큰 검증
        if not token:
            await websocket.accept()
            await websocket.close(code=4001, reason="Token required")
            return
        
        # 사용자 인증
        try:
            user = await get_user_from_token(token, db)
        except HTTPException as e:
            await websocket.accept()
            await websocket.close(code=4001, reason=f"Authentication failed: {e.detail}")
            return
        
        # 명시적으로 WebSocket 연결 수락
        await websocket.accept()
        
        # WebSocket 연결 등록
        connection_id = await connection_manager.connect(
            websocket=websocket,
            user=user,
            conversation_id=conversation_id
        )
        
        # 잠깐 대기하여 WebSocket 완전히 준비되도록 함
        import asyncio
        await asyncio.sleep(0.2)  # 대기 시간 증가
        
        # WebSocket 상태 재확인
        if websocket.client_state.name != "CONNECTED":
            print(f"❌ WebSocket not in CONNECTED state after delay: {websocket.client_state.name}")
            return
        
        # 연결 확인 메시지 전송
        try:
            print(f"📩 Sending connection established message to {connection_id}")
            await connection_manager.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user.id,
                "conversation_id": conversation_id,
                "timestamp": kr_time_now().isoformat(),
                "message": "연결이 성공적으로 설정되었습니다."
            })
        except ConnectionError as e:
            print(f"❌ Connection lost during message send: {e}")
            return  # 연결 실패 시 즉시 종료
        except Exception as e:
            print(f"❌ Failed to send connection established message to {connection_id}: {e}")
            return  # 기타 에러도 연결 종료
        
        # 메시지 수신 루프
        while True:
            try:
                # WebSocket 연결 상태 확인
                if websocket.client_state.name != "CONNECTED":
                    print(f"🔌 WebSocket no longer connected: {websocket.client_state.name}")
                    break
                
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
                        "timestamp": kr_time_now().isoformat()
                    })
                
                elif message_type == "typing":
                    # NOTE : 현재는 사용자가 typing 상태 일 때 따로 준비하는 작업이 없음.
                    is_typing = message_data.get("is_typing", False)
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "typing_echo",
                        "is_typing": is_typing,
                        "timestamp": kr_time_now().isoformat()
                    })
                
                else:
                    # 알 수 없는 메시지 타입
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "error",
                        "error": f"Unknown message type: {message_type}",
                        "timestamp": kr_time_now().isoformat()
                    })
                    
            except json.JSONDecodeError:
                await connection_manager.send_to_connection(connection_id, {
                    "type": "error",
                    "error": "Invalid JSON format",
                    "timestamp": kr_time_now().isoformat()
                })
            
            except WebSocketDisconnect:
                print(f"🔌 WebSocket disconnected during message processing: {connection_id}")
                break
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Error processing message: {error_msg}")
                
                # WebSocket 연결 관련 에러는 즉시 루프 종료
                if any(keyword in error_msg.lower() for keyword in [
                    "disconnect", "receive", "send", "websocket is not connected", 
                    "need to call", "accept", "closed", "connection", "not connected"
                ]):
                    print(f"🔌 Breaking loop due to connection error: {connection_id}")
                    break
                
                # 연결 상태 재확인
                if websocket.client_state.name != "CONNECTED":
                    print(f"🔌 WebSocket no longer connected during error handling: {websocket.client_state.name}")
                    break
                
                try:
                    await connection_manager.send_to_connection(connection_id, {
                        "type": "error",
                        "error": f"Failed to process message: {error_msg}",
                        "timestamp": kr_time_now().isoformat()
                    })
                except ConnectionError:
                    # ConnectionError는 이미 연결이 정리되었으므로 즉시 루프 종료
                    print(f"🔌 Connection lost during error response, breaking loop: {connection_id}")
                    break
                except Exception:
                    # 에러 메시지 전송도 실패하면 연결 문제이므로 루프 종료
                    print(f"🔌 Failed to send error message, breaking loop: {connection_id}")
                    break
    
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
        "timestamp": kr_time_now().isoformat()
    }