"""Critic Agent 노드 — 하이브리드 검증 (규칙 기반 Phase A + LLM Phase B)"""
import asyncio
import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from llm.graph.state import MainState, AgentResult, ValidationStatus
from llm.graph.prompts import CRITIC_LLM_PROMPT
from llm.tools.sql_tool import _validate_query
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

CRITIC_TIMEOUT_SECONDS = 20
MAX_RETRIES = 3


class CriticLLMOutput(BaseModel):
    """Critic Phase B LLM 출력"""
    passed: bool = Field(description="검증 통과 여부")
    feedback: str = Field(default="", description="실패 시 구체적 사유")


@dataclass(frozen=True)
class PhaseAOutcome:
    """Deterministic Phase A validation outcome."""
    validation_status: ValidationStatus
    feedback: str | None = None


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


def _normalize_sql(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def _normalize_text(text: str) -> str:
    return text.strip().lower()


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _is_unsupported_result(result: AgentResult) -> bool:
    reasoning = _normalize_text(result.get("reasoning", ""))
    return not result.get("query") and "unsupported" in reasoning


def _looks_like_error_result(result: AgentResult) -> bool:
    error = result.get("error") or ""
    if result.get("success") is False and error and "No SQL result found" not in error:
        return True

    reasoning = result.get("reasoning", "")
    if result.get("query") or not reasoning:
        return False

    return _has_any(
        _normalize_text(reasoning),
        (
            "sql execution failed",
            "query failed",
            "database error",
            "db error",
            "permission",
            "timeout",
            "timed out",
            "connection",
            "syntax error",
            "undefinedtable",
            "error",
            "failed",
            "실패",
            "오류",
            "에러",
            "초과",
        ),
    )


# =============================================================================
# Phase A: 규칙 기반 검증
# =============================================================================

def _validate_readonly_sql(result: AgentResult) -> str | None:
    """SQL 쿼리 안전성과 기본 shape 검증. query가 있을 때만 검사한다."""
    query = result.get("query", "")
    if not query:
        return None
    try:
        _validate_query(query)
    except ValueError as e:
        return str(e)
    return None


def _validate_payload_shape(result: AgentResult) -> str | None:
    """Downstream 노드가 처리할 수 있는 AgentResult payload인지 검증."""
    data = result.get("data", [])
    columns = result.get("columns", [])
    row_count = result.get("row_count", 0)

    if not isinstance(data, list):
        return "Agent result data must be a list."
    if not isinstance(columns, list):
        return "Agent result columns must be a list."
    if not isinstance(row_count, int) or row_count < 0:
        return "Agent result row_count must be a non-negative integer."
    if data and row_count == 0:
        return "Agent result row_count is 0 but data is not empty."

    for idx, row in enumerate(data[:5]):
        if not isinstance(row, dict):
            return f"Agent result data row {idx} must be an object."
    return None


def _classify_empty_result(query: str) -> PhaseAOutcome:
    _ = query
    return PhaseAOutcome(validation_status="valid_empty")


def _run_phase_a(agent_results: list[AgentResult], resolved_query: str) -> PhaseAOutcome:
    """Phase A: 규칙 기반 검증 (모든 에이전트 결과에 대해)

    Returns: deterministic validation status and feedback.
    """
    _ = resolved_query

    for result in agent_results:
        agent_name = result.get("agent_name", "unknown")
        query = _normalize_sql(result.get("query", ""))

        if _is_unsupported_result(result):
            return PhaseAOutcome(
                validation_status="unsupported",
                feedback=result.get("reasoning", "현재 데이터베이스에서 답할 수 없는 요청입니다."),
            )

        if _looks_like_error_result(result):
            return PhaseAOutcome(
                validation_status="retry_needed",
                feedback=f"[{agent_name}] 에이전트 실행 실패: {result.get('error') or result.get('reasoning', '')}",
            )

        feedback = _validate_payload_shape(result)
        if feedback:
            return PhaseAOutcome(validation_status="invalid_result", feedback=f"[{agent_name}] {feedback}")

        if not result.get("query"):
            return PhaseAOutcome(
                validation_status="no_sql_needed",
                feedback=result.get("reasoning"),
            )

        feedback = _validate_readonly_sql(result)
        if feedback:
            return PhaseAOutcome(validation_status="retry_needed", feedback=f"[{agent_name}] {feedback}")

        if result.get("row_count", 0) == 0 and not result.get("data"):
            empty_outcome = _classify_empty_result(query)
            if empty_outcome.validation_status != "valid_empty":
                return empty_outcome
            continue

    has_valid_empty = any(
        result.get("row_count", 0) == 0 and not result.get("data")
        for result in agent_results
    )
    return PhaseAOutcome(validation_status="valid_empty" if has_valid_empty else "passed")


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
    phase_a_outcome = _run_phase_a(agent_results, resolved_query)
    if phase_a_outcome.validation_status == "retry_needed":
        LOGGER.info(f"❌ Critic Phase A failed: {phase_a_outcome.feedback}")
        return _failure_return(retry_count, phase_a_outcome.feedback or "검증 실패")
    if phase_a_outcome.validation_status == "invalid_result":
        LOGGER.info(f"❌ Critic Phase A invalid result: {phase_a_outcome.feedback}")
        return _failure_return(
            retry_count,
            phase_a_outcome.feedback or "에이전트 결과 형식이 올바르지 않습니다.",
            validation_status="invalid_result",
        )
    if phase_a_outcome.validation_status == "unsupported":
        LOGGER.info(f"⚠️ Critic Phase A unsupported: {phase_a_outcome.feedback}")
        return {
            "critic_passed": False,
            "validation_status": "unsupported",
            "critic_feedback": phase_a_outcome.feedback,
            "needs_visualization": False,
        }
    if phase_a_outcome.validation_status == "valid_empty":
        LOGGER.info("✅ Critic Phase A valid empty result")
        return {
            "critic_passed": True,
            "validation_status": "valid_empty",
            "critic_feedback": None,
            "needs_visualization": False,
        }
    if phase_a_outcome.validation_status == "no_sql_needed":
        LOGGER.info("✅ Critic Phase A no SQL needed")
        return {
            "critic_passed": True,
            "validation_status": "no_sql_needed",
            "critic_feedback": None,
            "needs_visualization": False,
        }

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
                "validation_status": "passed",
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
            "validation_status": "passed",
            "critic_feedback": None,
            "needs_visualization": _should_visualize(agent_results),
        }


def _failure_return(
    current_retry_count: int,
    feedback: str,
    validation_status: ValidationStatus = "retry_needed",
) -> dict:
    """Critic 실패 시 반환값 생성"""
    new_retry_count = current_retry_count + 1

    if new_retry_count >= MAX_RETRIES:
        # 3회 소진 → 에러 응답 설정 후 END
        LOGGER.error(f"❌ Critic retries exhausted ({MAX_RETRIES})")
        return {
            "critic_passed": False,
            "validation_status": validation_status,
            "retry_count": new_retry_count,
            "agent_results": [],
            "final_response": "분석 결과의 품질 검증에 실패했습니다. 질문을 더 구체적으로 바꿔주세요.",
            "visualization_type": None,
            "visualization_data": None,
        }

    # 재시도 가능 → 피드백 + agent_results 초기화
    return {
        "critic_passed": False,
        "validation_status": validation_status,
        "critic_feedback": feedback,
        "retry_count": new_retry_count,
        "agent_results": [],  # reducer가 초기화
    }
