import asyncio
from typing import List, Dict, Optional
from traceback import format_exc

from common.logging_config import get_logger
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from conversation.repositories import add_message_to_session, get_chat_history


LOGGER = get_logger(__name__)


class ChatHistory(BaseChatMessageHistory):
    """채팅 히스토리"""
    
    def __init__(self, conversation_id : int, user_id: int, async_db_session_factory, max_cache_size: int = 5):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.async_db_session_factory = async_db_session_factory
        self.max_cache_size = max_cache_size  # 새 구조에서는 최대 2-3개 메시지만 필요

        # 메모리 캐시 (단순화)
        self._messages_cache: List[BaseMessage] = []
        self._loaded = False

        # 백그라운드 저장 큐 제거 - 즉시 저장으로 변경
    
    async def _ensure_loaded(self):
        """메시지가 로드되지 않았다면 DB에서 로드"""
        if self._loaded:
            return
        
        try:
            # DB에서 로드
            self._messages_cache = await self._load_from_db()
            LOGGER.info(f"✅ Loaded {len(self._messages_cache)} messages from DB")
            self._loaded = True
            
        except Exception as e:
            LOGGER.error(f"❌ Error loading messages: {e}")
            LOGGER.error(format_exc())
            self._messages_cache = []
            self._loaded = True
    
    @property
    def messages(self) -> List[BaseMessage]:
        """동기적으로 메시지 반환 (LangChain 인터페이스 요구사항)"""
        return self._messages_cache
    
    def add_message(self, message) -> None:
        """메시지 추가 (메모리 즉시 + DB 백그라운드) - 타입 안전"""
        # 타입 검증 및 변환
        if isinstance(message, BaseMessage):
            final_message = message
        elif isinstance(message, dict):
            print("⚠️ Dict detected - converting to BaseMessage")
            final_message = self._convert_dict_to_message(message)
            if final_message is None:
                print("❌ Conversion failed - skipping")
                return
        else:
            print(f"❌ Invalid type {type(message)} - skipping")
            return
        
        # 1. 메모리 캐시에 즉시 추가
        self._messages_cache.append(final_message)
        
        # 2. 캐시 크기 제한 (LRU: 가장 오래된 메시지 제거)
        if len(self._messages_cache) > self.max_cache_size:
            removed_count = len(self._messages_cache) - self.max_cache_size
            self._messages_cache = self._messages_cache[-self.max_cache_size:]
            LOGGER.debug(f"Cache size exceeded, removed {removed_count} oldest messages")
        
        # 3. 새 구조에서는 WebSocket에서 직접 저장하므로 여기서는 로깅만
        role = "user" if isinstance(final_message, HumanMessage) else "assistant"

        # ToolMessage는 DB에 저장하지 않음 (중간 과정이므로)
        if isinstance(final_message, ToolMessage):
            print("📋 ToolMessage detected - adding to cache only")
            return

        print(f"✅ Message added to cache: {role} (DB save handled by WebSocket)")

    def _convert_dict_to_message(self, message_dict: dict):
        """딕셔너리를 BaseMessage로 변환"""
        try:
            if "role" in message_dict and "content" in message_dict:
                role = message_dict["role"]
                content = message_dict["content"]
                if role == "user":
                    return HumanMessage(content=content)
                else:
                    return AIMessage(content=content)
            elif "text" in message_dict:
                return AIMessage(content=message_dict["text"])
            elif "output" in message_dict:
                return AIMessage(content=str(message_dict["output"]))
            elif "content" in message_dict:
                return AIMessage(content=message_dict["content"])
            else:
                print(f"❌ Cannot convert dict: {message_dict}")
                return None
        except Exception as e:
            print(f"❌ Error converting dict: {e}")
            return None
    
    async def _load_from_db(self) -> List[BaseMessage]:
        """Repository를 통한 DB 로드"""
        try:
            
            async with self.async_db_session_factory() as session:
                # Repository 함수 사용 (권한 확인 포함)
                history = await get_chat_history(
                    session=session,
                    conversation_id=self.conversation_id,
                    user_id=self.user_id,
                    limit=self.max_cache_size  # 캐시 크기만큼만 로드
                )
                
                if not history:
                    return []
                
                # 메시지를 LangChain 형식으로 변환
                langchain_messages = []
                for msg in history.messages:
                    if msg.role == "user":
                        langchain_messages.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        additional_kwargs = {}
                        if msg.tool_results:
                            additional_kwargs["tool_results"] = msg.tool_results
                        langchain_messages.append(AIMessage(
                            content=msg.content,
                            additional_kwargs=additional_kwargs
                        ))
                
                return langchain_messages
                
        except Exception as e:
            LOGGER.error(f"❌ DB load error: {e}")
            LOGGER.error(format_exc())
            return []

    
    def clear(self) -> None:
        """히스토리 클리어 (단순화)"""
        self._messages_cache = []
        print("🧹 Chat history cache cleared")

    async def close(self):
        """리소스 정리 (단순화)"""
        # 새 구조에서는 백그라운드 태스크가 없으므로 캐시만 정리
        self.clear()
        print("🔐 ChatHistory closed")


# ChatHistoryManager 클래스 제거됨 - 매번 새 conversation 생성으로 더 이상 필요 없음
