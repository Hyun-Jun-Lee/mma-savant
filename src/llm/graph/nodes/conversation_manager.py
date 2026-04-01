"""Conversation Manager 노드 — 대명사 해소, 맥락 보강

압축은 그래프 완료 후 WebSocket manager에서 수행 (DB 영속화).
"""
import asyncio
import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm.graph.state import MainState
from llm.graph.prompts import CONVERSATION_MANAGER_PROMPT
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

CM_TIMEOUT_SECONDS = 10


async def conversation_manager_node(state: MainState, llm) -> dict:
    """
    대화 관리 노드 — 맥락 해소만 수행 (압축은 post-graph에서 처리)

    분기 로직:
    - messages <= 1  → 패스스루 (compressed_messages = messages)
    - history >= 1   → 맥락 해소 (_resolve_only)
    """
    messages = state.get("messages", [])

    if not messages:
        LOGGER.warning("⚠️ No messages in state")
        return {"resolved_query": "", "compressed_messages": []}

    # 최신 사용자 메시지 추출
    original_query = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            original_query = msg.content
            break

    if not original_query:
        LOGGER.warning("⚠️ No human message found")
        return {"resolved_query": "", "compressed_messages": list(messages)}

    history = messages[:-1]  # 최신 메시지 제외한 히스토리

    # --- 히스토리 없음 → 패스스루 ---
    if len(history) == 0:
        LOGGER.info("📋 No history, passing through original query")
        return {
            "resolved_query": original_query,
            "compressed_messages": list(messages),
        }

    # --- 히스토리 있음 → 맥락 해소만 ---
    sql_context = state.get("sql_context", [])
    return await _resolve_only(messages, original_query, llm, sql_context)


def _format_history_as_text(
    messages: list, original_query: str, sql_context: list[dict] | None = None,
) -> str:
    """대화 히스토리를 텍스트 컨텍스트로 포맷 (채팅이 아닌 작업 입력으로 인식시킴)"""
    history = messages[:-1]
    lines = []
    for msg in history:
        role = "사용자" if getattr(msg, "type", "") == "human" else "어시스턴트"
        lines.append(f"[{role}]: {msg.content}")
    history_text = "\n".join(lines)

    parts = [f"## 이전 대화\n{history_text}"]

    if sql_context:
        ctx_str = json.dumps(sql_context, ensure_ascii=False, default=str)
        parts.append(f"\n## 이전 SQL 결과 (엔티티 ID 참조용)\n{ctx_str}")

    parts.append(f"\n## 사용자의 최신 질문\n{original_query}")
    return "\n".join(parts)


async def _resolve_only(
    messages: list, original_query: str, llm,
    sql_context: list[dict] | None = None,
) -> dict:
    """히스토리가 짧을 때: 맥락 해소만 수행"""
    try:
        cm_messages = [
            SystemMessage(content=CONVERSATION_MANAGER_PROMPT),
            HumanMessage(content=_format_history_as_text(messages, original_query, sql_context)),
        ]

        response = await asyncio.wait_for(
            llm.ainvoke(cm_messages),
            timeout=CM_TIMEOUT_SECONDS,
        )

        resolved_text = response.content if hasattr(response, "content") else str(response)
        resolved_text = resolved_text.strip() or original_query

        LOGGER.info(f"✅ Query resolved (no compress): '{resolved_text[:80]}...'")

        return {
            "resolved_query": resolved_text,
            "compressed_messages": list(messages) + [HumanMessage(content=resolved_text)],
            "messages": [AIMessage(content=resolved_text)],
        }

    except Exception as e:
        LOGGER.error(f"❌ Resolve-only failed: {e}")
        return {
            "resolved_query": original_query,
            "compressed_messages": list(messages) + [HumanMessage(content=original_query)],
            "messages": [AIMessage(content=original_query)],
        }


