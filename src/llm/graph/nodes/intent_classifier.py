"""의도 분류 노드 - 사용자 질문을 general/sql_needed/followup으로 분류"""
from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage

from llm.graph.state import MMAGraphState
from llm.graph.prompts import INTENT_CLASSIFIER_PROMPT
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


class IntentClassification(BaseModel):
    """사용자 질문의 의도 분류 결과"""
    intent: Literal["general", "sql_needed", "followup"] = Field(
        description="general: DB 조회 불필요, "
                    "sql_needed: 통계/전적 등 DB 조회 필요, "
                    "followup: 이전 대화를 참조하는 후속 질문"
    )


async def intent_classifier_node(state: MMAGraphState, llm) -> dict:
    """
    의도 분류 노드

    항상 LLM을 사용하여 사용자 질문의 의도를 분류.
    structured_output으로 정형화된 분류 결과를 보장.
    """
    messages = state["messages"]
    if not messages:
        LOGGER.warning("⚠️ No messages in state")
        return {"intent": "general"}

    has_history = len(messages) > 1

    try:
        structured_llm = llm.with_structured_output(IntentClassification)

        classify_messages = [
            SystemMessage(content=INTENT_CLASSIFIER_PROMPT),
            *messages[-5:]  # 최근 5개 메시지만
        ]

        result = await structured_llm.ainvoke(classify_messages)
        LOGGER.info(f"🤖 LLM classified: {result.intent}")

        # 히스토리 없는데 followup으로 분류된 경우 보정
        if result.intent == "followup" and not has_history:
            LOGGER.info("📋 Corrected followup → sql_needed (no history)")
            return {"intent": "sql_needed"}

        # 히스토리 있는데 sql_needed로 분류된 경우 → followup으로 보정
        # context_enricher를 거쳐야 이전 맥락이 반영됨
        if result.intent == "sql_needed" and has_history:
            LOGGER.info("📋 Corrected sql_needed → followup (has history)")
            return {"intent": "followup"}

        return {"intent": result.intent}

    except Exception as e:
        LOGGER.error(f"❌ Intent classification failed: {e}")
        # 실패 시 기본값: sql_needed (데이터 기반 답변이 더 안전)
        return {"intent": "sql_needed"}
