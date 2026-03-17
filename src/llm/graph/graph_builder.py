"""MMA StateGraph 조립 및 컴파일"""
from functools import partial

from langgraph.graph import StateGraph, START, END

from llm.graph.state import MMAGraphState
from llm.graph.nodes import (
    intent_classifier_node,
    direct_response_node,
    sql_agent_node,
    context_enricher_node,
    result_analyzer_node,
    visualize_node,
    text_response_node,
)
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


VALID_INTENTS = {"general", "sql_needed", "followup"}
VALID_RESPONSE_MODES = {"visualization", "text"}


def route_by_intent(state: MMAGraphState) -> str:
    """의도 분류 결과에 따른 라우팅"""
    intent = state.get("intent")
    if intent not in VALID_INTENTS:
        LOGGER.error(f"❌ Invalid intent: {intent!r}, expected one of {VALID_INTENTS}")
        raise ValueError(f"Invalid intent: {intent!r}")
    LOGGER.info(f"🔀 Routing by intent: {intent}")
    return intent


def route_by_response_mode(state: MMAGraphState) -> str:
    """시각화 적합성 판단 결과에 따른 라우팅"""
    mode = state.get("response_mode")
    if mode not in VALID_RESPONSE_MODES:
        LOGGER.error(f"❌ Invalid response_mode: {mode!r}, expected one of {VALID_RESPONSE_MODES}")
        raise ValueError(f"Invalid response_mode: {mode!r}")
    LOGGER.info(f"🔀 Routing by response_mode: {mode}")
    return mode


def build_mma_graph(llm):
    """
    MMA StateGraph 조립 및 컴파일

    Args:
        llm: LangChain LLM 인스턴스 (노드에서 사용)

    Returns:
        CompiledGraph: 컴파일된 그래프
    """
    graph = StateGraph(MMAGraphState)

    # 노드 등록 (llm을 partial로 바인딩)
    graph.add_node("intent_classifier", partial(intent_classifier_node, llm=llm))
    graph.add_node("direct_response", partial(direct_response_node, llm=llm))
    graph.add_node("sql_agent", partial(sql_agent_node, llm=llm))
    graph.add_node("context_enricher", partial(context_enricher_node, llm=llm))
    graph.add_node("result_analyzer", result_analyzer_node)  # 규칙 기반, LLM 불필요
    graph.add_node("visualize", partial(visualize_node, llm=llm))
    graph.add_node("text_response", partial(text_response_node, llm=llm))

    # 에지 정의
    graph.add_edge(START, "intent_classifier")

    graph.add_conditional_edges("intent_classifier", route_by_intent, {
        "general": "direct_response",
        "sql_needed": "sql_agent",
        "followup": "context_enricher",
    })

    graph.add_edge("context_enricher", "sql_agent")
    graph.add_edge("sql_agent", "result_analyzer")

    graph.add_conditional_edges("result_analyzer", route_by_response_mode, {
        "visualization": "visualize",
        "text": "text_response",
    })

    graph.add_edge("direct_response", END)
    graph.add_edge("visualize", END)
    graph.add_edge("text_response", END)

    compiled = graph.compile()
    LOGGER.info("✅ MMA StateGraph compiled successfully")

    return compiled
