"""Subgraph 패턴 — 분석+검증 루프를 독립 그래프로 분리

메인 그래프의 State와 분석 서브그래프의 State를 분리.
서브그래프는 자체 State, 에지, retry 로직을 캡슐화.
"""
from typing import TypedDict, Annotated, Literal, Optional

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentResult(TypedDict):
    agent_name: str
    query: str
    data: list[dict]
    columns: list[str]
    row_count: int
    reasoning: str


def reduce_agent_results(
    existing: list[AgentResult],
    new: list[AgentResult],
) -> list[AgentResult]:
    if not new:
        return []
    return existing + new


def _error_agent_result(agent_name: str, error: str) -> AgentResult:
    return {
        "agent_name": agent_name,
        "query": "",
        "data": [],
        "columns": [],
        "row_count": 0,
        "reasoning": error,
    }


# =============================================================================
# 분석 서브그래프 State — 분석+검증에 필요한 필드만
# =============================================================================

class AnalysisState(TypedDict):
    """분석 서브그래프 내부에서만 사용되는 State

    메인 그래프의 필드 중 분석에 필요한 것만 포함.
    messages, compressed_messages, final_response 등은 없음.
    """
    resolved_query: str
    active_agents: list[str]

    agent_results: Annotated[list[AgentResult], reduce_agent_results]

    critic_passed: bool
    critic_feedback: Optional[str]
    retry_count: int
    needs_visualization: bool


# =============================================================================
# 메인 그래프 State — 서브그래프를 "하나의 노드"로 취급
# =============================================================================

class MainState(TypedDict):
    """메인 그래프 State

    기존과 동일하지만, 서브그래프가 critic/retry를 내부 처리하므로
    메인 그래프 관점에서는 "analysis 노드에 넣으면 검증된 결과가 나온다"
    """
    # 대화 관리
    messages: Annotated[list[BaseMessage], add_messages]
    compressed_messages: list[BaseMessage]
    resolved_query: str
    sql_context: list[dict]

    # 라우팅
    route: Literal["general", "mma_analysis", "fighter_comparison", "complex"]
    active_agents: list[str]

    # 분석 결과 — 서브그래프가 검증 완료된 결과를 반환
    agent_results: Annotated[list[AgentResult], reduce_agent_results]

    # 서브그래프가 설정하는 플래그
    critic_passed: bool
    needs_visualization: bool

    # 출력
    final_response: str
    visualization_type: Optional[str]
    visualization_data: Optional[dict]
    insights: Optional[list[str]]

    # 메타데이터
    user_id: int
    conversation_id: int
