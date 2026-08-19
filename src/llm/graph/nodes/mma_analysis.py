"""MMA 분석 에이전트 노드 — SQL 기반 종합 MMA 데이터 분석"""
import asyncio
import json

from langgraph.errors import GraphRecursionError

from llm.graph.react_agent import build_react_agent
from langchain_core.messages import HumanMessage

from llm.graph.state import MainState, _error_agent_result
from llm.tools.sql_tool import execute_raw_sql_query
from llm.prompts import get_phase1_prompt
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

MMA_AGENT_TIMEOUT_SECONDS = 30
MMA_AGENT_RECURSION_LIMIT = 10


def _empty_sql_result() -> dict:
    return {
        "query": "", "success": False, "data": [],
        "columns": [], "row_count": 0,
        "error": "No SQL result found in agent output",
    }


def _extract_sql_results(messages) -> list[dict]:
    """에이전트 출력 메시지에서 성공한 SQL 결과들을 실행 순서대로 추출."""
    parsed_results = []
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "tool":
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict) and "success" in parsed:
                    parsed_results.append(parsed)
            except (json.JSONDecodeError, TypeError):
                continue

    successful_results = [result for result in parsed_results if result.get("success") is True]
    if successful_results:
        return successful_results
    if parsed_results:
        return [parsed_results[-1]]
    return [_empty_sql_result()]


def _extract_sql_result(messages) -> dict:
    """에이전트 출력 메시지에서 마지막 성공 SQL 결과를 추출 (하위 호환용)."""
    sql_results = _extract_sql_results(messages)
    return sql_results[-1] if sql_results else _empty_sql_result()


def _extract_reasoning(messages) -> str:
    """에이전트 출력에서 최종 AI reasoning 추출"""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            return msg.content
    return ""


def _build_agent(llm):
    """MMA 분석 SQL 에이전트 생성"""
    tools = [execute_raw_sql_query]
    system_prompt = get_phase1_prompt()
    return build_react_agent(model=llm, tools=tools, prompt=system_prompt)


def _build_agent_results(agent_name: str, sql_results: list[dict], reasoning: str) -> list[dict]:
    """SQL result set마다 downstream용 AgentResult를 생성."""
    multiple_results = len(sql_results) > 1
    agent_results = []

    for idx, sql_result in enumerate(sql_results, start=1):
        label = f"{agent_name}[{idx}]" if multiple_results else agent_name
        agent_results.append({
            "agent_name": label,
            "query": sql_result.get("query", ""),
            "data": sql_result.get("data", []),
            "columns": sql_result.get("columns", []),
            "row_count": sql_result.get("row_count", 0),
            "reasoning": reasoning,
            "success": sql_result.get("success", False),
            "error": sql_result.get("error"),
        })

    return agent_results


async def mma_analysis_node(state: MainState, llm) -> dict:
    """
    MMA 분석 에이전트 노드

    build_react_agent로 SQL 쿼리를 실행하고 결과를 AgentResult로 반환.
    Critic 피드백이 있으면 메시지에 포함하여 재실행.
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
        agent = _build_agent(llm)

        result = await asyncio.wait_for(
            agent.ainvoke(
                {"messages": messages},
                config={"recursion_limit": MMA_AGENT_RECURSION_LIMIT},
            ),
            timeout=MMA_AGENT_TIMEOUT_SECONDS,
        )

        agent_messages = result.get("messages", [])
        sql_results = _extract_sql_results(agent_messages)
        reasoning = _extract_reasoning(agent_messages)

        total_rows = sum(sql_result.get("row_count", 0) for sql_result in sql_results)
        all_successful = all(sql_result.get("success") is True for sql_result in sql_results)

        LOGGER.info(
            f"✅ MMA Analysis completed: success={all_successful}, "
            f"result_sets={len(sql_results)}, rows={total_rows}"
        )

        return {
            "agent_results": _build_agent_results("mma_analysis", sql_results, reasoning),
        }

    except GraphRecursionError:
        LOGGER.error(f"❌ MMA Analysis recursion limit ({MMA_AGENT_RECURSION_LIMIT})")
        return {
            "agent_results": [_error_agent_result(
                "mma_analysis",
                "쿼리 생성 과정이 너무 복잡합니다. 질문을 더 구체적으로 바꿔주세요.",
            )],
        }

    except asyncio.TimeoutError:
        LOGGER.error(f"❌ MMA Analysis timed out ({MMA_AGENT_TIMEOUT_SECONDS}s)")
        return {
            "agent_results": [_error_agent_result(
                "mma_analysis",
                f"처리 시간이 {MMA_AGENT_TIMEOUT_SECONDS}초를 초과했습니다.",
            )],
        }

    except Exception as e:
        LOGGER.error(f"❌ MMA Analysis failed: {e}")
        return {
            "agent_results": [_error_agent_result("mma_analysis", str(e))],
        }
