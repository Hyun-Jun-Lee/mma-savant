"""Private State 패턴 — 노드별 입출력 스키마 분리

기존 MainState를 OverallState로 유지하되,
각 노드가 필요한 필드만 보도록 Input/Output TypedDict를 정의.
그래프 구조는 변경 없음. 노드 함수의 타입 힌트만 변경.
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
# OverallState — 그래프 전체의 실제 저장소 (기존 MainState와 동일)
# =============================================================================

class OverallState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    compressed_messages: list[BaseMessage]
    resolved_query: str
    sql_context: list[dict]

    route: Literal["general", "mma_analysis", "fighter_comparison", "complex"]
    active_agents: list[str]

    agent_results: Annotated[list[AgentResult], reduce_agent_results]

    critic_passed: bool
    critic_feedback: Optional[str]
    retry_count: int
    needs_visualization: bool

    final_response: str
    visualization_type: Optional[str]
    visualization_data: Optional[dict]
    insights: Optional[list[str]]

    user_id: int
    conversation_id: int


# =============================================================================
# 노드별 Input 스키마 — 각 노드가 "보는" 필드만 선언
# =============================================================================

class ConversationManagerInput(TypedDict):
    """conversation_manager가 필요한 필드만"""
    messages: list[BaseMessage]
    compressed_messages: list[BaseMessage]
    sql_context: list[dict]
    user_id: int
    conversation_id: int


class SupervisorInput(TypedDict):
    """supervisor가 필요한 필드만"""
    resolved_query: str


class DirectResponseInput(TypedDict):
    """direct_response가 필요한 필드만"""
    resolved_query: str
    compressed_messages: list[BaseMessage]


class MmaAnalysisInput(TypedDict):
    """mma_analysis가 필요한 필드만"""
    resolved_query: str
    critic_feedback: Optional[str]


class FighterComparisonInput(TypedDict):
    """fighter_comparison이 필요한 필드만"""
    resolved_query: str
    critic_feedback: Optional[str]


class CriticInput(TypedDict):
    """critic이 필요한 필드만"""
    agent_results: list[AgentResult]
    resolved_query: str
    retry_count: int


class TextResponseInput(TypedDict):
    """text_response가 필요한 필드만"""
    agent_results: list[AgentResult]
    resolved_query: str


class VisualizationInput(TypedDict):
    """visualization이 필요한 필드만"""
    agent_results: list[AgentResult]
    resolved_query: str


# =============================================================================
# 노드별 Output 스키마 — 각 노드가 "쓰는" 필드만 선언
# =============================================================================

class ConversationManagerOutput(TypedDict):
    resolved_query: str
    compressed_messages: list[BaseMessage]
    sql_context: list[dict]


class SupervisorOutput(TypedDict):
    route: Literal["general", "mma_analysis", "fighter_comparison", "complex"]
    active_agents: list[str]


class CriticOutput(TypedDict):
    critic_passed: bool
    critic_feedback: Optional[str]
    retry_count: int
    needs_visualization: bool
    agent_results: list[AgentResult]  # 재시도 시 [] 초기화용


class TextResponseOutput(TypedDict):
    final_response: str


class VisualizationOutput(TypedDict):
    visualization_type: Optional[str]
    visualization_data: Optional[dict]
    insights: Optional[list[str]]
