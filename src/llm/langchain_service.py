"""
LangChain 기반 LLM 서비스
MCP tools와 LangChain 통합
"""
import asyncio
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import LLMResult

from config import Config
from llm.prompts import get_system_prompt_with_tools, get_conversation_starter


class StreamingCallbackHandler(AsyncCallbackHandler):
    """스트리밍 응답을 위한 콜백 핸들러"""
    
    def __init__(self):
        self.tokens = []
        self.message_id = str(uuid.uuid4())
        self.session_id = None
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """새 토큰이 생성될 때 호출"""
        self.tokens.append(token)
        # 여기서 스트리밍 이벤트를 발생시킬 수 있습니다
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM 시작 시 호출"""
        self.tokens = []
    
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 종료 시 호출"""
        pass


class LangChainLLMService:
    """LangChain 기반 LLM 서비스"""
    
    def __init__(self):
        # Anthropic LLM 초기화
        self.llm = ChatAnthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            model=Config.ANTHROPIC_MODEL_NAME,
            temperature=0.7,
            max_tokens=4000,
            streaming=True
        )
        
        # MCP 클라이언트 초기화
        self.mcp_client = None
        self.tools = []
        self._initialized = False
    
    async def initialize(self):
        """MCP 클라이언트 및 도구 초기화"""
        if self._initialized:
            return
        
        try:
            # MCP 서버 설정
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(current_dir)
            mcp_server_path = os.path.join(src_dir, "tools", "mcp_server.py")
            
            server_config = {
                "mma-savant": {
                    "command": "python",
                    "args": [mcp_server_path],
                    "transport": "stdio"
                }
            }
            
            # MCP 클라이언트 생성
            self.mcp_client = MultiServerMCPClient(server_config)
            
            # 도구 로드
            self.tools = await self.mcp_client.get_tools()
            print(f"✅ LangChain MCP Tools loaded: {len(self.tools)} tools")
            
            self._initialized = True
            
        except Exception as e:
            print(f"❌ Failed to initialize MCP client: {e}")
            self.tools = []
    
    async def generate_chat_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 메시지에 대한 채팅 응답 생성 (비스트리밍)
        """
        await self.initialize()
        
        try:
            # 메시지 히스토리 준비
            messages = self._prepare_messages(user_message, conversation_history)
            
            # 프롬프트 템플릿 생성
            prompt = ChatPromptTemplate.from_messages([
                ("system", get_system_prompt_with_tools()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            # 에이전트 생성
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
            
            # 에이전트 실행
            result = await agent_executor.ainvoke({
                "input": user_message,
                "chat_history": messages[:-1]  # 마지막 사용자 메시지 제외
            })
            
            return {
                "content": result["output"],
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "tool_calls": result.get("intermediate_steps", [])
            }
                
        except Exception as e:
            raise Exception(f"Failed to generate chat response: {str(e)}")
    
    async def generate_streaming_chat_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        사용자 메시지에 대한 스트리밍 채팅 응답 생성
        """
        await self.initialize()
        
        message_id = str(uuid.uuid4())
        
        try:
            # 시작 신호
            yield {
                "type": "start",
                "message_id": message_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 메시지 히스토리 준비
            messages = self._prepare_messages(user_message, conversation_history)
            
            # 스트리밍 응답 생성
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield {
                        "type": "content",
                        "content": chunk.content,
                        "message_id": message_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 종료 신호
            yield {
                "type": "end",
                "message_id": message_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "message_id": message_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_messages(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ):
        """LangChain 메시지 형식으로 변환"""
        messages = []
        
        # 시스템 메시지 추가
        messages.append(SystemMessage(content=get_system_prompt_with_tools()))
        
        # 대화 히스토리 추가
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # 현재 사용자 메시지 추가
        messages.append(HumanMessage(content=user_message))
        
        return messages
    
    def get_conversation_starter(self) -> str:
        """대화 시작 메시지 반환"""
        return get_conversation_starter()
    
    async def cleanup(self):
        """리소스 정리"""
        if self.mcp_client:
            await self.mcp_client.cleanup()


# 글로벌 서비스 인스턴스
_langchain_service = None

async def get_langchain_service() -> LangChainLLMService:
    """글로벌 LangChain 서비스 인스턴스 반환"""
    global _langchain_service
    if _langchain_service is None:
        _langchain_service = LangChainLLMService()
        await _langchain_service.initialize()
    return _langchain_service