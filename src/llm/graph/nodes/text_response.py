"""텍스트 분석 응답 노드 - SQL 결과를 텍스트로 분석"""
import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm.graph.state import MMAGraphState
from llm.graph.prompts import TEXT_RESPONSE_PROMPT
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


def _parse_text_response_json(response_text: str) -> dict | None:
    """LLM 응답에서 텍스트 응답 JSON 추출"""
    import re

    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    json_block = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    return None


async def text_response_node(state: MMAGraphState, llm) -> dict:
    """
    텍스트 분석 응답 노드

    SQL 결과가 시각화에 적합하지 않을 때 텍스트로 분석하여 응답.
    """
    try:
        input_text = _build_text_input(state)

        response = await llm.ainvoke([
            SystemMessage(content=TEXT_RESPONSE_PROMPT),
            HumanMessage(content=input_text),
        ])

        response_text = response.content if hasattr(response, 'content') else str(response)

        # JSON 파싱 시도
        parsed = _parse_text_response_json(response_text)

        if parsed:
            viz_data = parsed.get("visualization_data", {})
            content = viz_data.get("content", response_text)

            LOGGER.info(f"✅ Text response generated: {len(content)} chars")

            return {
                "visualization_type": "text_summary",
                "visualization_data": viz_data,
                "insights": [],
                "final_response": content,
                "messages": [AIMessage(content=content)],
            }

        # JSON 파싱 실패 → 원시 텍스트 사용
        LOGGER.info(f"✅ Text response (raw): {len(response_text)} chars")
        return {
            "visualization_type": "text_summary",
            "visualization_data": {"title": "", "content": response_text},
            "insights": [],
            "final_response": response_text,
            "messages": [AIMessage(content=response_text)],
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
