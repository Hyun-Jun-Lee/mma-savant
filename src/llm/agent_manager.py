"""
LangChain 에이전트 생성 및 관리
MCP 도구 로딩, 캐싱, 에이전트 설정을 담당
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llm.prompts.en_ver import get_en_system_prompt_with_tools
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


class AgentManager:
    """
    LangChain 에이전트 생성 및 관리 클래스
    MCP 도구 캐싱과 에이전트 설정을 담당
    """
    
    def __init__(self, mcp_server_path: Optional[str] = None):
        """
        에이전트 매니저 초기화
        
        Args:
            mcp_server_path: MCP 서버 경로 (None이면 기본 경로 사용)
        """
        # MCP 서버 경로 설정
        if mcp_server_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(current_dir)
            mcp_server_path = os.path.join(src_dir, "tools", "mcp_server.py")
        
        self.mcp_server_path = mcp_server_path
        self.server_params = StdioServerParameters(
            command="python",
            args=[mcp_server_path],
        )
        
        # 도구 캐싱
        self._cached_tools = None
        self._tools_loading = False
        self._cache_valid = False
        
        LOGGER.info(f"🎯 AgentManager initialized with MCP server: {mcp_server_path}")
    
    @asynccontextmanager
    async def get_mcp_tools(self):
        """
        MCP 도구들을 context manager로 제공
        세션을 유지하면서 도구에 접근할 수 있도록 함
        
        Yields:
            List: MCP 도구 리스트
        """
        LOGGER.debug("🔄 Loading MCP tools...")
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                try:
                    # 연결 초기화
                    await session.initialize()
                    
                    # 도구 로드
                    tools = await load_mcp_tools(session)
                    LOGGER.info(f"✅ MCP Tools loaded: {len(tools)} tools")
                    
                    yield tools
                    
                except Exception as e:
                    LOGGER.error(f"❌ Error loading MCP tools: {e}")
                    raise
    
    async def load_and_cache_mcp_tools(self) -> List[Any]:
        """
        MCP 도구를 로드하고 캐싱
        
        Returns:
            List: 로드된 도구 리스트
            
        Note:
            현재는 context manager 패턴을 사용하므로 실제 캐싱은 제한적
            향후 세션 재사용 패턴 구현 시 활용 가능
        """
        if self._tools_loading:
            # 로딩 중인 경우 대기
            max_wait = 30  # 30초 최대 대기
            wait_count = 0
            while self._tools_loading and wait_count < max_wait:
                await asyncio.sleep(1)
                wait_count += 1
            
            if self._tools_loading:
                raise TimeoutError("MCP tools loading timeout")
        
        if self._cached_tools and self._cache_valid:
            LOGGER.debug("📦 Using cached MCP tools")
            return self._cached_tools
        
        self._tools_loading = True
        try:
            # 실제로는 context manager를 사용해야 하므로
            # 여기서는 도구 정보만 반환하고 실제 사용은 get_mcp_tools() 사용
            LOGGER.info("⚠️ MCP tools require context manager - use get_mcp_tools() instead")
            return []
        finally:
            self._tools_loading = False
    
    def get_cached_tools(self) -> Optional[List[Any]]:
        """
        캐시된 도구 반환
        
        Returns:
            Optional[List]: 캐시된 도구 리스트 (없으면 None)
        """
        if self._cached_tools and self._cache_valid:
            return self._cached_tools
        return None
    
    def clear_tools_cache(self):
        """도구 캐시 클리어"""
        self._cached_tools = None
        self._cache_valid = False
        LOGGER.info("🗑️ MCP tools cache cleared")
    
    def create_agent_with_tools(
        self, 
        llm: Any, 
        tools: List[Any], 
        chat_history: Optional[List[BaseMessage]] = None
    ) -> Any:
        """
        도구와 함께 에이전트 생성
        
        Args:
            llm: LangChain LLM 인스턴스
            tools: 도구 리스트
            chat_history: 채팅 히스토리 (검증됨)
            
        Returns:
            Agent: 생성된 에이전트
        """
        try:
            # 프롬프트 템플릿 생성
            prompt = self.get_chat_prompt_template()
            
            # 에이전트 생성
            agent = create_tool_calling_agent(llm, tools, prompt)
            
            LOGGER.info(f"🤖 Agent created successfully with {len(tools)} tools")
            return agent
            
        except Exception as e:
            LOGGER.error(f"❌ Error creating agent: {e}")
            raise
    
    def create_agent_executor(
        self, 
        agent: Any, 
        tools: List[Any], 
        callback_handler: Any,
        **executor_kwargs
    ) -> AgentExecutor:
        """
        AgentExecutor 생성
        
        Args:
            agent: LangChain 에이전트
            tools: 도구 리스트
            callback_handler: 콜백 핸들러
            **executor_kwargs: AgentExecutor 추가 파라미터
            
        Returns:
            AgentExecutor: 설정된 에이전트 실행기
        """
        try:
            # 기본 설정
            default_config = {
                "verbose": True,
                "return_intermediate_steps": True,
                "callbacks": [callback_handler]
            }
            
            # 사용자 설정과 병합
            config = {**default_config, **executor_kwargs}
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                **config
            )
            
            LOGGER.info(f"⚙️ AgentExecutor created with config: {list(config.keys())}")
            return agent_executor
            
        except Exception as e:
            LOGGER.error(f"❌ Error creating AgentExecutor: {e}")
            raise
    
    def get_chat_prompt_template(self) -> ChatPromptTemplate:
        """
        채팅용 프롬프트 템플릿 생성
        
        Returns:
            ChatPromptTemplate: 설정된 프롬프트 템플릿
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", get_en_system_prompt_with_tools()),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            LOGGER.debug("📝 Chat prompt template created")
            return prompt
            
        except Exception as e:
            LOGGER.error(f"❌ Error creating prompt template: {e}")
            raise
    
    def validate_chat_history(self, history_messages: List[Any]) -> List[BaseMessage]:
        """
        채팅 히스토리 유효성 검사 및 필터링
        
        Args:
            history_messages: 검사할 히스토리 메시지들
            
        Returns:
            List[BaseMessage]: 유효한 메시지들만 필터링된 리스트
        """
        valid_messages = []
        invalid_count = 0
        
        try:
            for i, msg in enumerate(history_messages):
                if self._is_valid_message(msg):
                    valid_messages.append(msg)
                else:
                    invalid_count += 1
                    LOGGER.debug(f"Skipped invalid message at index {i}: {type(msg)} - {msg}")
            
            LOGGER.info(f"📚 Validated chat history: {len(valid_messages)} valid, {invalid_count} invalid")
            return valid_messages
            
        except Exception as e:
            LOGGER.error(f"❌ Error validating chat history: {e}")
            return []
    
    def _is_valid_message(self, message: Any) -> bool:
        """
        개별 메시지 유효성 검사
        
        Args:
            message: 검사할 메시지
            
        Returns:
            bool: 유효한 메시지인지 여부
        """
        # BaseMessage 인스턴스인지 확인
        if not isinstance(message, BaseMessage):
            return False
        
        # 필수 속성 확인
        if not hasattr(message, 'content') or not hasattr(message, 'type'):
            return False
        
        # 콘텐츠가 비어있지 않은지 확인
        if not message.content or not isinstance(message.content, str):
            return False
        
        return True
    
    def create_execution_config(
        self,
        user_message: str,
        chat_history: List[BaseMessage],
        **additional_config
    ) -> Dict[str, Any]:
        """
        에이전트 실행을 위한 설정 생성
        
        Args:
            user_message: 사용자 메시지
            chat_history: 채팅 히스토리
            **additional_config: 추가 설정
            
        Returns:
            Dict: 에이전트 실행 설정
        """
        config = {
            "input": user_message,
            "chat_history": chat_history,
            **additional_config
        }
        
        LOGGER.debug(f"⚙️ Execution config created with {len(chat_history)} history messages")
        return config
    
    def get_tools_info(self, tools: List[Any]) -> Dict[str, Any]:
        """
        도구 정보 요약
        
        Args:
            tools: 도구 리스트
            
        Returns:
            Dict: 도구 정보 요약
        """
        if not tools:
            return {"count": 0, "tools": []}
        
        tools_info = {
            "count": len(tools),
            "tools": []
        }
        
        try:
            for tool in tools:
                tool_info = {
                    "name": getattr(tool, 'name', 'unknown'),
                    "description": getattr(tool, 'description', 'No description'),
                    "type": type(tool).__name__
                }
                tools_info["tools"].append(tool_info)
            
            LOGGER.debug(f"📊 Tools info generated for {len(tools)} tools")
            
        except Exception as e:
            LOGGER.error(f"❌ Error generating tools info: {e}")
            tools_info["error"] = str(e)
        
        return tools_info
    
    async def health_check(self) -> Dict[str, Any]:
        """
        에이전트 매니저 상태 확인
        
        Returns:
            Dict: 상태 정보
        """
        status = {
            "agent_manager": "healthy",
            "mcp_server_path": self.mcp_server_path,
            "mcp_server_exists": os.path.exists(self.mcp_server_path),
            "tools_cached": self._cached_tools is not None,
            "cache_valid": self._cache_valid,
            "tools_loading": self._tools_loading
        }
        
        try:
            # MCP 연결 테스트
            async with self.get_mcp_tools() as tools:
                status.update({
                    "mcp_connection": "ok",
                    "available_tools": len(tools),
                    "tools_names": [getattr(tool, 'name', 'unknown') for tool in tools[:5]]  # 처음 5개만
                })
                
        except Exception as e:
            status.update({
                "mcp_connection": "failed",
                "mcp_error": str(e),
                "available_tools": 0
            })
        
        LOGGER.info(f"🏥 Health check completed: {status['mcp_connection']}")
        return status


# 편의 함수들
def create_simple_agent(llm: Any, tools: List[Any]) -> Any:
    """
    간단한 에이전트 생성 편의 함수
    
    Args:
        llm: LangChain LLM
        tools: 도구 리스트
        
    Returns:
        Agent: 생성된 에이전트
    """
    manager = AgentManager()
    return manager.create_agent_with_tools(llm, tools)


def validate_message_history(messages: List[Any]) -> List[BaseMessage]:
    """
    메시지 히스토리 검증 편의 함수
    
    Args:
        messages: 검증할 메시지들
        
    Returns:
        List[BaseMessage]: 유효한 메시지들
    """
    manager = AgentManager()
    return manager.validate_chat_history(messages)


async def get_available_tools_info() -> Dict[str, Any]:
    """
    사용 가능한 도구 정보 조회 편의 함수
    
    Returns:
        Dict: 도구 정보
    """
    manager = AgentManager()
    
    try:
        async with manager.get_mcp_tools() as tools:
            return manager.get_tools_info(tools)
    except Exception as e:
        LOGGER.error(f"❌ Error getting tools info: {e}")
        return {"count": 0, "tools": [], "error": str(e)}


if __name__ == "__main__":
    """테스트 및 디버깅용"""
    import asyncio
    
    async def test_agent_manager():
        print("🎯 Agent Manager Test")
        print("=" * 50)
        
        # AgentManager 생성
        manager = AgentManager()
        
        # 상태 확인
        print("\n🏥 Health Check:")
        health = await manager.health_check()
        for key, value in health.items():
            print(f"  {key}: {value}")
        
        # 도구 정보 확인
        print("\n🔧 Available Tools:")
        try:
            async with manager.get_mcp_tools() as tools:
                tools_info = manager.get_tools_info(tools)
                print(f"  Tool Count: {tools_info['count']}")
                for tool in tools_info['tools'][:3]:  # 처음 3개만
                    print(f"    - {tool['name']}: {tool['description'][:50]}...")
        except Exception as e:
            print(f"  Error: {e}")
        
        # 메시지 검증 테스트
        print("\n📝 Message Validation Test:")
        test_messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            {"invalid": "message"},  # 유효하지 않음
            HumanMessage(content=""),  # 빈 콘텐츠
        ]
        
        valid_messages = manager.validate_chat_history(test_messages)
        print(f"  Original: {len(test_messages)}, Valid: {len(valid_messages)}")
    
    # 테스트 실행
    if asyncio.get_event_loop().is_running():
        print("Running in existing event loop - skipping test")
    else:
        asyncio.run(test_agent_manager())