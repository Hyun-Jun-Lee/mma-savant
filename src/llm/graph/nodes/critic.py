"""Critic Agent 노드 — 하이브리드 검증 (규칙 기반 Phase A + LLM Phase B)"""
import asyncio
import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from llm.graph.state import MainState, AgentResult, ValidationStatus
from llm.graph.prompts import CRITIC_LLM_PROMPT
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


def _extract_intents(resolved_query: str) -> dict[str, bool]:
    text = _normalize_text(resolved_query)
    has_decision = _has_any(text, ("판정", "decision", "dec"))
    asks_for_wins = _has_any(text, ("승리", "승수", "win", "wins"))
    asks_for_fights = _has_any(text, ("경기", "참여", "participation", "fight", "fights"))
    return {
        "recent": _has_any(text, ("recent", "latest", "last", "최근", "마지막")),
        "upcoming": _has_any(text, ("upcoming", "next", "다음", "예정")),
        "win_rate": _has_any(text, ("승률", "win rate")),
        "clean_win_rate": _has_any(text, ("clean win", "clean rate", "무승부", "노컨테스트", "제외")),
        "ko_tko_wins": _has_any(text, ("ko/tko", "ko 승", "ko 승리", "tko 승", "tko 승리")),
        "submission_wins": _has_any(text, ("submission win", "submission wins", "서브미션 승", "서브미션 승리")),
        "decision_wins": has_decision and asks_for_wins,
        "decision_participation": has_decision and asks_for_fights and not asks_for_wins,
    }


def _is_unsupported_result(result: AgentResult) -> bool:
    reasoning = _normalize_text(result.get("reasoning", ""))
    return not result.get("query") and "unsupported" in reasoning


def _looks_like_error_result(result: AgentResult) -> bool:
    reasoning = result.get("reasoning", "")
    return not result.get("query") and bool(reasoning) and any(
        kw in reasoning for kw in ("초과", "복잡", "실패", "Error", "error")
    )


def _has_ambiguous_text_filter(query: str) -> bool:
    return bool(re.search(
        r"\b(name|fighter_name|method|result|event_name)\b\s+(?:i?like|=)",
        query,
    ))


def _has_completed_scope(query: str) -> bool:
    return (
        "v_completed_fighter_fights" in query
        or (
            "event_date <=" in query
            and ("current_date" in query or "current date" in query)
            and ("result is not null" in query or "result is not null" in query)
        )
    )


def _has_upcoming_scope(query: str) -> bool:
    return "event_date >" in query and ("current_date" in query or "current date" in query)


def _has_win_condition(query: str) -> bool:
    return "result = 'win'" in query or 'result = "win"' in query


def _has_submission_bucket(query: str) -> bool:
    return "sub-%" in query or "is_submission" in query or "submission_wins" in query


def _has_ko_tko_bucket(query: str) -> bool:
    return "ko/tko%" in query or "is_ko_tko" in query or "ko_tko_wins" in query


def _has_decision_bucket(query: str) -> bool:
    return "%dec%" in query or "u-dec" in query or "s-dec" in query or "m-dec" in query or "is_decision" in query or "decision_" in query


def _matches_win_rate_policy(query: str, clean_requested: bool) -> bool:
    if "v_fighter_record_summary" in query:
        return True
    if clean_requested:
        return "wins + losses" in query and "draws" not in query and "no_contests" not in query
    return "wins + losses + draws + no_contests" in query


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


def _validate_intent_guardrails(query: str, intents: dict[str, bool]) -> str | None:
    if intents["recent"] and not _has_completed_scope(query):
        return "recent fights 질문에는 completed-fight scope가 필요합니다."
    if intents["upcoming"] and not _has_upcoming_scope(query):
        return "upcoming 질문에는 future event 조건이 필요합니다."
    if intents["win_rate"] and not _matches_win_rate_policy(query, intents["clean_win_rate"]):
        if intents["clean_win_rate"]:
            return "clean win/loss rate 질문에는 wins / (wins + losses) denominator가 필요합니다."
        return "win rate 질문에는 wins / (wins + losses + draws + no_contests) denominator가 필요합니다."
    if intents["ko_tko_wins"]:
        if not _has_win_condition(query):
            return "KO/TKO wins 질문에는 result = 'win' 조건이 필요합니다."
        if not _has_ko_tko_bucket(query):
            return "KO/TKO wins 질문에는 KO/TKO method bucket이 필요합니다."
    if intents["submission_wins"]:
        if not _has_win_condition(query):
            return "submission wins 질문에는 result = 'win' 조건이 필요합니다."
        if not _has_submission_bucket(query):
            return "submission wins 질문에는 submission method bucket이 필요합니다."
    if intents["decision_wins"]:
        if not _has_win_condition(query):
            return "decision wins 질문에는 result = 'win' 조건이 필요합니다."
        if not _has_decision_bucket(query):
            return "decision wins 질문에는 decision method bucket이 필요합니다."
    if intents["decision_participation"]:
        if not _has_decision_bucket(query):
            return "decision participation 질문에는 decision method bucket이 필요합니다."
        if _has_win_condition(query):
            return "decision participation 질문에는 result = 'win'을 강제하면 안 됩니다."
    return None


def _classify_empty_result(query: str) -> PhaseAOutcome:
    if _has_ambiguous_text_filter(query):
        return PhaseAOutcome(
            validation_status="retry_needed",
            feedback="0행 결과입니다. name/method/result/weight_class/event text filter 값을 다시 검증하세요.",
        )
    return PhaseAOutcome(validation_status="valid_empty")


def _run_phase_a(agent_results: list[AgentResult], resolved_query: str) -> PhaseAOutcome:
    """Phase A: 규칙 기반 검증 (모든 에이전트 결과에 대해)

    Returns: deterministic validation status and feedback.
    """
    intents = _extract_intents(resolved_query)

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
                feedback=f"[{agent_name}] 에이전트 실행 실패: {result['reasoning']}",
            )

        feedback = _validate_sql_syntax(result)
        if feedback:
            return PhaseAOutcome(validation_status="retry_needed", feedback=f"[{agent_name}] {feedback}")

        if result.get("row_count", 0) == 0 and not result.get("data"):
            empty_outcome = _classify_empty_result(query)
            if empty_outcome.validation_status != "valid_empty":
                return empty_outcome
            continue

        feedback = _validate_intent_guardrails(query, intents)
        if feedback:
            return PhaseAOutcome(validation_status="retry_needed", feedback=f"[{agent_name}] {feedback}")

        feedback = _validate_value_ranges(result)
        if feedback:
            return PhaseAOutcome(validation_status="retry_needed", feedback=f"[{agent_name}] {feedback}")

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


def _failure_return(current_retry_count: int, feedback: str) -> dict:
    """Critic 실패 시 반환값 생성"""
    new_retry_count = current_retry_count + 1

    if new_retry_count >= MAX_RETRIES:
        # 3회 소진 → 에러 응답 설정 후 END
        LOGGER.error(f"❌ Critic retries exhausted ({MAX_RETRIES})")
        return {
            "critic_passed": False,
            "validation_status": "retry_needed",
            "retry_count": new_retry_count,
            "agent_results": [],
            "final_response": "분석 결과의 품질 검증에 실패했습니다. 질문을 더 구체적으로 바꿔주세요.",
            "visualization_type": None,
            "visualization_data": None,
        }

    # 재시도 가능 → 피드백 + agent_results 초기화
    return {
        "critic_passed": False,
        "validation_status": "retry_needed",
        "critic_feedback": feedback,
        "retry_count": new_retry_count,
        "agent_results": [],  # reducer가 초기화
    }
