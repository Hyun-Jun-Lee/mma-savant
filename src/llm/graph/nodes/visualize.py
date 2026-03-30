"""시각화 데이터 생성 노드 — agent_results를 차트 데이터로 변환"""
import json

from langchain_core.messages import SystemMessage, HumanMessage

from llm.graph.state import MainState
from llm.graph.prompts import VISUALIZE_PROMPT
from llm.graph.schemas import VisualizationDecision
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

_ID_PATTERNS = {"id", "_id", "fighter_id", "event_id", "weight_class_id"}


def _strip_id_columns(rows: list[dict]) -> list[dict]:
    """id 컬럼 제거"""
    if not rows:
        return []
    id_cols = {
        k for k in rows[0]
        if k.lower() in _ID_PATTERNS or k.lower().endswith("_id")
    }
    if not id_cols:
        return rows
    return [{k: v for k, v in row.items() if k not in id_cols} for row in rows]


def _merge_agent_data(agent_results: list) -> list[dict]:
    """모든 에이전트 결과에서 데이터 병합"""
    all_data = []
    for result in agent_results:
        all_data.extend(result.get("data", []))
    return all_data



def _collect_columns(agent_results: list) -> list[str]:
    """모든 에이전트 결과에서 컬럼명 수집 (중복 제거, 순서 유지)"""
    seen: set[str] = set()
    cols: list[str] = []
    for result in agent_results:
        for c in result.get("columns", []):
            if c not in seen:
                seen.add(c)
                cols.append(c)
    return cols


def _build_visualize_input(resolved_query: str, agent_results: list) -> str:
    """시각화 LLM 호출용 입력 데이터 구성"""
    columns = _collect_columns(agent_results)
    parts = [
        f"## 사용자 질문: {resolved_query}\n",
        f"## 사용 가능한 컬럼 (x_axis/y_axis는 반드시 이 목록에서만 선택): {columns}\n",
    ]

    for result in agent_results:
        agent_name = result.get("agent_name", "unknown")
        parts.append(f"## [{agent_name}] SQL 쿼리 결과")
        parts.append(f"- 쿼리: {result.get('query', '')}")
        parts.append(f"- 행 수: {result.get('row_count', 0)}")
        parts.append(f"\n### 데이터:")
        parts.append(json.dumps(result.get("data", []), ensure_ascii=False, default=str))
        parts.append("")

    return "\n".join(parts)


def _validate_axes(
    x_axis: str | None,
    y_axis: str | None,
    data_columns: set[str],
) -> tuple[str | None, str | None]:
    """LLM이 반환한 x_axis/y_axis가 실제 컬럼에 있는지 검증.

    존재하지 않는 컬럼명은 None으로 보정한다.
    """
    valid_x = x_axis if x_axis in data_columns else None
    valid_y = y_axis if y_axis in data_columns else None

    if valid_x != x_axis or valid_y != y_axis:
        LOGGER.warning(
            f"⚠️ Axis corrected: x_axis={x_axis!r}→{valid_x!r}, "
            f"y_axis={y_axis!r}→{valid_y!r} (available: {data_columns})"
        )
    return valid_x, valid_y


async def visualize_node(state: MainState, llm) -> dict:
    """
    시각화 데이터 생성 노드

    LLM이 차트 타입/제목/컬럼 매핑/인사이트를 결정하고,
    data는 agent_results에서 직접 구성 (LLM이 대량 데이터를 재생산하지 않음).
    """
    agent_results = state.get("agent_results", [])
    resolved_query = state.get("resolved_query", "")

    try:
        input_text = _build_visualize_input(resolved_query, agent_results)

        structured_llm = llm.with_structured_output(VisualizationDecision)
        decision = await structured_llm.ainvoke([
            SystemMessage(content=VISUALIZE_PROMPT),
            HumanMessage(content=input_text),
        ])

        # data는 agent_results에서 직접 구성
        raw_data = _merge_agent_data(agent_results)
        chart_data = _strip_id_columns(raw_data)

        viz_type = decision.selected_visualization
        data_columns = set(chart_data[0].keys()) if chart_data else set()

        # 1) LLM 반환값 검증: 실제 컬럼에 없으면 None으로 보정
        x_axis, y_axis = _validate_axes(decision.x_axis, decision.y_axis, data_columns)

        # 2) wide format(1행 다중 숫자 컬럼) → long format 변환
        if len(chart_data) == 1 and x_axis is None and y_axis is None:
            row = chart_data[0]
            numeric_cols = [k for k, v in row.items() if isinstance(v, (int, float))]
            if len(numeric_cols) >= 2:
                x_axis = "category"
                y_axis = "value"
                chart_data = [{x_axis: k, y_axis: v} for k, v in row.items()
                              if isinstance(v, (int, float))]
                if viz_type == "horizontal_bar":
                    x_axis, y_axis = y_axis, x_axis
                LOGGER.info(f"🔄 Wide→long: {len(chart_data)} rows, x={x_axis}, y={y_axis}")

        LOGGER.info(f"✅ Visualization generated: {viz_type}, data rows: {len(chart_data)}")

        return {
            "visualization_type": viz_type,
            "visualization_data": {
                "title": decision.title,
                "data": chart_data,
                "x_axis": x_axis,
                "y_axis": y_axis,
            },
            "insights": decision.insights,
        }

    except Exception as e:
        LOGGER.error(f"❌ Visualization failed: {e} (text response unaffected)")
        return {
            "visualization_type": None,
            "visualization_data": None,
            "insights": [],
        }
