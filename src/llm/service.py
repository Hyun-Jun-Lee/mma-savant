"""MMA Graph 서비스 - StateGraph 기반 LLM 응답 생성"""
import asyncio
import uuid
import time
from typing import Dict, Any, Optional, AsyncGenerator, List
from traceback import format_exc

from langchain_core.messages import HumanMessage, AIMessage

from config import Config
from llm.model_factory import create_llm_with_callbacks
from llm.graph import build_mma_graph
from llm.exceptions import LLMException
from common.logging_config import get_logger
from common.utils import utc_now

LOGGER = get_logger(__name__)

GRAPH_TIMEOUT_SECONDS = 60


class MMAGraphService:
    """StateGraph 기반 MMA LLM 서비스"""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or Config.LLM_PROVIDER
        self._llm = None
        self._compiled_graph = None

    async def initialize(self):
        """LLM 및 그래프 초기화 (한 번만 실행)"""
        if self._compiled_graph is not None:
            return

        llm, _ = create_llm_with_callbacks(
            message_id="graph-init",
            conversation_id=0,
            provider=self.provider,
        )
        self._llm = llm
        self._compiled_graph = build_mma_graph(llm)
        LOGGER.info(f"✅ MMA Graph service initialized (provider: {self.provider})")

    @staticmethod
    def build_messages_from_history(chat_history: List) -> list:
        """
        DB 채팅 히스토리(ChatMessageResponse 리스트)를 LangChain 메시지로 변환.
        최근 20개 메시지로 슬라이딩 윈도우 적용.
        """
        if not chat_history:
            return []

        messages = []
        for msg in chat_history:
            role = msg.role if hasattr(msg, "role") else msg.get("role", "")
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        if len(messages) > 10:
            messages = messages[-10:]

        return messages

    async def generate_streaming_chat_response(
        self,
        user_message: str,
        conversation_id: Optional[int] = None,
        user_id: Optional[int] = None,
        chat_history: Optional[List] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        StateGraph 실행 결과를 기존 인터페이스와 호환되는 형태로 yield.

        Yields:
            Dict[str, Any]: type=final_result | error | error_response
        """
        message_id = str(uuid.uuid4())
        start_time = time.time()

        if not user_id:
            yield {
                "type": "error",
                "error": "User ID is required",
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat(),
            }
            return

        try:
            await self.initialize()

            # 히스토리 + 현재 메시지 구성
            messages = self.build_messages_from_history(chat_history)
            messages.append(HumanMessage(content=user_message))

            # 그래프 실행 (타임아웃 적용)
            result = await asyncio.wait_for(
                self._compiled_graph.ainvoke({
                    "messages": messages,
                    "user_id": user_id,
                    "conversation_id": conversation_id or 0,
                }),
                timeout=GRAPH_TIMEOUT_SECONDS,
            )

            execution_time = time.time() - start_time

            # 결과 추출
            final_response = result.get("final_response", "")
            visualization_type = result.get("visualization_type")
            visualization_data = result.get("visualization_data")
            insights = result.get("insights", [])

            # 프론트엔드용 content 추출
            if visualization_type and visualization_type != "text_summary" and visualization_data:
                # 차트 시각화: 텍스트 content를 비움 (ChartRenderer가 표시)
                content = ""
            else:
                # text_summary: visualization_data.content에서 깨끗한 텍스트 추출
                if visualization_data and visualization_data.get("content"):
                    content = visualization_data["content"]
                else:
                    raise LLMException(
                        "visualization_data에 content 필드가 없습니다. "
                        f"visualization_type={visualization_type}, "
                        f"keys={list(visualization_data.keys()) if visualization_data else None}",
                        error_class="MISSING_CONTENT_FIELD",
                    )

            yield {
                "type": "final_result",
                "content": content,
                "final_response": final_response,
                "visualization_type": visualization_type,
                "visualization_data": visualization_data,
                "insights": insights,
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat(),
                "total_execution_time": execution_time,
            }

        except LLMException as e:
            LOGGER.error(f"❌ Graph execution failed: {e}")
            yield {
                "type": "error_response",
                "error": True,
                "error_class": e.error_class,
                "traceback": format_exc(),
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat(),
            }

        except Exception as e:
            LOGGER.error(f"❌ Graph execution error: {e}")
            if isinstance(e, asyncio.TimeoutError):
                error_message = (
                    f"응답 생성 시간이 {GRAPH_TIMEOUT_SECONDS}초를 초과했습니다. "
                    "질문을 더 간단하게 바꿔서 다시 시도해주세요."
                )
            else:
                error_message = str(e)
            if "rate_limit_error" in error_message or "429" in error_message:
                error_message = "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
            yield {
                "type": "error",
                "error": error_message,
                "message_id": message_id,
                "conversation_id": conversation_id,
                "timestamp": utc_now().isoformat(),
            }

        finally:
            total_time = time.time() - start_time
            LOGGER.info(f"⏱️ Graph execution took: {total_time:.3f}s")

    async def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "service": "MMAGraphService",
            "status": "healthy",
            "provider": self.provider,
            "graph_compiled": self._compiled_graph is not None,
            "timestamp": utc_now().isoformat(),
        }

    async def cleanup(self):
        """리소스 정리"""
        self._compiled_graph = None
        self._llm = None
        LOGGER.info("✅ MMA Graph service cleanup completed")


# 글로벌 서비스 인스턴스
_graph_service: Optional[MMAGraphService] = None


async def get_graph_service(
    provider: Optional[str] = None,
) -> MMAGraphService:
    """글로벌 MMA Graph 서비스 인스턴스 반환"""
    global _graph_service

    if _graph_service is None:
        _graph_service = MMAGraphService(provider=provider)
        LOGGER.info("✅ MMA Graph service created")

    return _graph_service
