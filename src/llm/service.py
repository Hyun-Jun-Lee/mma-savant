"""MMA Graph 서비스 - StateGraph 기반 LLM 응답 생성"""
import asyncio
import json
import uuid
import time
from typing import Dict, Any, Optional, AsyncGenerator, List
from traceback import format_exc

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from config import Config
from llm.model_factory import create_llm_with_callbacks, get_main_model, get_sub_model
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
        self._sub_llm = None
        self._compiled_graph = None

    async def initialize(self):
        """LLM 및 그래프 초기화 (한 번만 실행)"""
        if self._compiled_graph is not None:
            return

        if Config.MAIN_MODEL and Config.SUB_MODEL:
            main_llm = get_main_model()
            sub_llm = get_sub_model()
            self._llm = main_llm
            self._sub_llm = sub_llm
            self._compiled_graph = build_mma_graph(main_llm, sub_llm)
            LOGGER.info(
                f"✅ MMA Graph service initialized "
                f"(main={Config.MAIN_MODEL}, sub={Config.SUB_MODEL})"
            )
        else:
            llm, _ = create_llm_with_callbacks(
                message_id="graph-init",
                conversation_id=0,
                provider=self.provider,
            )
            self._llm = llm
            self._compiled_graph = build_mma_graph(llm)
            LOGGER.info(f"✅ MMA Graph service initialized (provider: {self.provider})")

    @staticmethod
    def build_messages_from_history(
        chat_history: List,
        compressed_context: Optional[str] = None,
    ) -> list:
        """
        DB 채팅 히스토리(ChatMessageResponse 리스트)를 LangChain 메시지로 변환.
        극단적 상황 방지를 위한 최대 100턴 상한 적용.
        (실제 슬라이딩 윈도우는 ConversationManager 노드에서 처리)
        """
        if not chat_history and not compressed_context:
            return []

        messages = []

        # 압축된 이전 대화 요약이 있으면 SystemMessage로 맨 앞에 삽입
        if compressed_context:
            messages.append(SystemMessage(content=f"[이전 대화 요약] {compressed_context}"))

        for msg in (chat_history or []):
            role = msg.role if hasattr(msg, "role") else msg.get("role", "")
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        if len(messages) > 100:
            messages = messages[-100:]

        return messages

    @staticmethod
    def extract_sql_context(chat_history: List) -> list[dict]:
        """
        DB 채팅 히스토리에서 SQL 컨텍스트(tool_results)를 추출.
        conversation_manager 노드에서만 사용 (다른 노드에 전파하지 않음).
        """
        if not chat_history:
            return []

        sql_context = []
        for msg in chat_history:
            role = msg.role if hasattr(msg, "role") else msg.get("role", "")
            tool_results = getattr(msg, "tool_results", None) if hasattr(msg, "role") else msg.get("tool_results")

            if role == "assistant" and tool_results:
                sql_context.extend(tool_results)

        return sql_context

    async def generate_streaming_chat_response(
        self,
        user_message: str,
        conversation_id: Optional[int] = None,
        user_id: Optional[int] = None,
        chat_history: Optional[List] = None,
        compressed_context: Optional[str] = None,
        compressed_sql_context: Optional[List[dict]] = None,
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
            messages = self.build_messages_from_history(
                chat_history, compressed_context=compressed_context,
            )
            messages.append(HumanMessage(content=user_message))

            sql_context = self.extract_sql_context(chat_history)
            if compressed_sql_context:
                sql_context = compressed_sql_context + sql_context
            sql_context = sql_context[-10:]  # 최대 10개

            # 그래프 실행 (타임아웃 적용)
            result = await asyncio.wait_for(
                self._compiled_graph.ainvoke({
                    "messages": messages,
                    "sql_context": sql_context,
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

            # SQL 에이전트 결과 → compact 형태로 추출
            agent_results_raw = result.get("agent_results", [])
            compact_agent_results = [
                {"query": r.get("query", ""), "data": r.get("data", [])}
                for r in agent_results_raw if r.get("data")
            ] or None

            # text_response만 실행된 경우 또는 Critic 소진 시
            # visualization_type/data가 없으므로 text_summary 폴백
            if not visualization_type or not visualization_data:
                visualization_type = "text_summary"
                visualization_data = {"title": "", "content": final_response}

            content = final_response

            yield {
                "type": "final_result",
                "content": content,
                "final_response": final_response,
                "visualization_type": visualization_type,
                "visualization_data": visualization_data,
                "insights": insights,
                "agent_results": compact_agent_results,
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

    async def compress_conversation(
        self,
        messages_to_compress: list,
        existing_summary: Optional[str] = None,
        sql_context: Optional[list[dict]] = None,
    ) -> Optional[str]:
        """LLM 압축 실행. 실패 시 None 반환."""
        from llm.graph.prompts import POST_GRAPH_COMPRESS_PROMPT
        from llm.graph.schemas import CompressionOutput

        await self.initialize()

        compress_llm = self._sub_llm or self._llm
        if not compress_llm:
            LOGGER.error("❌ No LLM available for compression")
            return None

        # 대화 내용을 텍스트로 포맷
        lines = []
        if existing_summary:
            lines.append(f"[기존 대화 요약] {existing_summary}")
        for msg in messages_to_compress:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            label = "사용자" if role == "user" else "어시스턴트"
            lines.append(f"[{label}]: {content}")

        conversation_text = "\n".join(lines)

        try:
            structured_llm = compress_llm.with_structured_output(CompressionOutput)
            result = await asyncio.wait_for(
                structured_llm.ainvoke([
                    SystemMessage(content=POST_GRAPH_COMPRESS_PROMPT),
                    HumanMessage(content=conversation_text),
                ]),
                timeout=10,
            )
            return result.summary.strip()
        except Exception as e:
            LOGGER.warning(f"⚠️ Compression failed (will retry next turn): {e}")
            return None

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
