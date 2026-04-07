"""MMA Multi-Agent StateGraph 조립 및 컴파일"""
from functools import partial

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from llm.graph.state import MainState
from llm.graph.nodes import (
    conversation_manager_node,
    supervisor_node,
    direct_response_node,
    mma_analysis_node,
    fighter_comparison_node,
    critic_node,
    text_response_node,
    visualize_node,
)
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


# =============================================================================
# 라우팅 함수
# =============================================================================

def supervisor_dispatch(state: MainState) -> list[Send]:
    """Supervisor 라우팅 결과에 따라 에이전트를 동적으로 활성화

    Returns:
        list[Send] — general이면 direct_response, 그 외 active_agents를 Send()
    """
    route = state.get("route", "mma_analysis")

    if route == "general":
        return [Send("direct_response", state)]

    # 단일 또는 복수 에이전트를 동적으로 활성화
    active_agents = state.get("active_agents", ["mma_analysis"])
    return [Send(agent, state) for agent in active_agents]


def critic_route(state: MainState) -> list[Send] | str:
    """Critic 결과에 따른 3방향 라우팅

    Returns:
        list[Send] — 통과: 텍스트(항상) + 시각화(조건부) 병렬 Send
        list[Send] — 재시도: active_agents 전체 재실행 Send
        END — 3회 소진 또는 에러 응답 설정됨: 그래프 종료
    """
    if state.get("critic_passed", False):
        # 통과 → 텍스트(항상) + 시각화(조건부) 병렬 실행
        sends = [Send("text_response", state)]
        if state.get("needs_visualization", False):
            sends.append(Send("visualization", state))
        return sends

    if state.get("retry_count", 0) >= 3:
        # 3회 소진 → END (critic_node에서 이미 final_response 설정됨)
        return END

    # 재시도 → 원래 활성화된 에이전트 전체를 Send()로 재실행
    active_agents = state.get("active_agents", [])
    if not active_agents:
        return END
    return [Send(agent, state) for agent in active_agents]


# =============================================================================
# 그래프 빌더
# =============================================================================

def build_mma_graph(main_llm, sub_llm=None):
    """
    MMA Multi-Agent StateGraph 조립 및 컴파일

    Args:
        main_llm: MAIN_MODEL LLM (MMA 분석, Fighter 비교, 텍스트 응답)
        sub_llm: SUB_MODEL LLM (CM, Supervisor, Critic, 시각화, direct_response)
                 None이면 main_llm을 모든 노드에 사용 (하위 호환)

    Returns:
        CompiledGraph: 컴파일된 그래프
    """
    if sub_llm is None:
        sub_llm = main_llm

    graph = StateGraph(MainState)

    # ── 노드 등록 (partial로 LLM 바인딩) ──
    graph.add_node("conversation_manager", partial(conversation_manager_node, llm=sub_llm))
    graph.add_node("supervisor", partial(supervisor_node, llm=sub_llm))
    graph.add_node("direct_response", partial(direct_response_node, llm=sub_llm))
    graph.add_node("mma_analysis", partial(mma_analysis_node, llm=main_llm))
    graph.add_node("fighter_comparison", partial(fighter_comparison_node, llm=main_llm))
    graph.add_node("critic", partial(critic_node, llm=sub_llm))
    graph.add_node("text_response", partial(text_response_node, llm=main_llm))
    graph.add_node("visualization", partial(visualize_node, llm=sub_llm))

    # ── 순차 에지 ──
    graph.add_edge(START, "conversation_manager")
    graph.add_edge("conversation_manager", "supervisor")

    # ── fan-in 에지: 분석 에이전트들 → critic ──
    graph.add_edge("mma_analysis", "critic")
    graph.add_edge("fighter_comparison", "critic")

    # ── 터미널 에지 ──
    graph.add_edge("direct_response", END)
    graph.add_edge("text_response", END)
    graph.add_edge("visualization", END)

    # ── 동적 라우팅 (Send() 기반, path_map으로 가능한 타겟 노드 명시) ──
    graph.add_conditional_edges(
        "supervisor", supervisor_dispatch,
        ["direct_response", "mma_analysis", "fighter_comparison"],
    )
    graph.add_conditional_edges(
        "critic", critic_route,
        ["text_response", "visualization", "mma_analysis", "fighter_comparison", END],
    )

    compiled = graph.compile()
    LOGGER.info("✅ MMA Multi-Agent StateGraph compiled successfully")

    return compiled
