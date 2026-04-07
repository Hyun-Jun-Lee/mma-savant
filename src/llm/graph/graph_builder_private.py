"""Private State 패턴 — 그래프 빌더

그래프 구조(에지, 라우팅)는 기존과 완전히 동일.
차이점: 노드 함수가 OverallState 대신 노드별 Input 스키마를 받음.

비교 포인트:
- graph_builder.py와 이 파일의 build 함수는 구조가 같음
- 변경은 노드 함수 쪽에서 발생 (타입 힌트만 변경)
"""
from functools import partial

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from llm.graph.state_private import OverallState
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


# =============================================================================
# 라우팅 함수 — 기존과 동일 (OverallState 사용)
# =============================================================================

def supervisor_dispatch(state: OverallState) -> list[Send]:
    route = state.get("route", "mma_analysis")

    if route == "general":
        return [Send("direct_response", state)]

    active_agents = state.get("active_agents", ["mma_analysis"])
    return [Send(agent, state) for agent in active_agents]


def critic_route(state: OverallState) -> list[Send] | str:
    if state.get("critic_passed", False):
        sends = [Send("text_response", state)]
        if state.get("needs_visualization", False):
            sends.append(Send("visualization", state))
        return sends

    if state.get("retry_count", 0) >= 3:
        return END

    active_agents = state.get("active_agents", [])
    if not active_agents:
        return END
    return [Send(agent, state) for agent in active_agents]


# =============================================================================
# 노드 함수 예시 — Private State 적용
#
# 기존: async def critic_node(state: MainState, llm) -> dict
# 변경: async def critic_node(state: CriticInput, llm) -> CriticOutput
#
# LangGraph가 OverallState에서 CriticInput에 해당하는 필드만 추출하여 전달.
# 노드는 자신이 선언한 필드 외에는 접근 불가.
# =============================================================================

# 실제 노드 함수는 nodes/ 디렉토리에 있으므로 여기서는 import만 표시.
# 아래는 노드 함수의 시그니처 변경 예시:
#
# [기존]
# async def conversation_manager_node(state: MainState, llm) -> dict:
#     messages = state.get("messages", [])          # 16개 필드 중 아무거나 접근 가능
#     visualization_type = state.get("visualization_type")  # 불필요한 접근도 가능
#
# [Private State 적용]
# async def conversation_manager_node(state: ConversationManagerInput, llm) -> ConversationManagerOutput:
#     messages = state["messages"]                  # 5개 필드만 접근 가능
#     visualization_type = state["visualization_type"]  # KeyError — 접근 불가


# 데모용 stub (실제로는 기존 nodes 모듈의 함수를 타입만 변경)
from llm.graph.state_private import (
    ConversationManagerInput, ConversationManagerOutput,
    SupervisorInput, SupervisorOutput,
    DirectResponseInput,
    MmaAnalysisInput,
    FighterComparisonInput,
    CriticInput, CriticOutput,
    TextResponseInput, TextResponseOutput,
    VisualizationInput, VisualizationOutput,
)


async def _example_critic_node(state: CriticInput, llm) -> CriticOutput:
    """critic 노드 — Private State 적용 예시

    state에는 agent_results, resolved_query, retry_count 3개만 존재.
    messages, route, visualization_type 등은 보이지 않음.
    """
    agent_results = state["agent_results"]     # OK
    resolved_query = state["resolved_query"]   # OK
    retry_count = state["retry_count"]         # OK
    # route = state["route"]                   # KeyError — 접근 불가

    # ... 검증 로직 ...

    return {
        "critic_passed": True,
        "critic_feedback": None,
        "retry_count": retry_count,
        "needs_visualization": False,
        "agent_results": agent_results,
    }


# =============================================================================
# 그래프 빌더 — 구조는 기존과 100% 동일
# =============================================================================

def build_mma_graph_private(main_llm, sub_llm=None):
    """Private State 패턴 적용 그래프

    기존 build_mma_graph와 비교:
    - StateGraph(MainState) → StateGraph(OverallState)  ← 이름만 변경
    - 노드 등록, 에지, 라우팅 모두 동일
    - 차이는 노드 함수 내부의 타입 힌트뿐
    """
    if sub_llm is None:
        sub_llm = main_llm

    # OverallState = 기존 MainState와 필드 동일
    graph = StateGraph(OverallState)

    # 노드 등록 — 기존과 동일 (실제로는 타입 힌트가 변경된 노드 함수 사용)
    # graph.add_node("conversation_manager", partial(conversation_manager_node, llm=sub_llm))
    # graph.add_node("supervisor", partial(supervisor_node, llm=sub_llm))
    # graph.add_node("direct_response", partial(direct_response_node, llm=sub_llm))
    # graph.add_node("mma_analysis", partial(mma_analysis_node, llm=main_llm))
    # graph.add_node("fighter_comparison", partial(fighter_comparison_node, llm=main_llm))
    # graph.add_node("critic", partial(critic_node, llm=sub_llm))
    # graph.add_node("text_response", partial(text_response_node, llm=main_llm))
    # graph.add_node("visualization", partial(visualize_node, llm=sub_llm))

    # 에지 — 기존과 완전히 동일
    # graph.add_edge(START, "conversation_manager")
    # graph.add_edge("conversation_manager", "supervisor")
    # graph.add_edge("mma_analysis", "critic")
    # graph.add_edge("fighter_comparison", "critic")
    # graph.add_edge("direct_response", END)
    # graph.add_edge("text_response", END)
    # graph.add_edge("visualization", END)

    # 라우팅 — 기존과 완전히 동일
    # graph.add_conditional_edges(
    #     "supervisor", supervisor_dispatch,
    #     ["direct_response", "mma_analysis", "fighter_comparison"],
    # )
    # graph.add_conditional_edges(
    #     "critic", critic_route,
    #     ["text_response", "visualization", "mma_analysis", "fighter_comparison", END],
    # )

    # compiled = graph.compile()
    # return compiled

    LOGGER.info("Private State 패턴: 그래프 구조 동일, 노드 타입 힌트만 변경")
