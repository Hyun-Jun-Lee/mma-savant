"""LLM Structured Output 스키마 정의"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class VisualizationDecision(BaseModel):
    """시각화 결정 스키마 (LLM은 메타데이터만, data는 코드에서 agent_results로 구성)"""
    selected_visualization: Literal[
        "bar_chart", "horizontal_bar", "stacked_bar",
        "pie_chart", "line_chart", "area_chart", "radar_chart",
        "scatter_plot", "ring_list", "lollipop_chart",
    ] = Field(description="차트 타입")
    title: str = Field(description="차트 제목 (한국어)")
    x_axis: Optional[str] = Field(
        None,
        description="x축/라벨/카테고리로 사용할 SQL 컬럼명 (table이면 null)",
    )
    y_axis: Optional[str] = Field(
        None,
        description="y축/값으로 사용할 SQL 컬럼명 (table이면 null)",
    )
    insights: list[str] = Field(description="차트 핵심 인사이트 (최대 3개)")


class TextSummaryOutput(BaseModel):
    """텍스트 응답용 출력 스키마 (insights 없음)"""
    title: str = Field(description="분석 제목 (한국어)")
    content: str = Field(description="사용자 질문에 대한 분석 답변")

class IntentClassification(BaseModel):
    """사용자 질문의 의도 분류 결과"""
    intent: Literal["general", "sql_needed", "followup"] = Field(
        description="general: DB 조회 불필요, "
                    "sql_needed: 통계/전적 등 DB 조회 필요, "
                    "followup: 이전 대화를 참조하는 후속 질문"
    )


class ConversationManagerOutput(BaseModel):
    """Conversation Manager 압축 결과 (요약 + 맥락 해소)"""
    summary: str = Field(
        description="이전 대화 요약 (1~3문장, 선수명·체급·핵심 데이터 포함)"
    )
    resolved_query: str = Field(
        description="맥락이 해소된 독립적 질문 (대명사·생략 대체)"
    )


class CompressionOutput(BaseModel):
    """Post-graph compression output"""
    summary: str = Field(description="대화 요약 (1~3문장, 선수명/체급/핵심 데이터 포함)")


class SupervisorRouting(BaseModel):
    """Supervisor 라우팅 결과 (structured output)"""
    route: Literal["general", "mma_analysis", "fighter_comparison", "complex"] = Field(
        description="general: 일반 대화/MMA 상식, "
                    "mma_analysis: 단일 선수 스탯/트렌드 분석, "
                    "fighter_comparison: 선수 간 비교, "
                    "complex: 복합 질문 (병렬 에이전트 실행)"
    )
    agents: list[str] = Field(
        default_factory=list,
        description="활성화할 에이전트 목록 (general일 때 빈 리스트, "
                    "mma_analysis/fighter_comparison일 때 해당 에이전트, "
                    "complex일 때 복수 에이전트)"
    )