"""Supervisor 노드 — LLM 기반 질문 라우팅"""
import asyncio

from langchain_core.messages import SystemMessage, HumanMessage

from llm.graph.state import MainState
from llm.graph.schemas import SupervisorRouting
from llm.graph.prompts import SUPERVISOR_PROMPT
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

SV_TIMEOUT_SECONDS = 10


async def supervisor_node(state: MainState, llm) -> dict:
    """
    Supervisor 라우팅 노드

    resolved_query를 분석하여 적절한 에이전트 조합을 결정.
    structured output으로 정형화된 라우팅 결과를 보장.

    출력:
        route: "general" | "mma_analysis" | "fighter_comparison" | "complex"
        active_agents: 활성화할 에이전트 목록
    """
    resolved_query = state.get("resolved_query", "")

    if not resolved_query:
        LOGGER.warning("⚠️ No resolved_query, defaulting to mma_analysis")
        return {
            "route": "mma_analysis",
            "active_agents": ["mma_analysis"],
        }

    try:
        structured_llm = llm.with_structured_output(SupervisorRouting)

        result = await asyncio.wait_for(
            structured_llm.ainvoke([
                SystemMessage(content=SUPERVISOR_PROMPT),
                HumanMessage(content=resolved_query),
            ]),
            timeout=SV_TIMEOUT_SECONDS,
        )

        route = result.route
        agents = result.agents

        # 라우팅 결과 정합성 보정
        if route == "general":
            agents = []
        elif route in ("mma_analysis", "fighter_comparison") and not agents:
            agents = [route]
        elif route == "complex" and len(agents) < 2:
            agents = ["mma_analysis", "fighter_comparison"]

        LOGGER.info(f"🔀 Supervisor routed: {route} → {agents}")

        return {
            "route": route,
            "active_agents": agents,
        }

    except Exception as e:
        LOGGER.error(f"❌ Supervisor failed: {e}")
        # 폴백: mma_analysis로 라우팅 (데이터 기반 답변이 더 안전)
        return {
            "route": "mma_analysis",
            "active_agents": ["mma_analysis"],
        }
