"""SQL Agent 노드 - langgraph.prebuilt.create_react_agent 기반 SQL 실행"""
import json

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from llm.graph.state import MMAGraphState
from llm.tools.sql_tool import create_sql_tool
from llm.prompts import get_phase1_prompt
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


SQL_AGENT_RECURSION_LIMIT = 10


def _build_sql_agent(llm):
    """SQL 에이전트 생성 (langgraph prebuilt)"""
    tools = [create_sql_tool()]
    system_prompt = get_phase1_prompt()

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )


def _extract_sql_result_from_messages(messages) -> dict:
    """에이전트 출력 메시지에서 SQL 결과 추출"""
    # 역순으로 메시지를 탐색하여 tool 결과 찾기
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == 'tool':
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict) and "success" in parsed:
                    return parsed
            except (json.JSONDecodeError, TypeError):
                continue

    return {
        "query": "",
        "success": False,
        "data": [],
        "columns": [],
        "row_count": 0,
        "error": "No SQL result found in agent output"
    }


async def sql_agent_node(state: MMAGraphState, llm) -> dict:
    """
    SQL Agent 노드

    langgraph.prebuilt.create_react_agent를 사용하여 SQL 쿼리를 실행.
    기존 Phase 1 로직을 대체.
    """
    messages = state["messages"]

    try:
        agent = _build_sql_agent(llm)

        # 에이전트 실행 - recursion_limit으로 무한 루프 방지
        result = await agent.ainvoke(
            {"messages": messages},
            config={"recursion_limit": SQL_AGENT_RECURSION_LIMIT},
        )

        # 에이전트 출력 메시지에서 SQL 결과 추출
        agent_messages = result.get("messages", [])
        sql_result = _extract_sql_result_from_messages(agent_messages)

        # 에이전트의 최종 응답 (AI reasoning)
        agent_reasoning = ""
        for msg in reversed(agent_messages):
            if hasattr(msg, 'type') and msg.type == 'ai' and msg.content:
                agent_reasoning = msg.content
                break

        LOGGER.info(
            f"✅ SQL Agent completed: success={sql_result.get('success')}, "
            f"rows={sql_result.get('row_count', 0)}"
        )

        return {
            "sql_result": sql_result,
            "messages": agent_messages,
        }

    except Exception as e:
        LOGGER.error(f"❌ SQL Agent failed: {e}")
        return {
            "sql_result": {
                "query": "",
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "error": str(e),
            },
        }
