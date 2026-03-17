"""
LangChain 기반 LLM 서비스 V2 - 리팩토링된 버전
모듈화된 아키텍처로 다양한 LLM 프로바이더 지원 및 향상된 성능 모니터링
"""
import uuid
import time
from typing import Dict, Any, Optional, AsyncGenerator, Tuple
from traceback import format_exc

from config import Config
from llm.model_factory import create_llm_with_callbacks, get_available_providers
from llm.agent_manager import AgentManager
from llm.exceptions import LLMException
from llm.stream_processor import validate_streaming_chunk
from common.logging_config import get_logger
from common.utils import utc_now

LOGGER = get_logger(__name__)


class LangChainLLMService:
    """
    LangChain LLM 서비스 V2 - 모듈화된 아키텍처
    """

    def __init__(self, provider: Optional[str] = None):
        """
        서비스 초기화

        Args:
            provider: 사용할 LLM 프로바이더 (None이면 Config에서 결정)
        """
        self.agent_manager = AgentManager()
        self.provider = provider or Config.LLM_PROVIDER

    async def generate_streaming_chat_response(
        self,
        user_message: str,
        conversation_id: Optional[int] = None,
        user_id: Optional[int] = None,
        provider_override: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        사용자 메시지에 대한 스트리밍 채팅 응답 생성
        1질문-1응답 구조: 히스토리 없이 매번 독립 실행

        Yields:
            Dict[str, Any]: 스트리밍 응답 청크들
        """
        message_id = str(uuid.uuid4())
        start_time = time.time()

        if not user_id:
            LOGGER.error("User ID is required for streaming chat response")
            yield {
                "type": "error",
                "error": "User ID is required",
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat()
            }
            return

        try:
            # LLM + 콜백 생성
            selected_provider = provider_override or self.provider
            llm, callback_handler = create_llm_with_callbacks(
                message_id=message_id,
                conversation_id=conversation_id,
                provider=selected_provider
            )
            LOGGER.info(f"🤖 Using provider: {selected_provider}")

            # Phase 1 시작 신호
            LOGGER.info("🚀 Starting Two-Phase execution...")
            yield {
                "type": "phase_start",
                "phase": 1,
                "description": "Analyzing query and collecting data",
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat()
            }

            # Agent Two-Step 실행 + 결과 처리
            result, execution_time = await self._execute_agent_two_step(
                user_message, llm, callback_handler
            )

            async for chunk in self._process_agent_result(
                result, execution_time, message_id, conversation_id
            ):
                if validate_streaming_chunk(chunk):
                    yield chunk
                else:
                    LOGGER.warning(f"⚠️ Invalid streaming chunk filtered: {chunk}")

        except LLMException as e:
            LOGGER.error(f"❌ LLM execution failed: {e}")
            LOGGER.error(format_exc())
            yield {
                "type": "error_response",
                "error": True,
                "error_class": e.error_class,
                "traceback": format_exc(),
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat()
            }

        except Exception as e:
            LOGGER.error(f"❌ Execution error: {e}")
            LOGGER.error(format_exc())
            error_message = str(e)
            if "rate_limit_error" in error_message or "429" in error_message:
                LOGGER.warning("🚫 Rate limit exceeded")
                error_message = "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
            yield {
                "type": "error",
                "error": error_message,
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat()
            }

        finally:
            total_time = time.time() - start_time
            LOGGER.info(f"⏱️ Total streaming function took: {total_time:.3f}s")

    async def _execute_agent_two_step(
        self, user_message: str, llm: Any, callback_handler: Any
    ) -> Tuple[Dict[str, Any], float]:
        """Agent Two-Step 실행 및 시간 측정"""
        two_phase_start = time.time()

        result = await self.agent_manager.process_two_step(
            user_query=user_message,
            llm=llm,
            callback_handler=callback_handler,
            chat_history=[]
        )

        # agent_manager에서 반환된 에러 응답 필드 정규화
        if result.get("error") and "error_class" not in result:
            result["error"] = True
            result["error_class"] = "UnexpectedException"
            result["traceback"] = result.get("error_details", {}).get("traceback", "")

        execution_time = time.time() - two_phase_start
        if not result.get("error"):
            LOGGER.info(f"✅ Two-Phase completed in {execution_time:.3f}s")

        return result, execution_time

    async def _process_agent_result(
        self, result: Dict[str, Any], execution_time: float,
        message_id: str, conversation_id: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Agent 실행 결과 처리"""
        # 에러 응답인 경우 바로 반환
        if result.get("error"):
            yield {
                "type": "error_response",
                "error": True,
                "error_class": result.get("error_class", "UnexpectedException"),
                "traceback": result.get("traceback", ""),
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat(),
                "total_execution_time": execution_time
            }
            return

        # 최종 결과 반환
        yield {
            **result,
            "type": "final_result",
            "message_id": message_id,
            "conversation_id": conversation_id,
            "timestamp": utc_now().isoformat(),
            "total_execution_time": execution_time
        }

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
                "timestamp": utc_now().isoformat(),
                "version": "2.0"
            }

            # 프로바이더 상태
            available_providers = get_available_providers()
            health_status.update({
                "llm_provider": self.provider,
                "available_providers": available_providers,
                "providers_count": len(available_providers)
            })

            # Two-Phase 시스템 상태
            agent_health = await self.agent_manager.health_check()
            health_status["two_phase_system"] = agent_health
            health_status["agent_manager_version"] = "v2"

            return health_status

        except Exception as e:
            LOGGER.error(f"❌ Health check error: {e}")
            return {
                "service": "LangChainLLMServiceV2",
                "status": "error",
                "error": str(e),
                "timestamp": utc_now().isoformat(),
                "two_phase_system": True
            }

    async def cleanup(self):
        """리소스 정리"""
        try:
            # Two-Phase 시스템 정리 (AgentManager는 MCP 캐시가 없음)
            if hasattr(self, 'agent_manager'):
                LOGGER.info("🧹 AgentManager cleanup (no MCP cache to clear)")

            LOGGER.info("✅ Two-Phase LLM service V2 cleanup completed")

        except Exception as e:
            LOGGER.error(f"❌ Two-Phase cleanup error: {e}")


# 글로벌 서비스 인스턴스 관리
_langchain_service_v2 = None


async def get_langchain_service(
    provider: Optional[str] = None
) -> LangChainLLMService:
    """
    글로벌 LangChain 서비스 V2 인스턴스 반환

    Args:
        provider: LLM 프로바이더 (새 인스턴스 생성 시에만 적용)

    Returns:
        LangChainLLMService: 서비스 인스턴스
    """
    global _langchain_service_v2

    if _langchain_service_v2 is None:
        _langchain_service_v2 = LangChainLLMService(
            provider=provider
        )
        LOGGER.info("✅ Two-Phase LangChain service V2 created")

    return _langchain_service_v2


# 편의 함수들
async def create_streaming_response(
    user_message: str,
    conversation_id : int,
    user_id: int,
    provider: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    스트리밍 응답 생성 편의 함수

    Args:
        user_message: 사용자 메시지
        conversation_id: 세션 ID
        user_id: 사용자 ID
        provider: 프로바이더 오버라이드

    Yields:
        Dict[str, Any]: 스트리밍 응답 청크들
    """
    service = await get_langchain_service(provider=provider)

    async for chunk in service.generate_streaming_chat_response(
        user_message=user_message,
        conversation_id=conversation_id,
        user_id=user_id,
        provider_override=provider
    ):
        yield chunk


if __name__ == "__main__":
    """테스트 및 디버깅용"""
    import asyncio

    async def test_service_v2():
        print("🚀 Two-Phase LangChain Service V2 Test")
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

            print(f"\n✅ Two-Phase Service V2 test completed successfully")

        except Exception as e:
            print(f"\n❌ Two-Phase Service V2 test failed: {e}")
            import traceback
            traceback.print_exc()

    # 테스트 실행
    if asyncio.get_event_loop().is_running():
        print("Running in existing event loop - skipping test")
    else:
        asyncio.run(test_service_v2())