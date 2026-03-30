"""Fighter 비교 에이전트 노드 — 다중 선수 비교 분석"""
import asyncio
import json

from langgraph.prebuilt import create_react_agent
from langgraph.errors import GraphRecursionError
from langchain_core.messages import HumanMessage

from llm.graph.state import MainState, _error_agent_result
from llm.graph.nodes.mma_analysis import (
    _extract_sql_result,
    _extract_reasoning,
)
from llm.tools.sql_tool import create_sql_tool
from llm.prompts import get_fighter_comparison_prompt
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

FC_AGENT_TIMEOUT_SECONDS = 30
FC_AGENT_RECURSION_LIMIT = 10


def _build_comparison_agent(llm):
    """Fighter 비교 SQL 에이전트 생성"""
    tools = [create_sql_tool()]
    system_prompt = get_fighter_comparison_prompt()
    return create_react_agent(model=llm, tools=tools, prompt=system_prompt)


async def fighter_comparison_node(state: MainState, llm) -> dict:
    """
    Fighter 비교 에이전트 노드

    MMA 분석과 동일한 구조로 create_react_agent를 사용하되,
    비교 전용 프롬프트로 다중 선수 비교에 특화.
    """
    messages = state.get("compressed_messages") or state.get("messages", [])
    critic_feedback = state.get("critic_feedback")

    # Critic 재시도 시 피드백을 메시지에 추가
    if critic_feedback:
        feedback_msg = HumanMessage(
            content=f"[이전 시도 피드백] {critic_feedback}\n위 피드백을 반영하여 쿼리를 수정해주세요."
        )
        messages = list(messages) + [feedback_msg]

    try:
        agent = _build_comparison_agent(llm)

        result = await asyncio.wait_for(
            agent.ainvoke(
                {"messages": messages},
                config={"recursion_limit": FC_AGENT_RECURSION_LIMIT},
            ),
            timeout=FC_AGENT_TIMEOUT_SECONDS,
        )

        agent_messages = result.get("messages", [])
        sql_result = _extract_sql_result(agent_messages)
        reasoning = _extract_reasoning(agent_messages)

        data = sql_result.get("data", [])
        columns = sql_result.get("columns", [])
        row_count = sql_result.get("row_count", 0)

        LOGGER.info(
            f"✅ Fighter Comparison completed: success={sql_result.get('success')}, "
            f"rows={row_count}"
        )

        return {
            "agent_results": [{
                "agent_name": "fighter_comparison",
                "query": sql_result.get("query", ""),
                "data": data,
                "columns": columns,
                "row_count": row_count,
                "reasoning": reasoning,
            }],
        }

    except GraphRecursionError:
        LOGGER.error(f"❌ Fighter Comparison recursion limit ({FC_AGENT_RECURSION_LIMIT})")
        return {
            "agent_results": [_error_agent_result(
                "fighter_comparison",
                "비교 쿼리 생성 과정이 너무 복잡합니다. 질문을 더 구체적으로 바꿔주세요.",
            )],
        }

    except asyncio.TimeoutError:
        LOGGER.error(f"❌ Fighter Comparison timed out ({FC_AGENT_TIMEOUT_SECONDS}s)")
        return {
            "agent_results": [_error_agent_result(
                "fighter_comparison",
                f"비교 처리 시간이 {FC_AGENT_TIMEOUT_SECONDS}초를 초과했습니다.",
            )],
        }

    except Exception as e:
        LOGGER.error(f"❌ Fighter Comparison failed: {e}")
        return {
            "agent_results": [_error_agent_result("fighter_comparison", str(e))],
        }
