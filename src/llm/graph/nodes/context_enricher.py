"""컨텍스트 보강 노드 - 후속 질문을 독립 질문으로 재작성"""
from langchain_core.messages import SystemMessage, HumanMessage

from llm.graph.state import MMAGraphState
from llm.graph.prompts import CONTEXT_ENRICHER_PROMPT
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


async def context_enricher_node(state: MMAGraphState, llm) -> dict:
    """
    후속 질문 맥락 보강 노드

    대화 히스토리를 참조하여 후속 질문을 독립적인 완전한 질문으로 재작성.
    SQL 에이전트는 재작성된 질문만 받으므로 변경 불필요.
    """
    messages = state["messages"]

    try:
        enricher_messages = [
            SystemMessage(content=CONTEXT_ENRICHER_PROMPT),
            *messages  # service 레이어에서 이미 10개로 제한됨
        ]

        rewritten = await llm.ainvoke(enricher_messages)
        rewritten_text = rewritten.content if hasattr(rewritten, 'content') else str(rewritten)

        LOGGER.info(f"✅ Context enriched: '{rewritten_text[:80]}...'")

        # 재작성된 질문을 messages에 추가 (원본 대체가 아닌 보강)
        return {
            "messages": [HumanMessage(content=rewritten_text)],
        }

    except Exception as e:
        LOGGER.error(f"❌ Context enrichment failed: {e}")
        # 실패 시 원본 메시지 그대로 유지 (sql_agent가 원본으로 시도)
        return {}
