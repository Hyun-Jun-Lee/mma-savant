"""Conversation Manager 노드 — 대명사 해소, 맥락 보강, 히스토리 압축"""
import asyncio
import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm.graph.state import MainState
from llm.graph.prompts import (
    CONVERSATION_MANAGER_PROMPT,
    CONVERSATION_MANAGER_COMPRESS_PROMPT,
)
from llm.graph.schemas import ConversationManagerOutput
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

CM_TIMEOUT_SECONDS = 10
COMPRESS_THRESHOLD = 6  # 히스토리 메시지 수 (최근 3턴 = 6 메시지)


async def conversation_manager_node(state: MainState, llm) -> dict:
    """
    대화 관리 노드 — 맥락 해소 + 히스토리 압축

    분기 로직:
    - messages <= 1  → 패스스루 (compressed_messages = messages)
    - history <= 6   → 맥락 해소만 (기존 로직, compressed_messages = 전체)
    - history > 6    → 압축 + 맥락 해소 (단일 structured output LLM 호출)
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

    # --- Branch 1: 히스토리 없음 → 패스스루 ---
    if len(history) == 0:
        LOGGER.info("📋 No history, passing through original query")
        return {
            "resolved_query": original_query,
            "compressed_messages": list(messages),
        }

    sql_context = state.get("sql_context", [])

    # --- Branch 2: 히스토리 짧음 (<=6) → 맥락 해소만 ---
    if len(history) <= COMPRESS_THRESHOLD:
        return await _resolve_only(messages, original_query, llm, sql_context)

    # --- Branch 3: 히스토리 김 (>6) → 압축 + 맥락 해소 ---
    return await _compress_and_resolve(messages, history, original_query, llm, sql_context)


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


async def _compress_and_resolve(
    messages: list, history: list, original_query: str, llm,
    sql_context: list[dict] | None = None,
) -> dict:
    """히스토리가 길 때: LLM으로 이전 대화 요약 + 맥락 해소를 동시 수행"""
    older = history[:-COMPRESS_THRESHOLD]   # 요약 대상
    recent = history[-COMPRESS_THRESHOLD:]  # 최근 3턴 원본 유지
    current_msg = messages[-1]              # 사용자 최신 메시지

    sql_ctx_msg = []
    if sql_context:
        ctx_str = json.dumps(sql_context, ensure_ascii=False, default=str)
        sql_ctx_msg = [SystemMessage(
            content=f"--- 이전 SQL 결과 (엔티티 ID 참조용) ---\n{ctx_str}"
        )]

    try:
        # 단일 structured output 호출로 요약 + 맥락 해소
        compress_messages = [
            SystemMessage(content=CONVERSATION_MANAGER_COMPRESS_PROMPT),
            SystemMessage(content="--- 이전 대화 (요약 대상) ---"),
            *older,
            SystemMessage(content="--- 최근 대화 (원본 유지) ---"),
            *recent,
            *sql_ctx_msg,
            SystemMessage(content="--- 사용자의 최신 질문 ---"),
            current_msg,
        ]

        structured_llm = llm.with_structured_output(ConversationManagerOutput)
        result = await asyncio.wait_for(
            structured_llm.ainvoke(compress_messages),
            timeout=CM_TIMEOUT_SECONDS,
        )

        summary = result.summary.strip()
        resolved_text = result.resolved_query.strip() or original_query

        # compressed_messages 조립: 요약 + 최근 3턴 + resolved query
        compressed = [
            SystemMessage(content=f"[이전 대화 요약] {summary}"),
            *recent,
            HumanMessage(content=resolved_text),
        ]

        total_before = len(messages)
        total_after = len(compressed)
        LOGGER.info(
            f"✅ Compressed: {total_before} → {total_after} msgs, "
            f"resolved: '{resolved_text[:80]}...'"
        )

        return {
            "resolved_query": resolved_text,
            "compressed_messages": compressed,
            "messages": [AIMessage(content=resolved_text)],
        }

    except Exception as e:
        LOGGER.error(f"❌ Compress failed, fallback to recent-only: {e}")
        # 폴백: 최근 3턴 + 원본 질문 (이전 히스토리 버림 — 토큰 초과보다 안전)
        fallback = list(recent) + [current_msg]
        return {
            "resolved_query": original_query,
            "compressed_messages": fallback,
            "messages": [AIMessage(content=original_query)],
        }
