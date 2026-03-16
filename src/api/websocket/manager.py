"""
WebSocket 연결 관리자
실시간 채팅을 위한 WebSocket 연결 및 메시지 처리
"""
import json
import uuid
import asyncio
from typing import Dict, List, Optional, Set, Tuple, Any
from traceback import format_exc

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from user.models import UserModel
from user.services import check_usage_limit, get_user_usage
from conversation.services import get_or_create_session
from llm.langchain_service import get_langchain_service, LangChainLLMService
from common.logging_config import get_logger
from common.utils import utc_now, parse_visualization_from_content

LOGGER = get_logger(__name__)

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 사용자별 연결: {user_id: Set[connection_id]}
        self.user_connections: Dict[int, Set[str]] = {}
        
        # 연결별 사용자: {connection_id: UserModel}
        self.connection_users: Dict[str, UserModel] = {}
        
        # 대화별 연결: {conversation_id: Set[connection_id]}
        self.conversation_connections: Dict[int, Set[str]] = {}
        
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
            LOGGER.info("✅ LangChain LLM service initialized")
        finally:
            self._initializing = False

    
    def _process_tool_result(self, result):
        """
        Tool 결과를 처리하여 created_at, updated_at 필드를 제거하고 구조화된 형태로 반환
        """
        
        try:
            # 결과가 문자열인 경우 JSON으로 파싱 시도
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 원본 문자열 반환 (길이 제한)
                    return result[:500] + "..." if len(str(result)) > 500 else str(result)
            else:
                parsed_result = result
            
            # 리스트인 경우 각 항목에서 timestamp 필드들 제거
            if isinstance(parsed_result, list):
                cleaned_result = []
                for item in parsed_result:
                    if isinstance(item, dict):
                        # created_at, updated_at 필드 제거
                        cleaned_item = {k: v for k, v in item.items() 
                                      if k not in ['created_at', 'updated_at']}
                        cleaned_result.append(cleaned_item)
                    else:
                        cleaned_result.append(item)
                return cleaned_result
            
            # 딕셔너리인 경우 timestamp 필드들 제거
            elif isinstance(parsed_result, dict):
                return {k: v for k, v in parsed_result.items() 
                       if k not in ['created_at', 'updated_at']}
            
            # 기타 타입은 원본 반환
            else:
                result_str = str(parsed_result)
                return result_str[:500] + "..." if len(result_str) > 500 else result_str
                
        except Exception as e:
            LOGGER.warning(f"⚠️ Error processing tool result: {e}")
            LOGGER.error(format_exc())
            # 에러 발생 시 원본 문자열 반환 (길이 제한)
            result_str = str(result)
            return result_str[:500] + "..." if len(result_str) > 500 else result_str
    
    async def connect(
        self,
        websocket: WebSocket,
        user: UserModel,
        conversation_id: Optional[int] = None
    ) -> str:
        """
        새 WebSocket 연결 수락 및 등록
        """
        try:
            # WebSocket 연결 수락은 routes.py에서 이미 처리됨
            # 여기서는 상태만 확인
            
            # WebSocket 상태 확인
            if websocket.client_state.name != "CONNECTED":
                LOGGER.error(f"❌ WebSocket not properly connected: {websocket.client_state.name}")
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
            
            # 대화별 연결 관리 (대화 ID가 있는 경우)
            if conversation_id:
                if conversation_id not in self.conversation_connections:
                    self.conversation_connections[conversation_id] = set()
                self.conversation_connections[conversation_id].add(connection_id)
            
            LOGGER.info(f"🔌 User {user.id} connected with connection {connection_id}")
            
            # 연결 등록만 수행, 메시지 전송은 routes.py에서 처리
            
            return connection_id
            
        except Exception as e:
            LOGGER.error(f"❌ Failed to establish WebSocket connection: {e}")
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
        
        # 대화별 연결에서 제거
        for conversation_id in list(self.conversation_connections.keys()):
            self.conversation_connections[conversation_id].discard(connection_id)
            if not self.conversation_connections[conversation_id]:
                del self.conversation_connections[conversation_id]
        
        LOGGER.info(f"🔌 Connection {connection_id} disconnected")
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """
        특정 연결에 메시지 전송
        """
        if connection_id not in self.active_connections:
            LOGGER.warning(f"⚠️ Connection {connection_id} not found in active connections")
            return
            
        websocket = self.active_connections[connection_id]
        
        try:
            
            # WebSocket이 CONNECTED 상태가 아닌 경우 즉시 제거
            if websocket.client_state.name != "CONNECTED":
                LOGGER.warning(f"🔌 WebSocket {connection_id} not in CONNECTED state ({websocket.client_state.name}), removing")
                await self.disconnect(connection_id)
                return
            
            # 추가 안전 검사: WebSocket 객체가 유효한지 확인
            if not hasattr(websocket, 'send_text'):
                LOGGER.error(f"❌ WebSocket {connection_id} missing send_text method")
                await self.disconnect(connection_id)
                return
                

            # 메시지 전송
            message_json = json.dumps(message, ensure_ascii=False)
            await websocket.send_text(message_json)
            
        except Exception as e:
            error_msg = str(e).lower()
            LOGGER.error(f"❌ Failed to send message to {connection_id}: {e}")
            LOGGER.debug(f"🔍 Error type: {type(e).__name__}")
            LOGGER.debug(f"🔍 WebSocket state during error: {websocket.client_state.name if hasattr(websocket, 'client_state') else 'unknown'}")
            
            # 모든 전송 관련 에러는 연결 정리 (더 포괄적으로)
            if any(keyword in error_msg for keyword in [
                "disconnect", "closed", "close", "send", "connection", 
                "websocket is not connected", "need to call", "accept",
                "not connected", "receive"
            ]):
                LOGGER.warning(f"🔌 Removing connection {connection_id} due to send error")
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
    
    async def send_to_conversation(self, conversation_id: int, message: dict):
        """
        특정 대화의 모든 연결에 메시지 전송
        """
        if conversation_id in self.conversation_connections:
            for connection_id in self.conversation_connections[conversation_id].copy():
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
        message_data: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """
        사용자 메시지 처리 메인 진입점
        스트리밍 방식으로 LLM 응답을 실시간 전송
        """
        try:
            # 검증 단계
            user = await self._validate_user_connection(connection_id)

            # 일일 사용량 제한 체크
            is_within_limit = await self._check_usage_limit(connection_id, db, user.id)
            if not is_within_limit:
                return  # 제한 초과 시 처리 중단

            content, conversation_id = await self._validate_message_data(connection_id, message_data)
            validated_conversation_id = await self._validate_or_create_session(db, user.id, conversation_id, content)

            # 응답 처리 (메시지 저장은 LLM 성공 후에만 수행)
            await self._send_message_acknowledgment(connection_id, validated_conversation_id)
            await self._process_llm_streaming_response(
                connection_id, content, validated_conversation_id, user.id, db
            )

        except Exception as e:
            await self._handle_message_error(connection_id, e)

    async def _validate_user_connection(self, connection_id: str) -> UserModel:
        """사용자 연결 상태 검증"""
        user = self.connection_users.get(connection_id)
        if not user:
            LOGGER.error(f"❌ User not found for connection {connection_id}")
            await self.send_to_connection(connection_id, {
                "type": "error",
                "error": "User not found",
                "timestamp": utc_now().isoformat()
            })
            raise ValueError(f"User not found for connection {connection_id}")
        return user

    async def _check_usage_limit(self, connection_id: str, db: AsyncSession, user_id: int) -> bool:
        """
        사용자의 일일 사용량 제한 확인
        Returns:
            True: 사용 가능
            False: 제한 초과
        """
        try:
            is_within_limit = await check_usage_limit(db, user_id)

            if not is_within_limit:
                # 사용량 정보 조회하여 상세 메시지 제공
                usage = await get_user_usage(db, user_id)
                LOGGER.warning(f"🚫 User {user_id} exceeded daily limit: {usage.daily_requests}/{usage.daily_limit}")

                await self.send_to_connection(connection_id, {
                    "type": "usage_limit_exceeded",
                    "error": "일일 사용량 제한을 초과했습니다.",
                    "daily_requests": usage.daily_requests,
                    "daily_limit": usage.daily_limit,
                    "remaining_requests": 0,
                    "timestamp": utc_now().isoformat()
                })
                return False

            return True

        except Exception as e:
            LOGGER.error(f"❌ Error checking usage limit for user {user_id}: {e}")
            # 제한 체크 실패 시 안전하게 허용 (서비스 중단 방지)
            return True

    async def _validate_message_data(self, connection_id: str, message_data: Dict[str, Any]) -> Tuple[str, Optional[int]]:
        """메시지 내용과 대화 ID 검증"""
        content = message_data.get("content", "").strip()
        conversation_id = message_data.get("conversation_id")

        if not content:
            LOGGER.warning(f"❌ Empty message content from {connection_id}")
            await self.send_to_connection(connection_id, {
                "type": "error",
                "error": "Message content is required",
                "timestamp": utc_now().isoformat()
            })
            raise ValueError("Message content is required")

        return content, conversation_id

    async def _validate_or_create_session(
        self,
        db: AsyncSession,
        user_id: int,
        conversation_id: Optional[int],
        content: str
    ) -> int:
        """매번 새로운 conversation 생성 (질문-응답 쌍별로)"""
        # 기존 세션 검증 로직 제거 - 항상 새 conversation 생성
        session_response = await get_or_create_session(
            db=db,
            user_id=user_id,
            content=content
        )
        LOGGER.info(f"✅ New conversation created for each question: conversation_id={session_response.id}")
        return session_response.id

    async def _send_message_acknowledgment(self, connection_id: str, conversation_id: int) -> None:
        """메시지 수신 확인 및 타이핑 상태 시작"""
        # 메시지 수신 확인
        await self.send_to_connection(connection_id, {
            "type": "message_received",
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "timestamp": utc_now().isoformat()
        })

        # 타이핑 상태 시작
        await self.send_to_connection(connection_id, {
            "type": "typing",
            "is_typing": True,
            "timestamp": utc_now().isoformat()
        })

    async def _process_llm_streaming_response(
        self,
        connection_id: str,
        content: str,
        conversation_id: int,
        user_id: int,
        db: AsyncSession
    ) -> None:
        """LLM 스트리밍 응답 처리"""
        # LLM 서비스 초기화 확인
        await self._ensure_llm_service()

        assistant_content = ""
        assistant_message_id = str(uuid.uuid4())
        chunk_count = 0
        has_error = False

        async for chunk in self.llm_service.generate_streaming_chat_response(
            user_message=content,
            conversation_id=conversation_id,
            user_id=user_id
        ):
            chunk_count += 1
            LOGGER.info(f"📦 Received chunk #{chunk_count}: type={chunk.get('type', 'unknown')}")

            chunk_type = chunk.get("type")
            if chunk_type == "start":
                await self._handle_start_chunk(connection_id, chunk, assistant_message_id, conversation_id)
            elif chunk_type == "content":
                assistant_content += await self._handle_content_chunk(connection_id, chunk, assistant_message_id, conversation_id)
            elif chunk_type == "final_result":
                await self._handle_final_result_chunk(connection_id, chunk, assistant_message_id, conversation_id)
            elif chunk_type == "end":
                await self._handle_end_chunk(connection_id, chunk, assistant_message_id, conversation_id, len(assistant_content))
            elif chunk_type == "error":
                has_error = True
                await self._handle_error_chunk(connection_id, chunk, assistant_message_id, conversation_id)
            elif chunk_type == "error_response":
                has_error = True
                await self._handle_error_response_chunk(connection_id, chunk, assistant_message_id, conversation_id)

        # 에러가 없었을 때만 사용자 메시지 저장
        print(f"(has_error: {has_error})")
        print(f"(has error type : {type(has_error)}")
        if not has_error:
            await self._save_user_message(db, conversation_id, user_id, content)
            print("(saved user message)")

    async def _handle_start_chunk(
        self,
        connection_id: str,
        chunk: Dict[str, Any],
        assistant_message_id: str,
        conversation_id: int
    ) -> None:
        """응답 시작 청크 처리"""
        await self.send_to_connection(connection_id, {
            "type": "response_start",
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "timestamp": chunk["timestamp"]
        })

    async def _handle_content_chunk(
        self,
        connection_id: str,
        chunk: Dict[str, Any],
        assistant_message_id: str,
        conversation_id: int
    ) -> str:
        """실시간 콘텐츠 청크 처리"""
        content = chunk["content"]
        chunk_data = {
            "type": "response_chunk",
            "content": content,
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "timestamp": chunk["timestamp"]
        }

        LOGGER.info(f"🟦 Sending response_chunk: content_length={len(content)}")
        try:
            await self.send_to_connection(connection_id, chunk_data)
            return content
        except Exception as e:
            LOGGER.error(f"❌ Error sending response_chunk: {e}")
            LOGGER.error(format_exc())
            raise

    async def _handle_final_result_chunk(
        self,
        connection_id: str,
        chunk: Dict[str, Any],
        assistant_message_id: str,
        conversation_id: int
    ) -> None:
        """최종 결과 청크 처리 (시각화 데이터 포함)"""
        final_content = chunk.get("content", "")
        final_message = {
            "type": "final_result",
            "content": final_content,
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "timestamp": chunk["timestamp"],
            # Frontend에서 사용하는 시각화 데이터
            "visualization_type": chunk.get("visualization_type"),
            "visualization_data": chunk.get("visualization_data"),
            "insights": chunk.get("insights", [])
        }

        LOGGER.info(f"🟦 Sending final_result: content_length={len(final_content)}")
        try:
            await self.send_to_connection(connection_id, final_message)
        except Exception as e:
            LOGGER.error(f"❌ Error sending final_result: {e}")
            LOGGER.error(format_exc())
            raise

        # Tool 결과 저장 (기존 로직 유지)
        if "intermediate_steps" in chunk:
            await self._process_tool_results(chunk["intermediate_steps"])

        # 최종 어시스턴트 메시지를 데이터베이스에 저장
        try:
            user = self.connection_users.get(connection_id)
            if user and final_content.strip():  # 빈 내용이 아닌 경우에만 저장
                from conversation.repositories import add_message_to_session
                from database.connection.postgres_conn import get_async_db

                async for db in get_async_db():
                    try:
                        saved_message = await add_message_to_session(
                            session=db,
                            conversation_id=conversation_id,
                            user_id=user.id,
                            content=final_content,
                            role="assistant"
                        )
                        if saved_message:
                            LOGGER.info(f"✅ Final assistant message saved to DB: {assistant_message_id}")
                        else:
                            LOGGER.warning(f"❌ Failed to save final assistant message: {assistant_message_id}")
                        break
                    except Exception as save_error:
                        LOGGER.error(f"❌ Error saving final message to DB: {save_error}")
                        LOGGER.error(format_exc())
            else:
                LOGGER.warning(f"⚠️ Skipping message save: user={bool(user)}, content_length={len(final_content.strip())}")
        except Exception as e:
            LOGGER.error(f"❌ Error in final message save process: {e}")
            LOGGER.error(format_exc())

    async def _handle_end_chunk(
        self,
        connection_id: str,
        chunk: Dict[str, Any],
        assistant_message_id: str,
        conversation_id: int,
        total_content_length: int
    ) -> None:
        """응답 종료 청크 처리"""
        # 타이핑 상태 종료
        await self.send_to_connection(connection_id, {
            "type": "typing",
            "is_typing": False,
            "timestamp": utc_now().isoformat()
        })

        # 응답 종료 알림
        await self.send_to_connection(connection_id, {
            "type": "response_end",
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "timestamp": chunk["timestamp"]
        })

    async def _handle_error_chunk(
        self,
        connection_id: str,
        chunk: Dict[str, Any],
        assistant_message_id: str,
        conversation_id: int
    ) -> None:
        """에러 청크 처리"""
        # 타이핑 상태 종료
        await self.send_to_connection(connection_id, {
            "type": "typing",
            "is_typing": False,
            "timestamp": utc_now().isoformat()
        })

        # 에러 메시지 전송
        await self.send_to_connection(connection_id, {
            "type": "error",
            "error": chunk["error"],
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "timestamp": chunk["timestamp"]
        })

    async def _handle_error_response_chunk(
        self,
        connection_id: str,
        chunk: Dict[str, Any],
        assistant_message_id: str,
        conversation_id: int
    ) -> None:
        """구조화된 에러 응답 청크 처리 (LLMException 기반)"""
        # 타이핑 상태 종료
        await self.send_to_connection(connection_id, {
            "type": "typing",
            "is_typing": False,
            "timestamp": utc_now().isoformat()
        })

        # 구조화된 에러 응답 전송 (프론트엔드가 기대하는 형식)
        await self.send_to_connection(connection_id, {
            "type": "error_response",
            "error": chunk["error"],
            "error_class": chunk["error_class"],
            "traceback": chunk["traceback"],
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "timestamp": chunk["timestamp"]
        })

    async def _process_tool_results(self, intermediate_steps: List[Any]) -> None:
        """Tool 실행 결과 처리"""
        if not intermediate_steps:
            return

        tool_info = []
        for i, step in enumerate(intermediate_steps):
            if len(step) >= 2:
                action, result = step
                processed_result = self._process_tool_result(result)

                tool_info.append({
                    "tool": getattr(action, 'tool', 'unknown'),
                    "input": getattr(action, 'tool_input', {}),
                    "result": processed_result
                })

    async def _save_user_message(self, db: AsyncSession, conversation_id: int, user_id: int, content: str) -> None:
        """사용자 메시지를 데이터베이스에 즉시 저장"""
        try:
            from conversation.repositories import add_message_to_session

            saved_message = await add_message_to_session(
                session=db,
                conversation_id=conversation_id,
                user_id=user_id,
                content=content,
                role="user"
            )

            if saved_message:
                LOGGER.info(f"✅ User message saved to DB: conversation_id={conversation_id}")
            else:
                LOGGER.warning(f"❌ Failed to save user message: conversation_id={conversation_id}")

        except Exception as e:
            LOGGER.error(f"❌ Error saving user message to DB: {e}")
            LOGGER.error(format_exc())
            # 사용자 메시지 저장 실패는 치명적이지 않으므로 예외를 다시 발생시키지 않음

    async def _handle_message_error(self, connection_id: str, error: Exception) -> None:
        """메시지 처리 에러 핸들링"""
        LOGGER.error(f"❌ Error handling user message: {error}")
        LOGGER.error(format_exc())

        await self.send_to_connection(connection_id, {
            "type": "error",
            "error": f"Failed to process message: {str(error)}",
            "timestamp": utc_now().isoformat()
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
            "total_conversations": len(self.conversation_connections),
            "timestamp": utc_now().isoformat()
        }


# 글로벌 연결 관리자 인스턴스
connection_manager = ConnectionManager()