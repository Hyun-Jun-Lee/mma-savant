"""
WebSocket 연결 관리자
실시간 채팅을 위한 WebSocket 연결 및 메시지 처리
"""
import json
import uuid
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from user.models import UserModel
from conversation.services import ChatSessionService
from llm.langchain_service import get_langchain_service, LangChainLLMService


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 사용자별 연결: {user_id: Set[connection_id]}
        self.user_connections: Dict[int, Set[str]] = {}
        
        # 연결별 사용자: {connection_id: UserModel}
        self.connection_users: Dict[str, UserModel] = {}
        
        # 세션별 연결: {session_id: Set[connection_id]}
        self.session_connections: Dict[str, Set[str]] = {}
        
        # LLM 서비스 (LangChain 사용)
        self.llm_service: LangChainLLMService = None
        self._initializing = False
    
    async def _ensure_llm_service(self):
        """LLM 서비스 초기화 보장"""
        if self.llm_service is not None:
            return
        
        if self._initializing:
            # 다른 요청이 이미 초기화 중인 경우 대기
            while self._initializing:
                await asyncio.sleep(0.1)
            return
        
        self._initializing = True
        try:
            self.llm_service = await get_langchain_service()
            print("✅ LangChain LLM service initialized")
        finally:
            self._initializing = False
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user: UserModel,
        session_id: Optional[str] = None
    ) -> str:
        """
        새 WebSocket 연결 수락 및 등록
        """
        try:
            # WebSocket 연결 수락은 routes.py에서 이미 처리됨
            # 여기서는 상태만 확인
            
            # WebSocket 상태 확인
            if websocket.client_state.name != "CONNECTED":
                print(f"❌ WebSocket not properly connected: {websocket.client_state.name}")
                raise ConnectionError("WebSocket connection failed")
            
            # 고유 연결 ID 생성
            connection_id = str(uuid.uuid4())
            
            # 연결 등록
            self.active_connections[connection_id] = websocket
            self.connection_users[connection_id] = user
            
            # 사용자별 연결 관리
            if user.id not in self.user_connections:
                self.user_connections[user.id] = set()
            self.user_connections[user.id].add(connection_id)
            
            # 세션별 연결 관리 (세션 ID가 있는 경우)
            if session_id:
                if session_id not in self.session_connections:
                    self.session_connections[session_id] = set()
                self.session_connections[session_id].add(connection_id)
            
            print(f"🔌 User {user.id} connected with connection {connection_id}")
            
            # 연결 등록만 수행, 메시지 전송은 routes.py에서 처리
            
            return connection_id
            
        except Exception as e:
            print(f"❌ Failed to establish WebSocket connection: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """
        WebSocket 연결 해제 및 정리
        """
        if connection_id not in self.active_connections:
            return
        
        # 사용자 정보 가져오기
        user = self.connection_users.get(connection_id)
        
        # 연결 정리
        del self.active_connections[connection_id]
        del self.connection_users[connection_id]
        
        # 사용자별 연결에서 제거
        if user and user.id in self.user_connections:
            self.user_connections[user.id].discard(connection_id)
            if not self.user_connections[user.id]:
                del self.user_connections[user.id]
        
        # 세션별 연결에서 제거
        for session_id in list(self.session_connections.keys()):
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
        
        print(f"🔌 Connection {connection_id} disconnected")
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """
        특정 연결에 메시지 전송
        """
        if connection_id not in self.active_connections:
            print(f"⚠️ Connection {connection_id} not found in active connections")
            return
            
        websocket = self.active_connections[connection_id]
        
        try:
            
            # WebSocket이 CONNECTED 상태가 아닌 경우 즉시 제거
            if websocket.client_state.name != "CONNECTED":
                print(f"🔌 WebSocket {connection_id} not in CONNECTED state ({websocket.client_state.name}), removing")
                await self.disconnect(connection_id)
                return
            
            # 추가 안전 검사: WebSocket 객체가 유효한지 확인
            if not hasattr(websocket, 'send_text'):
                print(f"❌ WebSocket {connection_id} missing send_text method")
                await self.disconnect(connection_id)
                return
                
            
            # 메시지 전송
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ Failed to send message to {connection_id}: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            print(f"🔍 WebSocket state during error: {websocket.client_state.name if hasattr(websocket, 'client_state') else 'unknown'}")
            
            # 모든 전송 관련 에러는 연결 정리 (더 포괄적으로)
            if any(keyword in error_msg for keyword in [
                "disconnect", "closed", "close", "send", "connection", 
                "websocket is not connected", "need to call", "accept",
                "not connected", "receive"
            ]):
                print(f"🔌 Removing connection {connection_id} due to send error")
                await self.disconnect(connection_id)
                # 에러를 re-raise하여 상위에서 처리하도록 함
                raise ConnectionError(f"WebSocket connection lost for {connection_id}")
    
    async def send_to_user(self, user_id: int, message: dict):
        """
        특정 사용자의 모든 연결에 메시지 전송
        """
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self.send_to_connection(connection_id, message)
    
    async def send_to_session(self, session_id: str, message: dict):
        """
        특정 세션의 모든 연결에 메시지 전송
        """
        if session_id in self.session_connections:
            for connection_id in self.session_connections[session_id].copy():
                await self.send_to_connection(connection_id, message)
    
    async def broadcast(self, message: dict):
        """
        모든 연결에 메시지 브로드캐스트
        """
        for connection_id in list(self.active_connections.keys()):
            await self.send_to_connection(connection_id, message)
    
    async def handle_user_message(
        self,
        connection_id: str,
        message_data: dict,
        db: AsyncSession
    ):
        """
        사용자 메시지 처리 및 LLM 응답 생성
        """
        try:
            user = self.connection_users.get(connection_id)
            if not user:
                await self.send_to_connection(connection_id, {
                    "type": "error",
                    "error": "User not found",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # 메시지 데이터 검증
            content = message_data.get("content", "").strip()
            session_id = message_data.get("session_id")
            
            if not content:
                print(f"❌ Empty message content from {connection_id}")
                await self.send_to_connection(connection_id, {
                    "type": "error",
                    "error": "Message content is required",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # 세션 검증 또는 생성
            if session_id:
                # 기존 세션 검증
                session_valid = await ChatSessionService.validate_session_access(
                    db=db,
                    session_id=session_id,
                    user_id=user.id
                )
                
                if not session_valid:
                    # 검증 실패 시 에러 대신 새 세션 생성
                    from conversation.services import get_or_create_session
                    session_response = await get_or_create_session(
                        db=db,
                        user_id=user.id
                    )
                    session_id = session_response.session_id
                    print(f"✅ New session created: session_id={session_id}")
                else:
                    print(f"✅ Session validation successful: session_id={session_id}")
            else:
                # 새 세션 생성
                print(f"🆕 Creating new session for user {user.id}")
                from conversation.services import get_or_create_session
                session_response = await get_or_create_session(
                    db=db,
                    user_id=user.id
                )
                session_id = session_response.session_id
                print(f"✅ New session created: session_id={session_id}")
            
            # 사용자 메시지를 데이터베이스에 저장
            from conversation.models import ChatMessageCreate
            user_message = ChatMessageCreate(
                content=content,
                role="user",
                session_id=session_id
            )
            
            saved_message = await ChatSessionService.add_message(
                db=db,
                session_id=session_id,
                user_id=user.id,
                message_data=user_message
            )
            
            # 사용자 메시지 확인 응답
            await self.send_to_connection(connection_id, {
                "type": "message_received",
                "message_id": saved_message.id if saved_message else str(uuid.uuid4()),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # 타이핑 상태 시작
            await self.send_to_connection(connection_id, {
                "type": "typing",
                "is_typing": True,
                "timestamp": datetime.now().isoformat()
            })
            
            # 대화 히스토리 조회
            history_response = await ChatSessionService.get_session_history(
                db=db,
                session_id=session_id,
                user_id=user.id,
                limit=10  # 최근 10개 메시지만
            )
            
            conversation_history = []
            if history_response:
                conversation_history = [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in history_response.messages
                ]
            
            # LLM 서비스 초기화 확인
            await self._ensure_llm_service()
            
            # LLM 스트리밍 응답 생성
            assistant_content = ""
            assistant_message_id = str(uuid.uuid4())
            
            async for chunk in self.llm_service.generate_streaming_chat_response(
                user_message=content,
                conversation_history=conversation_history,
                session_id=session_id
            ):
                
                if chunk["type"] == "start":
                    await self.send_to_connection(connection_id, {
                        "type": "response_start",
                        "message_id": assistant_message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    })
                
                elif chunk["type"] == "content":
                    assistant_content += chunk["content"]
                    chunk_data = {
                        "type": "response_chunk",
                        "content": chunk["content"],
                        "message_id": assistant_message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    }
                    try:
                        await self.send_to_connection(connection_id, chunk_data)
                    except Exception as e:
                        raise
                
                elif chunk["type"] == "end":
                    # 타이핑 상태 종료
                    await self.send_to_connection(connection_id, {
                        "type": "typing",
                        "is_typing": False,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # 어시스턴트 메시지를 데이터베이스에 저장
                    assistant_message = ChatMessageCreate(
                        content=assistant_content,
                        role="assistant",
                        session_id=session_id
                    )
                    
                    await ChatSessionService.add_message(
                        db=db,
                        session_id=session_id,
                        user_id=user.id,
                        message_data=assistant_message
                    )
                    
                    await self.send_to_connection(connection_id, {
                        "type": "response_end",
                        "message_id": assistant_message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    })
                
                elif chunk["type"] == "error":
                    await self.send_to_connection(connection_id, {
                        "type": "typing",
                        "is_typing": False,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    await self.send_to_connection(connection_id, {
                        "type": "error",
                        "error": chunk["error"],
                        "message_id": assistant_message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    })
        
        except Exception as e:
            print(f"❌ Error handling user message: {e}")
            await self.send_to_connection(connection_id, {
                "type": "error",
                "error": f"Failed to process message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
    
    def get_connection_count(self) -> int:
        """활성 연결 수 반환"""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: int) -> int:
        """특정 사용자의 연결 수 반환"""
        return len(self.user_connections.get(user_id, set()))
    
    def get_stats(self) -> dict:
        """연결 통계 반환"""
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "total_sessions": len(self.session_connections),
            "timestamp": datetime.now().isoformat()
        }


# 글로벌 연결 관리자 인스턴스
connection_manager = ConnectionManager()