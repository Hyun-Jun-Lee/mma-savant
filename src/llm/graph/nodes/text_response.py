"""텍스트 분석 응답 노드 — agent_results를 텍스트로 분석"""
import asyncio
import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm.graph.state import MainState
from llm.graph.prompts import TEXT_RESPONSE_PROMPT
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

TR_TIMEOUT_SECONDS = 15


def _build_text_input(resolved_query: str, agent_results: list) -> str:
    """텍스트 분석 LLM 호출용 입력 데이터 구성"""
    parts = [f"## 사용자 질문: {resolved_query}\n"]

    for result in agent_results:
        agent_name = result.get("agent_name", "unknown")
        parts.append(f"## [{agent_name}] SQL 쿼리 결과")
        parts.append(f"- 쿼리: {result.get('query', '')}")
        parts.append(f"- 행 수: {result.get('row_count', 0)}")
        parts.append(f"- 컬럼: {', '.join(result.get('columns', []))}")
        parts.append(f"\n### 데이터:")
        parts.append(json.dumps(result.get("data", []), ensure_ascii=False, default=str))
        parts.append("")

    return "\n".join(parts)


async def text_response_node(state: MainState, llm) -> dict:
    """
    텍스트 분석 응답 노드

    SQL agent reasoning은 private execution context이므로 사용자 응답으로 재사용하지 않는다.
    단일/복수 에이전트 모두 SQL 결과를 response LLM으로 전달하여 최종 응답을 생성한다.
    """
    agent_results = state.get("agent_results", [])
    resolved_query = state.get("resolved_query", "")

    try:
        input_text = _build_text_input(resolved_query, agent_results)
        response = await asyncio.wait_for(
            llm.ainvoke([
                SystemMessage(content=TEXT_RESPONSE_PROMPT),
                HumanMessage(content=input_text),
            ]),
            timeout=TR_TIMEOUT_SECONDS,
        )
        content = response.content if hasattr(response, "content") else str(response)

        LOGGER.info(f"✅ Text response generated: {len(content)} chars")

        return {
            "final_response": content,
            "messages": [AIMessage(content=content)],
        }

    except Exception as e:
        LOGGER.error(f"❌ Text response failed: {e}")
        fallback = "응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

        return {
            "final_response": fallback,
            "messages": [AIMessage(content=fallback)],
        }
