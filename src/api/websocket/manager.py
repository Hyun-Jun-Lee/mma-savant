"""
WebSocket 연결 관리자
실시간 채팅을 위한 WebSocket 연결 및 메시지 처리
"""
import json
import uuid
import asyncio
from typing import Dict, Optional, Set, Any
from traceback import format_exc

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from user.models import UserModel
from user.services import check_usage_limit, get_user_usage, update_user_usage
from conversation.services import get_or_create_session
from conversation.repositories import (
    get_recent_messages, add_message_direct,
    get_conversation_compression, get_messages_after,
    get_message_count_after, update_conversation_compression,
)
from llm.service import get_graph_service, MMAGraphService
from common.logging_config import get_logger
from common.utils import utc_now

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
        
        # LLM 서비스 (StateGraph 기반)
        self.llm_service: MMAGraphService = None
        self._initializing = False

    async def _ensure_llm_service(self):
        """LLM 서비스 초기화 보장"""
        if self.llm_service is not None:
            return

        if self._initializing:
            while self._initializing:
                await asyncio.sleep(0.1)
            return

        self._initializing = True
        try:
            self.llm_service = await get_graph_service()
            LOGGER.info("✅ MMA Graph service initialized")
        finally:
            self._initializing = False

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
        - conversation_id 없음: 새 대화 → LLM 성공 후 세션 생성 + 메시지 저장
        - conversation_id 있음: 기존 대화 → 히스토리 로드 후 LLM 처리 + 기존 세션에 저장
        """
        try:
            user = await self._validate_user_connection(connection_id)

            is_within_limit = await self._check_usage_limit(connection_id, db, user.id)
            if not is_within_limit:
                return

            content = await self._validate_message_data(connection_id, message_data)
            conversation_id = message_data.get("conversation_id")

            await self._send_typing_indicator(connection_id)
            await self._process_llm_streaming_response(
                connection_id, content, user.id, db, conversation_id
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

    async def _validate_message_data(self, connection_id: str, message_data: Dict[str, Any]) -> str:
        """메시지 내용 검증"""
        content = message_data.get("content", "").strip()

        if not content:
            LOGGER.warning(f"❌ Empty message content from {connection_id}")
            await self.send_to_connection(connection_id, {
                "type": "error",
                "error": "Message content is required",
                "timestamp": utc_now().isoformat()
            })
            raise ValueError("Message content is required")

        return content

    async def _send_typing_indicator(self, connection_id: str) -> None:
        """타이핑 상태 시작"""
        await self.send_to_connection(connection_id, {
            "type": "typing",
            "is_typing": True,
            "timestamp": utc_now().isoformat()
        })

    async def _load_chat_history(
        self, db: AsyncSession, conversation_id: int, user_id: int
    ) -> dict:
        """기존 대화의 히스토리를 DB에서 로드 (압축 데이터 포함).

        Returns:
            {"messages": list, "compressed_context": str|None, "compressed_sql_context": list|None}
        """
        try:
            compression = await get_conversation_compression(db, conversation_id)

            if compression and compression["compressed_until_message_id"]:
                messages = await get_messages_after(
                    db, conversation_id, compression["compressed_until_message_id"],
                )
                LOGGER.info(
                    f"📜 Loaded {len(messages)} messages after compression boundary "
                    f"for conversation {conversation_id}"
                )
                return {
                    "messages": [msg.to_response() for msg in messages],
                    "compressed_context": compression["compressed_context"],
                    "compressed_sql_context": compression["compressed_sql_context"],
                }
            else:
                messages = await get_recent_messages(
                    session=db, conversation_id=conversation_id, limit=10,
                )
                LOGGER.info(
                    f"📜 Loaded {len(messages)} recent messages "
                    f"for conversation {conversation_id}"
                )
                return {
                    "messages": [msg.to_response() for msg in messages] if messages else [],
                    "compressed_context": None,
                    "compressed_sql_context": None,
                }
        except Exception as e:
            LOGGER.error(f"❌ Failed to load chat history: {e}")
            return {"messages": [], "compressed_context": None, "compressed_sql_context": None}

    async def _process_llm_streaming_response(
        self,
        connection_id: str,
        content: str,
        user_id: int,
        db: AsyncSession,
        conversation_id: Optional[int] = None,
    ) -> None:
        """
        LLM 스트리밍 응답 처리
        - conversation_id 없음: 새 대화 → LLM 성공 후 세션 생성 + 저장
        - conversation_id 있음: 기존 대화 → 히스토리 로드 + 기존 세션에 저장
        """
        await self._ensure_llm_service()

        assistant_message_id = str(uuid.uuid4())
        has_error = False
        final_result_chunk = None

        # 기존 대화인 경우 히스토리 로드
        chat_history_data = {"messages": [], "compressed_context": None, "compressed_sql_context": None}
        if conversation_id:
            chat_history_data = await self._load_chat_history(db, conversation_id, user_id)

        async for chunk in self.llm_service.generate_streaming_chat_response(
            user_message=content,
            conversation_id=conversation_id or 0,
            user_id=user_id,
            chat_history=chat_history_data["messages"],
            compressed_context=chat_history_data["compressed_context"],
            compressed_sql_context=chat_history_data["compressed_sql_context"],
        ):
            chunk_type = chunk.get("type")

            if chunk_type == "final_result":
                final_result_chunk = chunk
            elif chunk_type in ("error", "error_response"):
                has_error = True
                if chunk_type == "error":
                    await self._handle_error_chunk(
                        connection_id, chunk, assistant_message_id, conversation_id or 0
                    )
                else:
                    await self._handle_error_response_chunk(
                        connection_id, chunk, assistant_message_id, conversation_id or 0
                    )

        if not has_error and final_result_chunk:
            conversation_id = await self._save_successful_conversation(
                db, user_id, content, final_result_chunk, connection_id,
                existing_conversation_id=conversation_id,
            )

            # 그래프 완료 후 압축 (비동기, 실패 무시)
            await self._maybe_compress_conversation(db, conversation_id)

            await self._send_final_result(
                connection_id, final_result_chunk, assistant_message_id, conversation_id
            )

            await self.send_to_connection(connection_id, {
                "type": "typing",
                "is_typing": False,
                "timestamp": utc_now().isoformat()
            })
            await self.send_to_connection(connection_id, {
                "type": "response_end",
                "message_id": assistant_message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat()
            })

    async def _send_final_result(
        self,
        connection_id: str,
        chunk: Dict[str, Any],
        assistant_message_id: str,
        conversation_id: int
    ) -> None:
        """최종 결과를 프론트엔드에 전송 (DB 저장 없음 — 호출자가 처리)"""
        final_content = chunk.get("content", "")
        final_message = {
            "type": "final_result",
            "content": final_content,
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "timestamp": chunk["timestamp"],
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

    async def _save_successful_conversation(
        self,
        db: AsyncSession,
        user_id: int,
        user_content: str,
        final_result_chunk: Dict[str, Any],
        connection_id: str,
        existing_conversation_id: Optional[int] = None,
    ) -> int:
        """
        LLM 성공 후 메시지 저장.
        - existing_conversation_id 없음: 새 세션 생성 후 저장
        - existing_conversation_id 있음: 기존 세션에 메시지 추가
        Returns: conversation_id
        """
        if existing_conversation_id:
            conversation_id = existing_conversation_id
            LOGGER.info(f"📝 Appending to existing conversation: {conversation_id}")
        else:
            session_response = await get_or_create_session(
                db=db, user_id=user_id, content=user_content
            )
            conversation_id = session_response.id
            LOGGER.info(f"✅ Conversation created after LLM success: conversation_id={conversation_id}")

        # 사용자 메시지 저장
        await self._save_user_message(db, conversation_id, user_id, user_content)

        # 어시스턴트 메시지 저장
        final_response = final_result_chunk.get("final_response", "")
        viz_type = final_result_chunk.get("visualization_type")
        viz_data = final_result_chunk.get("visualization_data")

        # DB 저장용: final_response에 SQL 데이터가 포함되어 후속 질문의 맥락 제공
        save_content = final_response.strip() or ""

        # content 또는 시각화 데이터가 있으면 저장 (둘 다 없으면 스킵)
        if save_content or (viz_type and viz_data):
            # SQL 에이전트 결과 → tool_results (히스토리 컨텍스트용)
            tool_results = final_result_chunk.get("agent_results") or None

            # 시각화 메타데이터 → visualization (프론트엔드 차트용)
            visualization = None
            if viz_type and viz_data:
                visualization = [{
                    "visualization_type": viz_type,
                    "visualization_data": viz_data,
                    "insights": final_result_chunk.get("insights", []),
                }]

            try:
                saved = await add_message_direct(
                    session=db,
                    conversation_id=conversation_id,
                    content=save_content,
                    role="assistant",
                    tool_results=tool_results,
                    visualization=visualization,
                )
                LOGGER.info(f"✅ Assistant message saved to DB: conversation_id={conversation_id}")
            except Exception as e:
                LOGGER.error(f"❌ Error saving assistant message: {e}")
                LOGGER.error(format_exc())

        # 사용량 증가 (LLM 성공 시 1회 차감)
        try:
            from user.dto import UserUsageUpdateDTO
            await update_user_usage(db, UserUsageUpdateDTO(
                user_id=user_id, increment_requests=1,
            ))
            LOGGER.info(f"📊 Usage incremented for user {user_id}")
        except Exception as e:
            LOGGER.error(f"❌ Failed to increment usage for user {user_id}: {e}")

        # 모든 작업 성공 후 단일 commit (트랜잭션 원자성 보장)
        await db.commit()

        return conversation_id

    COMPRESS_THRESHOLD = 10  # 압축 트리거 메시지 수

    async def _maybe_compress_conversation(
        self, db: AsyncSession, conversation_id: int,
    ) -> None:
        """그래프 완료 후 대화 압축 실행 (필요 시).

        - boundary 이후 메시지 수 <= COMPRESS_THRESHOLD → 스킵
        - 압축 대상 메시지 분리 → LLM 압축 → DB 저장
        - 실패 시 로그만 남기고 다음 턴에 재시도
        """
        try:
            compression = await get_conversation_compression(db, conversation_id)

            existing_boundary = (
                compression["compressed_until_message_id"] if compression else None
            )
            existing_summary = (
                compression["compressed_context"] if compression else None
            )
            existing_sql_ctx = (
                compression["compressed_sql_context"] if compression else None
            )

            msg_count = await get_message_count_after(
                db, conversation_id, existing_boundary,
            )
            if msg_count <= self.COMPRESS_THRESHOLD:
                return

            # boundary 이후 모든 메시지 로드
            if existing_boundary:
                all_messages = await get_messages_after(db, conversation_id, existing_boundary)
            else:
                all_messages = await get_recent_messages(db, conversation_id, limit=100)

            if len(all_messages) <= self.COMPRESS_THRESHOLD:
                return

            # older (압축 대상) / recent (유지) 분리
            split_idx = len(all_messages) - self.COMPRESS_THRESHOLD
            older = all_messages[:split_idx]
            new_boundary_msg = older[-1]  # 마지막 압축 대상 메시지

            # older에서 sql_context 추출
            new_sql_entries = []
            older_as_dicts = []
            for msg in older:
                older_as_dicts.append({"role": msg.role, "content": msg.content})
                if msg.role == "assistant" and msg.tool_results:
                    new_sql_entries.extend(msg.tool_results)

            # 기존 compressed_sql_context와 병합 (최대 10개)
            merged_sql_ctx = (existing_sql_ctx or []) + new_sql_entries
            merged_sql_ctx = merged_sql_ctx[-10:]

            # LLM 압축 호출
            new_summary = await self.llm_service.compress_conversation(
                messages_to_compress=older_as_dicts,
                existing_summary=existing_summary,
                sql_context=merged_sql_ctx,
            )

            if new_summary is None:
                LOGGER.warning(f"⚠️ Compression skipped for conversation {conversation_id}")
                return

            # DB 저장
            await update_conversation_compression(
                session=db,
                conversation_id=conversation_id,
                compressed_context=new_summary,
                compressed_sql_context=merged_sql_ctx if merged_sql_ctx else None,
                compressed_until_message_id=new_boundary_msg.message_id,
            )
            await db.commit()
            LOGGER.info(
                f"✅ Conversation {conversation_id} compressed: "
                f"{len(older)} msgs → summary, boundary={new_boundary_msg.message_id}"
            )

        except Exception as e:
            LOGGER.warning(f"⚠️ Compression error for conversation {conversation_id}: {e}")

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

    async def _save_user_message(self, db: AsyncSession, conversation_id: int, user_id: int, content: str) -> None:
        """사용자 메시지를 데이터베이스에 즉시 저장"""
        try:
            saved_message = await add_message_direct(
                session=db,
                conversation_id=conversation_id,
                content=content,
                role="user",
            )
            LOGGER.info(f"✅ User message saved to DB: conversation_id={conversation_id}")

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