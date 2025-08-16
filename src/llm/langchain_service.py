"""
LangChain 기반 LLM 서비스
단일 MCP 서버용 최적화된 구현
"""
import os
import asyncio
import uuid
import time
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from traceback import format_exc
from contextlib import asynccontextmanager

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llm.prompts.en_ver import get_en_system_prompt_with_tools
from llm.providers import get_anthropic_llm
from llm.callbacks import get_anthropic_callback_handler
from conversation.message_manager import ChatHistoryManager
from database.connection.postgres_conn import get_async_db_context
from common.logging_config import get_logger

LOGGER = get_logger(__name__)




class LangChainLLMService:
    """LangChain 기반 LLM 서비스 - 단일 MCP 서버 최적화"""
    
    def __init__(self, max_cache_size: int = 100):
        self.history_manager = ChatHistoryManager(
            async_db_session_factory=get_async_db_context,
            max_cache_size=max_cache_size
        )
        
        # 단일 MCP 서버 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        mcp_server_path = os.path.join(src_dir, "tools", "mcp_server.py")
        
        self.server_params = StdioServerParameters(
            command="python",
            args=[mcp_server_path],
        )
        
        # MCP 도구 캐싱
        self._cached_tools = None
        self._tools_loading = False
    
    @asynccontextmanager
    async def _get_mcp_tools(self):
        """
        MCP 도구들을 context manager로 제공 (세션 유지)
        """
        print("🔄 Loading MCP tools...")
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 연결 초기화
                await session.initialize()
                
                # 도구 로드
                tools = await load_mcp_tools(session)
                print(f"✅ MCP Tools loaded: {len(tools)} tools")
                
                yield tools

    async def generate_streaming_chat_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        사용자 메시지에 대한 실제 스트리밍 채팅 응답 생성
        """
        if not session_id:
            LOGGER.error("Session ID is required for streaming chat response")
            raise ValueError("Session ID is required for streaming chat response")

        if not user_id:
            LOGGER.error("User ID is required for streaming chat response")
            raise ValueError("User ID is required for streaming chat response")

        message_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Chat history 가져오기
        try:
            history_start = time.time()
            history = await self.history_manager.get_session_history(session_id, user_id)
            history_time = time.time() - history_start
            LOGGER.info(f"⏱️ History loading: {history_time:.3f}s")
            LOGGER.info(f"📚 Loaded {len(history.messages)} messages from cache")
        except Exception as e:
            LOGGER.error(f"❌ Error loading chat history: {e}")
            LOGGER.error(format_exc())
            yield {
                "type": "error",
                "error": f"Failed to load chat history: {str(e)}",
                "message_id": message_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            return

        # 단일 MCP 서버에서 도구 로드
        try:
            mcp_start = time.time()
            async with self._get_mcp_tools() as tools:
                mcp_time = time.time() - mcp_start
                LOGGER.info(f"⏱️ MCP tools loading took: {mcp_time:.3f}s")
                LOGGER.info(f"🔧 Loaded {len(tools)} MCP tools")
                
                # 에이전트 설정 및 생성
                try:
                    # 프롬프트 템플릿 생성
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", get_en_system_prompt_with_tools()),
                        ("human", "{input}"),
                        ("placeholder", "{agent_scratchpad}"),
                    ])
                    
                    
                    # 콜백 핸들러 가져오기 (스트리밍 이벤트 처리용)
                    callback_handler = get_anthropic_callback_handler(message_id, session_id)
                    
                    # LLM Provider를 통한 LLM 생성
                    streaming_llm = get_anthropic_llm(
                        callback_handler=callback_handler
                    )

                    # 에이전트 생성 (스트리밍 LLM 사용)
                    agent = create_tool_calling_agent(streaming_llm, tools, prompt)

                    agent_executor = AgentExecutor(
                        agent=agent, 
                        tools=tools, 
                        verbose=True,
                        return_intermediate_steps=True,  
                        callbacks=[callback_handler]  
                    )

                    # 히스토리와 함께 실행하는 체인 생성
                    def get_session_history_sync(sid: str):
                        LOGGER.debug(f"get_session_history_sync called with sid: {sid}")
                        return history  # 이미 로드된 히스토리 반환
                    
                    chain_with_history = RunnableWithMessageHistory(
                        agent_executor,
                        get_session_history_sync,
                        input_messages_key="input",
                        history_messages_key="chat_history"
                    )
                    
                    LOGGER.info(f"🤖 Agent created with {len(tools)} tools")
                    
                except Exception as e:
                    LOGGER.error(f"❌ Error creating agent: {e}")
                    LOGGER.error(format_exc())
                    yield {
                        "type": "error",
                        "error": f"Failed to create agent: {str(e)}",
                        "message_id": message_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    return
                
                async def run_agent():
                    try:
                        LOGGER.info("🚀 Starting agent execution...")
                        
                        agent_exec_start = time.time()
                        invoke_start = time.time()
                        
                        # RunnableWithMessageHistory를 사용하여 실행
                        config = {"configurable": {"session_id": session_id}}
                        response_content = ""
                        tool_results = []
                        
                        # 스트리밍으로 결과 처리
                        async for chunk in chain_with_history.astream(
                            {"input": user_message},
                            config=config
                        ):
                            if isinstance(chunk, dict):
                                if "output" in chunk:
                                    content = chunk["output"]
                                    # 타입 안전성 확보
                                    if isinstance(content, str):
                                        response_content += content
                                    elif isinstance(content, list):
                                        # 리스트인 경우 각 항목 처리
                                        for item in content:
                                            if isinstance(item, dict) and 'text' in item:
                                                response_content += item['text']
                                            else:
                                                response_content += str(item)
                                    elif isinstance(content, dict):
                                        # 딕셔너리인 경우 text 필드 추출
                                        if 'text' in content:
                                            response_content += content['text']
                                        else:
                                            response_content += str(content)
                                    else:
                                        # 기타 타입은 문자열로 변환
                                        response_content += str(content)
                                
                                if "intermediate_steps" in chunk:
                                    steps = chunk["intermediate_steps"]
                                    LOGGER.info(f"🔧 Found intermediate_steps: {len(steps)} steps")
                                    for step in steps:
                                        if len(step) >= 2:
                                            action, observation = step
                                            tool_result = {
                                                "tool": getattr(action, 'tool', 'unknown'),
                                                "input": str(action.tool_input),
                                                "result": str(observation)[:500]
                                            }
                                            tool_results.append(tool_result)
                                            LOGGER.debug(f"Added tool result: {tool_result['tool']}")
                        
                        invoke_time = time.time() - invoke_start
                        agent_exec_time = time.time() - agent_exec_start
                        
                        LOGGER.info("✅ Agent execution completed")
                        LOGGER.info(f"⏱️ Chain execution took: {invoke_time:.3f}s")
                        LOGGER.info(f"⏱️ Total agent execution took: {agent_exec_time:.3f}s")
                        
                        # AI 응답을 히스토리에 추가 (메모리 즉시 + DB 백그라운드)
                        if response_content:
                            
                            ai_message = AIMessage(
                                content=response_content,
                                additional_kwargs={"tool_results": tool_results} if tool_results else {}
                            )
                            history.add_message(ai_message)
                        
                        # 결과 분석 로깅
                        if tool_results:
                            LOGGER.info(f"📊 Agent used {len(tool_results)} tools")
                            for i, tool_result in enumerate(tool_results):
                                LOGGER.info(f"   Step {i+1}: Used tool '{tool_result['tool']}'")
                        
                        # 최종 결과 큐에 추가
                        await callback_handler.stream_queue.put({
                            "type": "final_result",
                            "content": response_content,
                            "tool_results": tool_results,
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        LOGGER.error(f"❌ Agent execution failed: {e}")
                        LOGGER.error(format_exc())
                        
                        # Rate limit 에러 특별 처리
                        error_message = str(e)
                        if "rate_limit_error" in error_message or "429" in error_message:
                            LOGGER.warning("🚫 Rate limit exceeded - reducing token usage recommended")
                            error_message = "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
                        
                        await callback_handler.stream_queue.put({
                            "type": "error",
                            "error": error_message,
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        })
                    finally:
                        # 종료 신호
                        await callback_handler.stream_queue.put(None)
                
                # 에이전트 실행 태스크 시작
                agent_task = asyncio.create_task(run_agent())
                
                # 스트리밍 이벤트를 실시간으로 yield
                first_chunk_time = None
                chunk_count = 0
                while True:
                    try:
                        # 타임아웃을 두어 무한 대기 방지
                        chunk = await asyncio.wait_for(
                            callback_handler.stream_queue.get(), 
                            timeout=60.0
                        )
                        
                        if chunk is None:  # 종료 신호
                            break
                        
                        # 첫 번째 응답 청크 시간 측정
                        if first_chunk_time is None and chunk.get("type") == "content":
                            first_chunk_time = time.time() - start_time
                            print(f"⏱️ First response chunk took: {first_chunk_time:.3f}s")
                        
                        chunk_count += 1
                        
                        yield chunk
                        
                    except asyncio.TimeoutError:
                        LOGGER.warning("⚠️ Streaming timeout - sending error")
                        yield {
                            "type": "error",
                            "error": "Streaming timeout",
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        break
                    except Exception as e:
                        LOGGER.error(f"❌ Error in streaming: {e}")
                        LOGGER.error(format_exc())
                        yield {
                            "type": "error",
                            "error": str(e),
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        break
                
                try:
                    await agent_task
                except Exception as e:
                    LOGGER.error(f"❌ Agent task error: {e}")
                    LOGGER.error(format_exc())
                
                total_time = time.time() - start_time
                LOGGER.info(f"⏱️ Total streaming function took: {total_time:.3f}s")
                
        except Exception as e:
            LOGGER.error(f"❌ Error loading MCP tools: {e}")
            LOGGER.error(format_exc())
            yield {
                "type": "error",
                "error": f"Failed to load MCP tools: {str(e)}",
                "message_id": message_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }

    def get_conversation_starter(self) -> str:
        """대화 시작 메시지 반환"""
        return get_conversation_starter()
    
    async def cleanup(self):
        """리소스 정리 - MCP context manager가 자동으로 처리"""
        LOGGER.info("✅ LLM service cleanup completed")


# 글로벌 서비스 인스턴스 - 간단한 싱글톤
_langchain_service = None

async def get_langchain_service() -> LangChainLLMService:
    """글로벌 LangChain 서비스 인스턴스 반환"""
    global _langchain_service
    
    if _langchain_service is None:
        _langchain_service = LangChainLLMService()
        LOGGER.info("✅ Single MCP server LangChain service created")
    
    return _langchain_service