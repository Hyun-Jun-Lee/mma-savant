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

    단일 에이전트: reasoning 재사용 (LLM 호출 생략)
    복수 에이전트: 결과 통합하여 LLM으로 텍스트 생성
    """
    agent_results = state.get("agent_results", [])
    resolved_query = state.get("resolved_query", "")

    try:
        if len(agent_results) == 1 and agent_results[0].get("reasoning"):
            # 단일 에이전트 → reasoning 재사용 (LLM 호출 생략)
            LOGGER.info("♻️ Reusing agent reasoning, skipping LLM call")
            content = agent_results[0]["reasoning"]
        else:
            # 복수 에이전트 또는 reasoning 없음 → LLM 호출
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
        # 폴백: reasoning이 있으면 그대로 사용
        fallback = ""
        for result in agent_results:
            if result.get("reasoning"):
                fallback = result["reasoning"]
                break
        if not fallback:
            fallback = "데이터 분석 중 오류가 발생했습니다."

        return {
            "final_response": fallback,
            "messages": [AIMessage(content=fallback)],
        }
