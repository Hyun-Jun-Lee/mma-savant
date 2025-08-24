"""
LangChain 기반 LLM 서비스 V2 - 리팩토링된 버전
모듈화된 아키텍처로 다양한 LLM 프로바이더 지원 및 향상된 성능 모니터링
"""
import os
import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from traceback import format_exc

from langchain_core.messages import AIMessage, HumanMessage

from config import Config
from llm.model_factory import create_llm_with_callbacks, get_available_providers
from llm.agent_manager import AgentManager
from llm.stream_processor import (
    extract_safe_text_content, 
    clean_response_content,
    create_final_result,
    create_error_response,
    validate_streaming_chunk
)
from common.utils import remove_timestamps_from_tool_result
from llm.performance_monitor import setup_langsmith_tracing
from conversation.message_manager import ChatHistoryManager
from database.connection.postgres_conn import get_async_db_context
from common.logging_config import get_logger
from common.utils import kr_time_now

LOGGER = get_logger(__name__)


class LangChainLLMService:
    """
    LangChain LLM 서비스 V2 - 모듈화된 아키텍처
    """
    
    def __init__(self, max_cache_size: int = 100, provider: Optional[str] = None):
        """
        서비스 초기화
        
        Args:
            max_cache_size: 히스토리 캐시 크기
            provider: 사용할 LLM 프로바이더 (None이면 Config에서 결정)
        """
        # 성능 모니터링 및 트레이싱 설정
        setup_langsmith_tracing()
        
        # 핵심 컴포넌트 초기화
        self.history_manager = ChatHistoryManager(
            async_db_session_factory=get_async_db_context,
            max_cache_size=max_cache_size
        )
        
        self.agent_manager = AgentManager()
        
        # LLM 프로바이더 설정
        self.provider = provider or Config.LLM_PROVIDER
    
    async def generate_streaming_chat_response(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        provider_override: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        사용자 메시지에 대한 스트리밍 채팅 응답 생성
        
        Args:
            user_message: 사용자 메시지
            session_id: 세션 ID
            user_id: 사용자 ID
            provider_override: 프로바이더 오버라이드
        
        Yields:
            Dict[str, Any]: 스트리밍 응답 청크들
        """
        # 필수 매개변수 검증
        if not session_id:
            LOGGER.error("Session ID is required for streaming chat response")
            yield create_error_response(
                ValueError("Session ID is required"),
                "unknown",
                "unknown"
            )
            return

        if not user_id:
            LOGGER.error("User ID is required for streaming chat response")
            yield create_error_response(
                ValueError("User ID is required"),
                "unknown",
                session_id
            )
            return

        message_id = str(uuid.uuid4())
        start_time = time.time()
        
        # LangSmith 메타데이터 설정
        langsmith_metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "message_id": message_id,
            "service": "mma-savant",
            "version": "2.0",
            "start_time": kr_time_now().isoformat()
        }
        
        # LangSmith 메타데이터 준비 (자동으로 추적됨)
        if Config.LANGCHAIN_TRACING_V2:
            LOGGER.debug(f"LangSmith metadata prepared: {langsmith_metadata}")
        
        try:
            
            # 1. 채팅 히스토리 로드
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
                    "timestamp": kr_time_now().isoformat()
                }
                return
            
            # 2. MCP 도구 로드 및 LLM 설정
            try:
                mcp_start = time.time()
                async with self.agent_manager.get_mcp_tools() as tools:
                    mcp_time = time.time() - mcp_start
                    LOGGER.info(f"⏱️ MCP tools loading took: {mcp_time:.3f}s")
                    LOGGER.info(f"🔧 Loaded {len(tools)} MCP tools")
                    
                    # 에이전트 설정 및 생성
                    try:
                        # LLM 및 콜백 생성
                        selected_provider = provider_override or self.provider
                        llm, callback_handler = create_llm_with_callbacks(
                            message_id=message_id,
                            session_id=session_id,
                            provider=selected_provider
                        )
                        
                        LOGGER.info(f"🤖 Using provider: {selected_provider}")
                        
                        # 히스토리 검증 및 에이전트 생성
                        valid_chat_history = self.agent_manager.validate_chat_history(history.messages)
                        agent = self.agent_manager.create_agent_with_tools(llm, tools, valid_chat_history)
                        agent_executor = self.agent_manager.create_agent_executor(
                            agent, tools, callback_handler
                        )
                        
                        LOGGER.info(f"📚 Using {len(valid_chat_history)} valid messages for context")
                        LOGGER.info(f"🤖 Agent created with {len(tools)} tools")
                        
                    except Exception as e:
                        LOGGER.error(f"❌ Error creating agent: {e}")
                        LOGGER.error(format_exc())
                        yield {
                            "type": "error",
                            "error": f"Failed to create agent: {str(e)}",
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": kr_time_now().isoformat()
                        }
                        return
                
                    # 3. 에이전트 실행 및 스트리밍
                    async for chunk in self._execute_agent_with_streaming(
                        agent_executor=agent_executor,
                        user_message=user_message,
                        chat_history=valid_chat_history,
                        callback_handler=callback_handler,
                        history=history,
                        message_id=message_id,
                        session_id=session_id,
                        user_id=user_id
                    ):
                        # 청크 유효성 검사
                        if validate_streaming_chunk(chunk):
                            yield chunk
                        else:
                            LOGGER.warning(f"⚠️ Invalid streaming chunk filtered: {chunk}")
            
            except Exception as e:
                LOGGER.error(f"❌ Error loading MCP tools: {e}")
                LOGGER.error(format_exc())
                yield {
                    "type": "error",
                    "error": f"Failed to load MCP tools: {str(e)}",
                    "message_id": message_id,
                    "session_id": session_id,
                    "timestamp": kr_time_now().isoformat()
                }
        
        except Exception as e:
            LOGGER.error(f"❌ Main execution error: {e}")
            LOGGER.error(format_exc())
            yield {
                "type": "error", 
                "error": str(e),
                "message_id": message_id,
                "session_id": session_id,
                "timestamp": kr_time_now().isoformat()
            }
        
        finally:
            # 총 실행 시간 로깅
            total_time = time.time() - start_time
            LOGGER.info(f"⏱️ Total streaming function took: {total_time:.3f}s")
            
            # LangSmith 최종 메트릭 로깅 (자동으로 추적됨)
            if Config.LANGCHAIN_TRACING_V2:
                final_metrics = {
                    "total_streaming_time": total_time,
                    "message_id": message_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "completion_status": "success"
                }
                LOGGER.info(f"LangSmith final metrics: {final_metrics}")
    
    async def _execute_agent_with_streaming(
        self,
        agent_executor,
        user_message: str,
        chat_history: List,
        callback_handler,
        history,
        message_id: str,
        session_id: str,
        user_id: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        에이전트 실행 및 스트리밍 처리
        """
        response_content = ""
        tool_results = []
        
        async def run_agent():
            nonlocal response_content, tool_results
            
            try:
                agent_exec_start = time.time()
                LOGGER.info("🚀 Starting agent execution...")
                
                # 사용자 메시지를 히스토리에 추가
                user_msg = HumanMessage(content=user_message)
                history.add_message(user_msg)
                
                # 에이전트 실행 설정
                execution_config = self.agent_manager.create_execution_config(
                    user_message=user_message,
                    chat_history=chat_history
                )
                
                # 에이전트 스트리밍 실행 (v1과 동일한 방식)
                async for chunk in agent_executor.astream(execution_config):
                    if isinstance(chunk, dict):
                        if "output" in chunk:
                            content = chunk["output"]
                            extracted_text = extract_safe_text_content(content)
                            if extracted_text:
                                response_content += extracted_text
                        
                        if "intermediate_steps" in chunk:
                            steps = chunk["intermediate_steps"]
                            LOGGER.info(f"🔧 Found intermediate_steps: {len(steps)} steps")
                            for step in steps:
                                if len(step) >= 2:
                                    action, observation = step
                                    tool_result = {
                                        "tool": getattr(action, 'tool', 'unknown'),
                                        "input": str(action.tool_input),
                                        "result": str(remove_timestamps_from_tool_result(observation))
                                    }
                                    tool_results.append(tool_result)
                
                agent_exec_time = time.time() - agent_exec_start
                LOGGER.info("✅ Agent execution completed")
                LOGGER.info(f"⏱️ Total agent execution took: {agent_exec_time:.3f}s")
                
                # AI 응답을 히스토리에 추가 (메모리 즉시 + DB 백그라운드)
                if response_content:
                    # response_content가 문자열인지 확인 및 정리
                    if isinstance(response_content, str):
                        clean_content = response_content.strip()
                    else:
                        LOGGER.warning(f"⚠️ Non-string response_content: {type(response_content)} - {response_content}")
                        clean_content = extract_safe_text_content(response_content)
                    
                    if clean_content:
                        ai_message = AIMessage(
                            content=clean_content,
                            additional_kwargs={"tool_results": tool_results if tool_results else []}
                        )
                        history.add_message(ai_message)
                        LOGGER.info(f"✅ AI message added to history: {len(clean_content)} chars")
                    else:
                        LOGGER.warning("⚠️ Empty or invalid response content after cleaning - not adding to history")
                
                # 결과 분석 로깅
                if tool_results:
                    LOGGER.info(f"📊 Agent used {len(tool_results)} tools")
                    for i, tool_result in enumerate(tool_results):
                        LOGGER.info(f"   Step {i+1}: Used tool '{tool_result['tool']}'")
                
                # 최종 결과 큐에 추가
                final_result = {
                    "type": "final_result",
                    "content": response_content,
                    "tool_results": tool_results,
                    "message_id": message_id,
                    "session_id": session_id,
                    "timestamp": kr_time_now().isoformat(),
                    "total_execution_time": agent_exec_time,
                    "langsmith_enabled": Config.LANGCHAIN_TRACING_V2
                }
                
                # LangSmith 성능 메트릭 추가
                if Config.LANGCHAIN_TRACING_V2:
                    performance_metrics = {
                        "total_execution_time": agent_exec_time,
                        "tools_used_count": len(tool_results),
                        "response_length": len(response_content),
                        "user_id": user_id,
                        "session_id": session_id
                    }
                    LOGGER.info(f"LangSmith performance metrics: {performance_metrics}")
                    final_result["performance_metrics"] = performance_metrics
                
                await callback_handler.stream_queue.put(final_result)
                    
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
                    "timestamp": kr_time_now().isoformat(),
                    "langsmith_enabled": Config.LANGCHAIN_TRACING_V2
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
                    first_chunk_time = time.time()
                    LOGGER.debug("⚡ First response chunk received")
                
                chunk_count += 1
                yield chunk
                
            except asyncio.TimeoutError:
                LOGGER.warning("⚠️ Streaming timeout - sending error")
                yield {
                    "type": "error",
                    "error": "Streaming timeout",
                    "message_id": message_id,
                    "session_id": session_id,
                    "timestamp": kr_time_now().isoformat()
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
                    "timestamp": kr_time_now().isoformat()
                }
                break
        
        try:
            await agent_task
        except Exception as e:
            LOGGER.error(f"❌ Agent task error: {e}")
    
    def get_conversation_starter(self) -> str:
        """대화 시작 메시지 반환"""
        try:
            # 사용 가능한 프로바이더에 따른 맞춤 메시지
            available_providers = get_available_providers()
            provider_info = f" (Using {self.provider})" if len(available_providers) > 1 else ""
            
            return f"안녕하세요! MMA Savant에 오신 것을 환영합니다{provider_info}. MMA에 관한 모든 것을 물어보세요!"
            
        except Exception as e:
            LOGGER.error(f"❌ Error getting conversation starter: {e}")
            return "안녕하세요! MMA에 관한 질문을 해주세요."
    
    async def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        try:
            # 기본 상태
            health_status = {
                "service": "LangChainLLMServiceV2",
                "status": "healthy",
                "timestamp": kr_time_now().isoformat(),
                "version": "2.0"
            }
            
            # 프로바이더 상태
            available_providers = get_available_providers()
            health_status.update({
                "llm_provider": self.provider,
                "available_providers": available_providers,
                "providers_count": len(available_providers)
            })
            
            # 에이전트 매니저 상태
            agent_health = await self.agent_manager.health_check()
            health_status["agent_manager"] = agent_health
            
            # LangSmith 상태
            health_status["langsmith_enabled"] = Config.LANGCHAIN_TRACING_V2
            
            return health_status
            
        except Exception as e:
            LOGGER.error(f"❌ Health check error: {e}")
            return {
                "service": "LangChainLLMServiceV2",
                "status": "error",
                "error": str(e),
                "timestamp": kr_time_now().isoformat()
            }
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            # 에이전트 매니저 정리
            if hasattr(self, 'agent_manager'):
                self.agent_manager.clear_tools_cache()
            
            LOGGER.info("✅ LLM service V2 cleanup completed")
            
        except Exception as e:
            LOGGER.error(f"❌ Cleanup error: {e}")


# 글로벌 서비스 인스턴스 관리
_langchain_service_v2 = None


async def get_langchain_service(
    provider: Optional[str] = None,
    max_cache_size: int = 100
) -> LangChainLLMService:
    """
    글로벌 LangChain 서비스 V2 인스턴스 반환
    
    Args:
        provider: LLM 프로바이더 (새 인스턴스 생성 시에만 적용)
        max_cache_size: 캐시 크기 (새 인스턴스 생성 시에만 적용)
    
    Returns:
        LangChainLLMService: 서비스 인스턴스
    """
    global _langchain_service_v2
    
    if _langchain_service_v2 is None:
        _langchain_service_v2 = LangChainLLMService(
            max_cache_size=max_cache_size,
            provider=provider
        )
        LOGGER.info("✅ LangChain service V2 created")
    
    return _langchain_service_v2


# 편의 함수들
async def create_streaming_response(
    user_message: str,
    session_id: str,
    user_id: int,
    provider: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    스트리밍 응답 생성 편의 함수
    
    Args:
        user_message: 사용자 메시지
        session_id: 세션 ID
        user_id: 사용자 ID
        provider: 프로바이더 오버라이드
    
    Yields:
        Dict[str, Any]: 스트리밍 응답 청크들
    """
    service = await get_langchain_service(provider=provider)
    
    async for chunk in service.generate_streaming_chat_response(
        user_message=user_message,
        session_id=session_id,
        user_id=user_id,
        provider_override=provider
    ):
        yield chunk


if __name__ == "__main__":
    """테스트 및 디버깅용"""
    import asyncio
    
    async def test_service_v2():
        print("🚀 LangChain Service V2 Test")
        print("=" * 50)
        
        try:
            # 서비스 생성
            service = await get_langchain_service()
            
            # 상태 확인
            health = await service.health_check()
            print(f"\n🏥 Health Check:")
            print(f"  Status: {health['status']}")
            print(f"  Provider: {health['llm_provider']}")
            print(f"  Available Providers: {health['available_providers']}")
            
            # 대화 시작 메시지
            starter = service.get_conversation_starter()
            print(f"\n💬 Conversation Starter:")
            print(f"  {starter}")
            
            print(f"\n✅ Service V2 test completed successfully")
            
        except Exception as e:
            print(f"\n❌ Service V2 test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # 테스트 실행
    if asyncio.get_event_loop().is_running():
        print("Running in existing event loop - skipping test")
    else:
        asyncio.run(test_service_v2())