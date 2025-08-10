import asyncio
from typing import List, Dict, Optional
from traceback import format_exc

from common.logging_config import get_logger
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from conversation.repositories import add_message_to_session, get_chat_history


LOGGER = get_logger(__name__)


class ChatHistory(BaseChatMessageHistory):
    """채팅 히스토리"""
    
    def __init__(self, session_id: str, user_id: int, async_db_session_factory, max_cache_size: int = 100):
        self.session_id = session_id
        self.user_id = user_id
        self.async_db_session_factory = async_db_session_factory
        self.max_cache_size = max_cache_size  # 메모리 캐시 최대 메시지 개수
        
        # 메모리 캐시
        self._messages_cache: List[BaseMessage] = []
        self._loaded = False
        
        # 백그라운드 저장 큐
        self._save_queue = asyncio.Queue()
        self._save_task = None
        self._start_background_message_save()
    
    def _start_background_message_save(self):
        """백그라운드 DB 저장 태스크 시작"""
        if self._save_task is None or self._save_task.done():
            self._save_task = asyncio.create_task(self._background_message_saver())
    
    async def _background_message_saver(self):
        """백그라운드에서 DB 저장 처리"""
        while True:
            try:
                save_item = await self._save_queue.get()
                if save_item is None:
                    break
                
                async with self.async_db_session_factory() as session:
                    if save_item["action"] == "add":
                        message_data = save_item["message"]
                        
                        # Repository 함수 사용 (권한 확인 포함)
                        saved_message = await add_message_to_session(
                            session=session,
                            session_id=self.session_id,
                            user_id=self.user_id,
                            content=message_data["content"],
                            role=message_data["role"],
                            tool_results=message_data.get("tool_results")
                        )
                        
                        if not saved_message:
                            LOGGER.warning(f"❌ Failed to save message: session not found or permission denied")
                self._save_queue.task_done()
                
            except Exception as e:
                LOGGER.error(f"❌ Background save error: {e}")
                LOGGER.error(format_exc())
                continue
    
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
    
    def add_message(self, message: BaseMessage) -> None:
        """메시지 추가 (메모리 즉시 + DB 백그라운드)"""
        # 1. 메모리 캐시에 즉시 추가
        self._messages_cache.append(message)
        
        # 2. 캐시 크기 제한 (LRU: 가장 오래된 메시지 제거)
        if len(self._messages_cache) > self.max_cache_size:
            removed_count = len(self._messages_cache) - self.max_cache_size
            self._messages_cache = self._messages_cache[-self.max_cache_size:]
            LOGGER.debug(f"Cache size exceeded, removed {removed_count} oldest messages")
        
        # 3. DB 저장을 백그라운드 큐에 추가
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        tool_results = None
        
        if isinstance(message, AIMessage) and hasattr(message, 'additional_kwargs'):
            tool_results = message.additional_kwargs.get("tool_results")
        
        save_item = {
            "action": "add",
            "message": {
                "content": message.content,
                "role": role,
                "tool_results": tool_results
            }
        }
        
        try:
            self._save_queue.put_nowait(save_item)
        except asyncio.QueueFull:
            LOGGER.warning("⚠️ Save queue is full, skipping DB save")
    
    
    async def _load_from_db(self) -> List[BaseMessage]:
        """Repository를 통한 DB 로드"""
        try:
            
            async with self.async_db_session_factory() as session:
                # Repository 함수 사용 (권한 확인 포함)
                history = await get_chat_history(
                    session=session,
                    session_id=self.session_id,
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
        """히스토리 클리어"""
        self._messages_cache = []
        
        # DB 클리어를 백그라운드 큐에 추가
        clear_item = {"action": "clear", "message": None}
        try:
            self._save_queue.put_nowait(clear_item)
        except asyncio.QueueFull:
            LOGGER.warning("⚠️ Save queue is full, skipping DB clear")
    
    async def close(self):
        """리소스 정리"""
        # 모든 대기 중인 저장 작업 완료
        await self._save_queue.join()
        
        # 백그라운드 태스크 종료
        if self._save_task and not self._save_task.done():
            await self._save_queue.put(None)
            await self._save_task


class ChatHistoryManager:
    """채팅 히스토리 매니저"""
    
    def __init__(self, async_db_session_factory=None, max_cache_size: int = 10):
        self.async_db_session_factory = async_db_session_factory
        self.max_cache_size = max_cache_size
        self._active_histories: Dict[str, ChatHistory] = {}
    
    async def get_session_history(self, session_id: str, user_id: int) -> ChatHistory:
        """세션별 하이브리드 히스토리 반환"""
        if session_id not in self._active_histories:
            history = ChatHistory(
                session_id=session_id,
                user_id=user_id,
                async_db_session_factory=self.async_db_session_factory,
                max_cache_size=self.max_cache_size
            )
            
            # 초기 로드
            await history._ensure_loaded()
            
            self._active_histories[session_id] = history
        
        return self._active_histories[session_id]
    
    async def cleanup_session(self, session_id: str):
        """특정 세션 정리"""
        if session_id in self._active_histories:
            await self._active_histories[session_id].close()
            del self._active_histories[session_id]
    
    async def cleanup_all(self):
        """모든 세션 정리"""
        for history in self._active_histories.values():
            await history.close()
        self._active_histories.clear()
