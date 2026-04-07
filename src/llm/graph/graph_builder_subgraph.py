"""Subgraph 패턴 — 분석+검증 루프를 서브그래프로 캡슐화

기존 그래프:
  supervisor → mma_analysis  ─┐
             → fighter_comparison ─┤→ critic → (재시도 or 통과)
                                                → text_response
                                                → visualization

서브그래프 적용 후:
  supervisor → [analysis_subgraph] → text_response
                  내부:                → visualization
                  mma_analysis ─┐
                  fighter_comparison ─┤→ critic → (재시도 or 통과)

메인 그래프에서는 분석+검증 전체가 "analysis" 하나의 노드로 보임.
retry 로직이 서브그래프 내부에 캡슐화됨.
"""
from functools import partial

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from llm.graph.state_subgraph import MainState, AnalysisState
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

MAX_RETRIES = 3


# =============================================================================
# 1. 분석 서브그래프 — 자체 State, 자체 에지, 자체 retry 로직
# =============================================================================

def _analysis_fan_out(state: AnalysisState) -> list[Send]:
    """서브그래프 진입 시 active_agents에 따라 분석 노드 분기"""
    active_agents = state.get("active_agents", ["mma_analysis"])
    return [Send(agent, state) for agent in active_agents]


def _critic_route_internal(state: AnalysisState) -> list[Send] | str:
    """서브그래프 내부 critic 라우팅

    기존 graph_builder.py의 critic_route와 동일하지만,
    통과 시 text_response로 보내지 않고 END로 빠짐.
    → 서브그래프가 종료되면 메인 그래프가 다음 노드를 결정.
    """
    if state.get("critic_passed", False):
        # 통과 → 서브그래프 종료, 메인 그래프로 복귀
        return END

    if state.get("retry_count", 0) >= MAX_RETRIES:
        # 3회 소진 → 서브그래프 종료 (critic_node에서 이미 에러 설정)
        return END

    # 재시도 → 서브그래프 내부에서 분석 노드 재실행
    active_agents = state.get("active_agents", [])
    if not active_agents:
        return END
    return [Send(agent, state) for agent in active_agents]


def build_analysis_subgraph(main_llm, sub_llm):
    """분석+검증 서브그래프 빌드

    AnalysisState만 사용 — messages, final_response 등 불필요한 필드 없음.

    흐름:
      START → fan_out → mma_analysis ─┐
                       → fighter_comparison ─┤→ critic → END (통과)
                                                      → 재시도 (fan_out으로 돌아감)
                                                      → END (3회 소진)
    """
    graph = StateGraph(AnalysisState)

    # 노드 등록
    graph.add_node("mma_analysis", partial(mma_analysis_node, llm=main_llm))
    graph.add_node("fighter_comparison", partial(fighter_comparison_node, llm=main_llm))
    graph.add_node("critic", partial(critic_node, llm=sub_llm))

    # fan-in: 분석 → critic
    graph.add_edge("mma_analysis", "critic")
    graph.add_edge("fighter_comparison", "critic")

    # 진입: active_agents에 따라 분기
    graph.add_conditional_edges(
        START, _analysis_fan_out,
        ["mma_analysis", "fighter_comparison"],
    )

    # critic 이후: 통과/재시도/소진 → 서브그래프 내부에서 처리
    graph.add_conditional_edges(
        "critic", _critic_route_internal,
        ["mma_analysis", "fighter_comparison", END],
    )

    return graph.compile()


# =============================================================================
# 2. 메인 그래프 — 서브그래프를 하나의 노드로 사용
# =============================================================================

def _supervisor_dispatch(state: MainState) -> list[Send]:
    """메인 그래프 라우팅 — 기존과 동일"""
    route = state.get("route", "mma_analysis")

    if route == "general":
        return [Send("direct_response", state)]

    # general이 아닌 모든 경우 → analysis 서브그래프로
    return [Send("analysis", state)]


def _post_analysis_route(state: MainState) -> list[Send] | str:
    """서브그래프 완료 후 라우팅

    기존에는 critic_route가 text_response/visualization을 결정했지만,
    이제 서브그래프가 critic을 내부 처리했으므로 메인에서는
    critic_passed 결과만 보고 다음 단계를 결정.
    """
    if not state.get("critic_passed", False):
        # 서브그래프에서 retry 소진 → END
        return END

    sends = [Send("text_response", state)]
    if state.get("needs_visualization", False):
        sends.append(Send("visualization", state))
    return sends


def build_mma_graph_subgraph(main_llm, sub_llm=None):
    """서브그래프 패턴 적용 메인 그래프

    기존 build_mma_graph와 비교:

    [기존]
      START → CM → supervisor → mma_analysis  ─┐
                               → fighter_comparison ─┤→ critic → text_response
                                                              → visualization
                                                              → 재시도
                               → direct_response → END

    [서브그래프 적용]
      START → CM → supervisor → [analysis]  → text_response
                                             → visualization
                               → direct_response → END

    메인 그래프가 단순해짐:
    - 8개 노드 → 5개 노드
    - critic/retry 로직이 서브그래프 내부로 캡슐화
    - 메인에서는 "분석 요청 → 검증된 결과 수신"만 관심
    """
    if sub_llm is None:
        sub_llm = main_llm

    # 서브그래프 컴파일
    analysis_compiled = build_analysis_subgraph(main_llm, sub_llm)

    # 메인 그래프
    graph = StateGraph(MainState)

    # ── 노드 등록 ──
    graph.add_node("conversation_manager", partial(conversation_manager_node, llm=sub_llm))
    graph.add_node("supervisor", partial(supervisor_node, llm=sub_llm))
    graph.add_node("direct_response", partial(direct_response_node, llm=sub_llm))
    graph.add_node("analysis", analysis_compiled)  # 서브그래프를 노드로 등록
    graph.add_node("text_response", partial(text_response_node, llm=main_llm))
    graph.add_node("visualization", partial(visualize_node, llm=sub_llm))

    # ── 순차 에지 ──
    graph.add_edge(START, "conversation_manager")
    graph.add_edge("conversation_manager", "supervisor")

    # ── 터미널 에지 ──
    graph.add_edge("direct_response", END)
    graph.add_edge("text_response", END)
    graph.add_edge("visualization", END)

    # ── 라우팅 ──
    # supervisor → direct_response 또는 analysis 서브그래프
    graph.add_conditional_edges(
        "supervisor", _supervisor_dispatch,
        ["direct_response", "analysis"],
    )

    # analysis 서브그래프 완료 후 → text_response + visualization 또는 END
    graph.add_conditional_edges(
        "analysis", _post_analysis_route,
        ["text_response", "visualization", END],
    )

    compiled = graph.compile()
    LOGGER.info("MMA Subgraph 패턴 compiled successfully")

    return compiled
