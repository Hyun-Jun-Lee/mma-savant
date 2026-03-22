"""텍스트 분석 응답 노드 - SQL 결과를 텍스트로 분석"""
import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm.graph.state import MMAGraphState
from llm.graph.prompts import TEXT_RESPONSE_PROMPT
from llm.graph.schemas import TextSummaryOutput
from llm.graph.nodes.visualize import _build_data_summary
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


def _build_text_input(state: MMAGraphState) -> str:
    """텍스트 분석 LLM 호출용 입력 데이터 구성"""
    sql_result = state.get("sql_result", {})
    messages = state["messages"]

    # 사용자 원본 질문 추출
    user_query = ""
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'human':
            user_query = msg.content

    return f"""## 사용자 질문: {user_query}

## SQL 쿼리 결과
- 쿼리: {sql_result.get('query', '')}
- 행 수: {sql_result.get('row_count', 0)}
- 컬럼: {', '.join(sql_result.get('columns', []))}

## 데이터:
{json.dumps(sql_result.get('data', []), ensure_ascii=False, default=str)}"""


async def text_response_node(state: MMAGraphState, llm) -> dict:
    """
    텍스트 분석 응답 노드

    sql_agent가 이미 생성한 agent_reasoning이 있으면 재사용 (LLM 호출 생략).
    없는 경우만 with_structured_output으로 새로 생성.
    """
    try:
        agent_reasoning = state.get("agent_reasoning")

        if agent_reasoning:
            # sql_agent가 이미 생성한 답변 재사용 — LLM 호출 불필요
            LOGGER.info("♻️ Reusing agent_reasoning, skipping LLM call")
            content = agent_reasoning
            viz_data = {"title": "", "content": content}
        else:
            # fallback: agent_reasoning 없는 경우 LLM 호출
            input_text = _build_text_input(state)
            structured_llm = llm.with_structured_output(TextSummaryOutput)
            result = await structured_llm.ainvoke([
                SystemMessage(content=TEXT_RESPONSE_PROMPT),
                HumanMessage(content=input_text),
            ])
            content = result.content
            viz_data = {"title": result.title, "content": content}

        # 히스토리용: 텍스트 + SQL 데이터 요약 (후속 질문의 맥락 제공)
        data_summary = _build_data_summary(state.get("sql_result", {}))
        parts = [content]
        if data_summary:
            parts.append(data_summary)
        summary_for_history = "\n".join(p for p in parts if p)

        LOGGER.info(f"✅ Text response generated: {len(content)} chars")

        return {
            "visualization_type": "text_summary",
            "visualization_data": viz_data,
            "insights": [],
            "final_response": summary_for_history,
            "messages": [AIMessage(content=summary_for_history)],
        }

    except Exception as e:
        LOGGER.error(f"❌ Text response failed: {e}")
        error_msg = "데이터 분석 중 오류가 발생했습니다."
        return {
            "visualization_type": "text_summary",
            "visualization_data": {"title": "", "content": error_msg},
            "insights": [],
            "final_response": error_msg,
            "messages": [AIMessage(content=error_msg)],
        }
