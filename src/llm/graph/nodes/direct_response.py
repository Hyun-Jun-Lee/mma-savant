"""일반 질문 응답 노드 - DB 조회 없이 LLM이 직접 응답"""
from langchain_core.messages import SystemMessage, AIMessage

from llm.graph.state import MMAGraphState
from llm.graph.prompts import DIRECT_RESPONSE_PROMPT
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


async def direct_response_node(state: MMAGraphState, llm) -> dict:
    """
    일반 질문에 대한 직접 응답 노드

    MMA 지식 질문, 인사, MMA 외 질문 거절 등을 처리.
    SQL 조회 없이 LLM이 직접 텍스트 응답을 생성.
    """
    messages = state["messages"]

    try:
        response_messages = [
            SystemMessage(content=DIRECT_RESPONSE_PROMPT),
            *messages  # service 레이어에서 이미 10개로 제한됨
        ]

        response = await llm.ainvoke(response_messages)
        response_text = response.content if hasattr(response, 'content') else str(response)

        LOGGER.info(f"✅ Direct response generated: {len(response_text)} chars")

        return {
            "final_response": response_text,
            "response_mode": "text",
            "visualization_type": "text_summary",
            "visualization_data": {
                "title": "",
                "content": response_text,
            },
            "insights": [],
            "messages": [AIMessage(content=response_text)],
        }

    except Exception as e:
        LOGGER.error(f"❌ Direct response failed: {e}")
        error_msg = "죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요."
        return {
            "final_response": error_msg,
            "response_mode": "text",
            "visualization_type": "text_summary",
            "visualization_data": {"title": "", "content": error_msg},
            "insights": [],
            "messages": [AIMessage(content=error_msg)],
        }
