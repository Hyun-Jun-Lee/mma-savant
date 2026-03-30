"""MMA Multi-Agent Graph State 정의"""
from typing import TypedDict, Annotated, Literal, Optional

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentResult(TypedDict):
    """각 에이전트의 통합 출력 스키마"""
    agent_name: str                  # "mma_analysis" | "fighter_comparison" | "enrichment"
    query: str                       # 실행한 SQL 쿼리
    data: list[dict]                 # SQL 결과 데이터
    columns: list[str]               # 결과 컬럼명
    row_count: int                   # 결과 행 수
    reasoning: str                   # 에이전트의 자연어 분석 (텍스트 응답 재사용 가능)


def reduce_agent_results(
    existing: list[AgentResult],
    new: list[AgentResult],
) -> list[AgentResult]:
    """agent_results 커스텀 reducer

    - 빈 리스트 할당(=[]) -> 초기화 (Critic 재시도 전 리셋용)
    - 그 외 -> 기존 결과에 추가 (병렬 에이전트 합산)
    """
    if not new:
        return []
    return existing + new


def _error_agent_result(agent_name: str, error: str) -> AgentResult:
    """에러 발생 시 AgentResult 생성 헬퍼"""
    return {
        "agent_name": agent_name,
        "query": "",
        "data": [],
        "columns": [],
        "row_count": 0,
        "reasoning": error,
    }


class MainState(TypedDict):
    """멀티 에이전트 그래프의 공유 상태"""

    # 대화 관리
    messages: Annotated[list[BaseMessage], add_messages]
    compressed_messages: list[BaseMessage]  # 압축된 히스토리 (downstream 에이전트용)
    resolved_query: str              # Conversation Manager 출력
    sql_context: list[dict]          # 이전 턴 SQL 결과 (conversation_manager 전용)

    # 라우팅
    route: Literal["general", "mma_analysis", "fighter_comparison", "complex"]
    active_agents: list[str]         # Supervisor가 결정한 활성 에이전트

    # 분석 결과 (커스텀 reducer: 병렬 합산 + 재시도 시 초기화)
    agent_results: Annotated[list[AgentResult], reduce_agent_results]

    # 검증
    critic_passed: bool
    critic_feedback: Optional[str]
    retry_count: int                 # Critic이 실패 반환 시 +1, 최대 3
    needs_visualization: bool        # Critic이 판단한 시각화 필요 여부

    # 출력
    final_response: str              # 텍스트 응답 (항상 존재)
    visualization_type: Optional[str]   # 시각화 타입 (조건부)
    visualization_data: Optional[dict]  # 시각화 데이터 (조건부)
    insights: Optional[list[str]]       # 차트 인사이트 (시각화 시에만)

    # 메타데이터
    user_id: int
    conversation_id: int
