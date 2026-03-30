"""
message_manager.py 테스트 코드
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from conversation.message_manager import ChatHistory


class MockAsyncDBSession:
    """Mock DB 세션"""
    
    def __init__(self):
        self.closed = False
        self.committed = False
        self.rollbacked = False
        self._mock_results = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.closed = True
    
    async def commit(self):
        self.committed = True
    
    async def rollback(self):
        self.rollbacked = True
    
    async def execute(self, query):
        """Mock execute 메서드"""
        # Mock 결과 객체 반환
        return MockResult(self._mock_results)
    
    def add(self, obj):
        """Mock add 메서드"""
        pass
    
    async def flush(self):
        """Mock flush 메서드"""
        pass


class MockResult:
    """Mock 쿼리 결과"""
    
    def __init__(self, results):
        self.results = results
    
    def scalars(self):
        """Mock scalars 메서드"""
        return MockScalars(self.results)
    
    def scalar(self):
        """Mock scalar 메서드"""
        return self.results[0] if self.results else None
    
    def scalar_one_or_none(self):
        """Mock scalar_one_or_none 메서드"""
        return self.results[0] if self.results else None


class MockScalars:
    """Mock scalars 객체"""
    
    def __init__(self, results):
        self.results = results
    
    def all(self):
        """Mock all 메서드"""
        return self.results


class MockAsyncDBSessionFactory:
    """Mock DB 세션 팩토리"""
    
    def __init__(self):
        self.sessions = []
    
    def __call__(self):
        """Context manager를 반환하는 팩토리"""
        return MockAsyncDBSessionContext(self)


class MockAsyncDBSessionContext:
    """Mock DB 세션 컨텍스트 매니저"""
    
    def __init__(self, factory):
        self.factory = factory
        self.session = None
    
    async def __aenter__(self):
        self.session = MockAsyncDBSession()
        self.factory.sessions.append(self.session)
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.closed = True


@pytest.fixture
def mock_db_session_factory():
    """Mock DB 세션 팩토리 픽스처"""
    return MockAsyncDBSessionFactory()


@pytest.fixture
def mock_recent_messages():
    """Mock MessageModel 리스트 (get_recent_messages 반환값)"""

    class MockMessageModel:
        def __init__(self, role, content, tool_results=None):
            self.role = role
            self.content = content
            self.tool_results = tool_results

    return [
        MockMessageModel(role="user", content="Hello"),
        MockMessageModel(role="assistant", content="Hi there!"),
    ]


class TestChatHistory:
    """ChatHistory 클래스 테스트"""
    
    @pytest.mark.asyncio
    async def test_init_basic_properties(self, mock_db_session_factory):
        """초기화 시 기본 속성들이 설정되는지 테스트"""
        chat_history = ChatHistory(
            conversation_id=123,
            user_id=1,
            async_db_session_factory=mock_db_session_factory,
            max_cache_size=5
        )

        assert chat_history.conversation_id == 123
        assert chat_history.user_id == 1
        assert chat_history.max_cache_size == 5
        assert not chat_history._loaded

        # 리소스 정리
        await chat_history.close()
    
    @pytest.mark.asyncio
    async def test_add_message_to_memory_cache(self, mock_db_session_factory):
        """메시지가 메모리 캐시에 추가되는지 테스트"""
        chat_history = ChatHistory(
            conversation_id=123,
            user_id=1,
            async_db_session_factory=mock_db_session_factory,
            max_cache_size=5
        )

        # 메시지 추가
        user_msg = HumanMessage(content="Hello")
        ai_msg = AIMessage(content="Hi there!")

        chat_history.add_message(user_msg)
        chat_history.add_message(ai_msg)

        # 메모리 캐시 확인
        messages = chat_history.messages
        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"
        assert isinstance(messages[0], HumanMessage)
        assert isinstance(messages[1], AIMessage)
    
    @pytest.mark.asyncio
    async def test_cache_size_limit_lru(self, mock_db_session_factory):
        """캐시 크기 제한 및 LRU 동작 테스트"""
        chat_history = ChatHistory(
            conversation_id=123,
            user_id=1,
            async_db_session_factory=mock_db_session_factory,
            max_cache_size=3  # 최대 3개 메시지
        )

        # 5개 메시지 추가 (3개 초과)
        for i in range(5):
            msg = HumanMessage(content=f"Message {i}")
            chat_history.add_message(msg)

        # 최신 3개만 남아있어야 함
        messages = chat_history.messages
        assert len(messages) == 3
        assert messages[0].content == "Message 2"  # 가장 오래된 것
        assert messages[1].content == "Message 3"
        assert messages[2].content == "Message 4"  # 가장 최신
    
    @pytest.mark.asyncio
    async def test_add_message_with_tool_results(self, mock_db_session_factory):
        """툴 결과가 있는 AI 메시지 추가 테스트"""
        chat_history = ChatHistory(
            conversation_id=123,
            user_id=1,
            async_db_session_factory=mock_db_session_factory,
            max_cache_size=5
        )

        # 툴 결과가 있는 AI 메시지
        ai_msg = AIMessage(
            content="I used a tool",
            additional_kwargs={"tool_results": [{"tool": "search", "result": "found"}]}
        )

        chat_history.add_message(ai_msg)

        # 메모리 캐시 확인
        messages = chat_history.messages
        assert len(messages) == 1
        assert messages[0].content == "I used a tool"
        assert messages[0].additional_kwargs["tool_results"] == [{"tool": "search", "result": "found"}]
    
    
    @pytest.mark.asyncio
    async def test_load_from_db(self, mock_db_session_factory, mock_recent_messages):
        """DB에서 메시지 로드 테스트"""
        with patch('conversation.message_manager.get_recent_messages') as mock_get:
            mock_get.return_value = mock_recent_messages

            chat_history = ChatHistory(
                conversation_id=123,
                user_id=1,
                async_db_session_factory=mock_db_session_factory,
                max_cache_size=5
            )

            # DB에서 로드
            await chat_history._ensure_loaded()

            # 로드된 메시지 확인
            messages = chat_history.messages
            assert len(messages) == 2
            assert messages[0].content == "Hello"
            assert messages[1].content == "Hi there!"
            assert isinstance(messages[0], HumanMessage)
            assert isinstance(messages[1], AIMessage)
            assert chat_history._loaded is True

            # get_recent_messages가 호출되었는지 확인
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args.kwargs["conversation_id"] == 123
            assert call_args.kwargs["limit"] == 5
    
    @pytest.mark.asyncio
    async def test_clear_messages(self, mock_db_session_factory):
        """메시지 클리어 테스트"""
        chat_history = ChatHistory(
            conversation_id=123,
            user_id=1,
            async_db_session_factory=mock_db_session_factory,
            max_cache_size=5
        )

        # 메시지 추가
        chat_history.add_message(HumanMessage(content="Hello"))
        chat_history.add_message(AIMessage(content="Hi there!"))

        # 클리어 전 확인
        assert len(chat_history.messages) == 2

        # 클리어 실행
        chat_history.clear()

        # 클리어 후 확인
        assert len(chat_history.messages) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])