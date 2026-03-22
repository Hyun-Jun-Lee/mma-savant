"""시각화 데이터 생성 노드 - SQL 결과를 차트 데이터로 변환"""
import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llm.graph.state import MMAGraphState
from llm.graph.prompts import VISUALIZE_PROMPT
from llm.graph.schemas import ChartVisualizationOutput
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

MAX_SUMMARY_ROWS = 10


def _build_data_summary(sql_result: dict) -> str:
    """SQL 쿼리와 결과를 히스토리용 텍스트로 변환

    후속 질문에서 "1등 선수", "상위 3명" 등의 참조를 해석할 수 있도록
    실행된 SQL 쿼리와 결과 데이터를 포함.
    """
    parts = []

    query = sql_result.get("query", "")
    if query:
        parts.append(f"[SQL] {query}")

    data = sql_result.get("data", [])
    columns = sql_result.get("columns", [])
    if data and columns:
        rows = []
        for i, row in enumerate(data[:MAX_SUMMARY_ROWS], 1):
            values = [f"{col}: {row.get(col, '')}" for col in columns]
            rows.append(f"{i}. " + ", ".join(values))
        parts.append("[결과]\n" + "\n".join(rows))

    return "\n".join(parts)


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


async def visualize_node(state: MMAGraphState, llm) -> dict:
    """
    시각화 데이터 생성 노드

    SQL 결과를 분석하여 최적의 차트 타입을 선택하고
    시각화 데이터를 구조화된 JSON으로 생성.
    with_structured_output으로 스키마를 강제하여 파싱 안정성 보장.
    """
    try:
        input_text = _build_visualize_input(state)

        structured_llm = llm.with_structured_output(ChartVisualizationOutput)
        result = await structured_llm.ainvoke([
            SystemMessage(content=VISUALIZE_PROMPT),
            HumanMessage(content=input_text),
        ])

        viz_type = result.selected_visualization
        viz_data = result.visualization_data.model_dump()
        insights = result.insights

        # 히스토리용 텍스트 요약 생성 (후속 질문의 맥락 제공)
        title = viz_data.get("title", "")
        data_summary = _build_data_summary(state.get("sql_result", {}))
        parts = [title]
        if data_summary:
            parts.append(data_summary)
        if insights:
            parts.append("\n".join(f"- {i}" for i in insights))
        summary = "\n".join(p for p in parts if p)

        LOGGER.info(f"✅ Visualization generated: {viz_type}")

        return {
            "visualization_type": viz_type,
            "visualization_data": viz_data,
            "insights": insights,
            "final_response": summary,
            "messages": [AIMessage(content=summary)],
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
