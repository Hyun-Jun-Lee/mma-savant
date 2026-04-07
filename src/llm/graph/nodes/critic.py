"""Critic Agent 노드 — 하이브리드 검증 (규칙 기반 Phase A + LLM Phase B)"""
import asyncio
import json

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from llm.graph.state import MainState, AgentResult
from llm.graph.prompts import CRITIC_LLM_PROMPT
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

CRITIC_TIMEOUT_SECONDS = 20
MAX_RETRIES = 3


class CriticLLMOutput(BaseModel):
    """Critic Phase B LLM 출력"""
    passed: bool = Field(description="검증 통과 여부")
    feedback: str = Field(default="", description="실패 시 구체적 사유")


# =============================================================================
# 시각화 필요 여부 — 규칙 기반 판별
# =============================================================================

def _is_numeric_value(val) -> bool:
    """숫자 또는 숫자형 문자열 판별"""
    if isinstance(val, bool):
        return False
    if isinstance(val, (int, float)):
        return True
    if isinstance(val, str):
        try:
            float(val)
            return True
        except ValueError:
            return False
    return False


def _count_numeric_columns(row: dict) -> int:
    """실질적 수치 컬럼 수 계산 (id류·boolean 제외)"""
    count = 0
    for key, val in row.items():
        if "id" in key.lower():
            continue
        if _is_numeric_value(val):
            count += 1
    return count


def _should_visualize(agent_results: list[AgentResult]) -> bool:
    """데이터 특성 기반 시각화 필요 여부 판별 (규칙 기반)

    판별 기준:
    - 3행 이상 + 수치 컬럼 1개 이상 → True (랭킹, 집계)
    - 2행 + 수치 컬럼 2개 이상 → True (비교)
    - 1행 + 수치 컬럼 4개 이상 → True (레이더 차트 등 다차원 프로필)
    - 그 외 → False (텍스트 응답)
    """
    for result in agent_results:
        row_count = result.get("row_count", 0)
        data = result.get("data", [])

        if row_count == 0 or not data:
            continue

        numeric_cols = _count_numeric_columns(data[0])

        if row_count >= 3 and numeric_cols >= 1:
            return True
        if row_count == 2 and numeric_cols >= 2:
            return True
        if row_count == 1 and numeric_cols >= 4:
            return True

    return False


# =============================================================================
# Phase A: 규칙 기반 검증
# =============================================================================

def _validate_sql_syntax(result: AgentResult) -> str | None:
    """SQL 쿼리 기본 검증"""
    query = result.get("query", "")
    if not query:
        return "SQL 쿼리가 비어있습니다."
    # 기본 SQL 키워드 존재 확인
    upper = query.upper()
    if not any(kw in upper for kw in ("SELECT", "WITH")):
        return f"유효하지 않은 SQL: SELECT/WITH 키워드 없음"
    return None


def _validate_result_not_empty(result: AgentResult) -> str | None:
    """결과 데이터 비어있는지 확인"""
    if result.get("row_count", 0) == 0 and not result.get("data"):
        return "SQL 실행 결과가 비어있습니다 (0행). 쿼리 조건을 확인하세요."
    return None


def _validate_value_ranges(result: AgentResult) -> str | None:
    """결과 값 범위 타당성 검증"""
    data = result.get("data", [])
    if not data:
        return None

    for row in data[:5]:  # 상위 5행만 샘플 검증
        if not isinstance(row, dict):
            continue
        for key, val in row.items():
            if not isinstance(val, (int, float)):
                continue
            lower_key = key.lower()
            # 비율/퍼센트 필드 검증
            if any(kw in lower_key for kw in ("rate", "pct", "ratio", "accuracy", "percentage")):
                if val < 0 or val > 100:
                    return f"비율 필드 '{key}'의 값 {val}이 0~100 범위를 벗어남"
            # 음수 카운트 검증
            if any(kw in lower_key for kw in ("count", "wins", "losses", "total", "fights")):
                if val < 0:
                    return f"카운트 필드 '{key}'의 값 {val}이 음수"
    return None


def _run_phase_a(agent_results: list[AgentResult]) -> str | None:
    """Phase A: 규칙 기반 검증 (모든 에이전트 결과에 대해)

    Returns: 실패 피드백 (None이면 통과)
    """
    for result in agent_results:
        agent_name = result.get("agent_name", "unknown")

        # 에러 AgentResult는 즉시 실패
        if not result.get("query") and result.get("reasoning"):
            # _error_agent_result 패턴: query 비어있고 reasoning에 에러 메시지
            if any(kw in result.get("reasoning", "") for kw in ("초과", "복잡", "실패", "Error", "error")):
                return f"[{agent_name}] 에이전트 실행 실패: {result['reasoning']}"

        # SQL 검증
        feedback = _validate_sql_syntax(result)
        if feedback:
            return f"[{agent_name}] {feedback}"

        # 빈 결과 검증
        feedback = _validate_result_not_empty(result)
        if feedback:
            return f"[{agent_name}] {feedback}"

        # 값 범위 검증
        feedback = _validate_value_ranges(result)
        if feedback:
            return f"[{agent_name}] {feedback}"

    return None


# =============================================================================
# Phase B: LLM 의미적 정합성 검증
# =============================================================================

def _build_critic_input(resolved_query: str, agent_results: list[AgentResult]) -> str:
    """Phase B LLM 입력 구성"""
    parts = [f"## 사용자 질문\n{resolved_query}\n"]

    for result in agent_results:
        parts.append(f"## [{result.get('agent_name', 'unknown')}] 결과")
        parts.append(f"- SQL: {result.get('query', '')}")
        parts.append(f"- 행 수: {result.get('row_count', 0)}")
        parts.append(f"- 컬럼: {', '.join(result.get('columns', []))}")

        data = result.get("data", [])
        if data:
            sample = data[:5]
            parts.append(f"- 데이터 샘플:\n{json.dumps(sample, ensure_ascii=False, default=str)}")
        parts.append("")

    return "\n".join(parts)


# =============================================================================
# 메인 Critic 노드
# =============================================================================

async def critic_node(state: MainState, llm) -> dict:
    """
    Critic Agent 노드

    Phase A (규칙 기반): SQL 문법, 빈 결과, 값 범위 검증
    Phase B (LLM 기반): Phase A 통과 시에만 의미적 정합성 검증

    실패 시 retry_count 증가, agent_results 초기화.
    3회 소진 시 에러 응답 설정.
    """
    agent_results = state.get("agent_results", [])
    resolved_query = state.get("resolved_query", "")
    retry_count = state.get("retry_count", 0)

    if not agent_results:
        LOGGER.warning("⚠️ No agent_results to validate")
        return _failure_return(retry_count, "검증할 에이전트 결과가 없습니다.")

    # ── Phase A: 규칙 기반 검증 ──
    phase_a_feedback = _run_phase_a(agent_results)
    if phase_a_feedback:
        LOGGER.info(f"❌ Critic Phase A failed: {phase_a_feedback}")
        return _failure_return(retry_count, phase_a_feedback)

    # ── Phase B: LLM 의미적 정합성 검증 ──
    try:
        structured_llm = llm.with_structured_output(CriticLLMOutput)
        critic_input = _build_critic_input(resolved_query, agent_results)

        result = await asyncio.wait_for(
            structured_llm.ainvoke([
                SystemMessage(content=CRITIC_LLM_PROMPT),
                HumanMessage(content=critic_input),
            ]),
            timeout=CRITIC_TIMEOUT_SECONDS,
        )

        if result.passed:
            viz = _should_visualize(agent_results)
            LOGGER.info(
                f"✅ Critic passed (Phase A + Phase B), "
                f"needs_visualization={viz}"
            )
            return {
                "critic_passed": True,
                "critic_feedback": None,
                "needs_visualization": viz,
            }

        LOGGER.info(f"❌ Critic Phase B failed: {result.feedback}")
        return _failure_return(retry_count, result.feedback)

    except Exception as e:
        # LLM 실패 시 Phase A만 통과했으면 통과 처리 (규칙 기반 결과 신뢰)
        LOGGER.warning(f"⚠️ Critic Phase B LLM failed: {e}, passing with Phase A only")
        return {
            "critic_passed": True,
            "critic_feedback": None,
            "needs_visualization": _should_visualize(agent_results),
        }


def _failure_return(current_retry_count: int, feedback: str) -> dict:
    """Critic 실패 시 반환값 생성"""
    new_retry_count = current_retry_count + 1

    if new_retry_count >= MAX_RETRIES:
        # 3회 소진 → 에러 응답 설정 후 END
        LOGGER.error(f"❌ Critic retries exhausted ({MAX_RETRIES})")
        return {
            "critic_passed": False,
            "retry_count": new_retry_count,
            "agent_results": [],
            "final_response": "분석 결과의 품질 검증에 실패했습니다. 질문을 더 구체적으로 바꿔주세요.",
            "visualization_type": None,
            "visualization_data": None,
        }

    # 재시도 가능 → 피드백 + agent_results 초기화
    return {
        "critic_passed": False,
        "critic_feedback": feedback,
        "retry_count": new_retry_count,
        "agent_results": [],  # reducer가 초기화
    }
