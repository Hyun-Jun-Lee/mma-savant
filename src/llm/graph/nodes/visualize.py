"""시각화 데이터 생성 노드 - SQL 결과를 차트 데이터로 변환"""
import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm.graph.state import MMAGraphState
from llm.graph.prompts import VISUALIZE_PROMPT
from llm.chart_loader import validate_chart_id
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


def _build_visualize_input(state: MMAGraphState) -> str:
    """시각화 LLM 호출용 입력 데이터 구성"""
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


def _parse_visualization_json(response_text: str) -> dict | None:
    """LLM 응답에서 시각화 JSON 추출"""
    import re

    # 직접 JSON 파싱
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # ```json ... ``` 블록 추출
    json_block = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # { ... } 패턴 추출
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if "selected_visualization" in parsed or "visualization_data" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    return None


async def visualize_node(state: MMAGraphState, llm) -> dict:
    """
    시각화 데이터 생성 노드

    SQL 결과를 분석하여 최적의 차트 타입을 선택하고
    시각화 데이터를 구조화된 JSON으로 생성.
    """
    try:
        input_text = _build_visualize_input(state)

        response = await llm.ainvoke([
            SystemMessage(content=VISUALIZE_PROMPT),
            HumanMessage(content=input_text),
        ])

        response_text = response.content if hasattr(response, 'content') else str(response)

        # JSON 파싱
        parsed = _parse_visualization_json(response_text)

        if parsed:
            viz_type = parsed.get("selected_visualization", "text_summary")
            viz_data = parsed.get("visualization_data", {})
            insights = parsed.get("insights", [])

            # 차트 타입 검증
            if not validate_chart_id(viz_type):
                LOGGER.warning(f"⚠️ Invalid chart type: {viz_type}, falling back to text_summary")
                viz_type = "text_summary"

            # 히스토리용 텍스트 요약 생성 (후속 질문의 맥락 제공)
            title = viz_data.get("title", "")
            summary = title
            if insights:
                summary = f"{title}\n" + "\n".join(f"- {i}" for i in insights)

            LOGGER.info(f"✅ Visualization generated: {viz_type}")

            return {
                "visualization_type": viz_type,
                "visualization_data": viz_data,
                "insights": insights,
                "final_response": summary,
                "messages": [AIMessage(content=summary)],
            }

        # JSON 파싱 실패 → text_summary fallback
        LOGGER.warning("⚠️ Failed to parse visualization JSON, using text_summary")
        return {
            "visualization_type": "text_summary",
            "visualization_data": {"title": "", "content": response_text},
            "insights": [],
            "final_response": response_text,
            "messages": [AIMessage(content=response_text)],
        }

    except Exception as e:
        LOGGER.error(f"❌ Visualization failed: {e}")
        error_msg = "시각화 데이터 생성에 실패했습니다."
        return {
            "visualization_type": "text_summary",
            "visualization_data": {"title": "", "content": error_msg},
            "insights": [],
            "final_response": error_msg,
            "messages": [AIMessage(content=error_msg)],
        }
