"""결과 분석 노드 - SQL 결과의 시각화 적합성 판단"""
from llm.graph.state import MMAGraphState
from common.logging_config import get_logger

LOGGER = get_logger(__name__)


def _rule_based_analysis(data: list, columns: list, row_count: int) -> str | None:
    """
    규칙 기반 시각화 적합성 판단

    Returns:
        "visualization" | "text" | None (LLM에 위임)
    """
    # 데이터 없음
    if row_count == 0:
        return "text"

    # 단일 행, 컬럼 3개 이하 → 텍스트 (단순 값 응답)
    if row_count == 1 and len(columns) <= 3:
        return "text"

    # 단일 행, 컬럼 4개 이상 → 시각화 (다차원 스탯, radar 등)
    if row_count == 1 and len(columns) >= 4:
        has_numeric = _has_numeric_columns(data, columns)
        return "visualization" if has_numeric else "text"

    # 2행 이상, 수치 데이터 있음 → 시각화
    if row_count >= 2:
        has_numeric = _has_numeric_columns(data, columns)
        if has_numeric:
            return "visualization"

    # 2행 이상이지만 수치 없음 → 텍스트 (이름 목록 등)
    if row_count >= 2:
        return "text"

    return None


_ID_SUFFIXES = {"id", "_id", "fighter_id", "event_id", "weight_class_id"}


def _is_id_column(col_name: str) -> bool:
    """식별자 컬럼인지 판별 (시각화 대상에서 제외)"""
    lower = col_name.lower()
    return lower in _ID_SUFFIXES or lower.endswith("_id")


def _has_numeric_columns(data: list, columns: list) -> bool:
    """시각화에 의미 있는 수치 컬럼이 있는지 확인 (id 컬럼 제외)"""
    if not data:
        return False

    first_row = data[0]
    for col in columns:
        if _is_id_column(col):
            continue
        val = first_row.get(col) if isinstance(first_row, dict) else None
        if isinstance(val, (int, float)):
            return True

    return False


async def result_analyzer_node(state: MMAGraphState, **kwargs) -> dict:
    """
    시각화 적합성 판단 노드

    SQL 결과를 분석하여 차트로 보여줄지 텍스트로 답할지 결정.
    대부분 규칙 기반으로 판단, 애매한 경우만 LLM에 위임.
    """
    sql_result = state.get("sql_result")

    if not sql_result or not sql_result.get("success"):
        LOGGER.info("📋 Result analyzer: text (SQL failed or no result)")
        return {"response_mode": "text"}

    data = sql_result.get("data", [])
    columns = sql_result.get("columns", [])
    row_count = sql_result.get("row_count", 0)

    # 규칙 기반 판단
    mode = _rule_based_analysis(data, columns, row_count)
    if mode:
        LOGGER.info(f"📋 Result analyzer (rule-based): {mode}")
        return {"response_mode": mode}

    # 규칙으로 결정 못한 경우 → 기본값 text
    LOGGER.info("📋 Result analyzer (default): text")
    return {"response_mode": "text"}
