"""LLM Structured Output 스키마 정의"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChartData(BaseModel):
    title: str = Field(description="차트 제목 (한국어)")
    data: list[dict] = Field(description="차트 데이터 배열")
    x_axis: Optional[str] = Field(None, description="x축 필드명 (축이 있는 차트에만 제공, pie_chart·radar_chart·ring_list·table은 null)")
    y_axis: Optional[str] = Field(None, description="y축 필드명 (축이 있는 차트에만 제공, pie_chart·radar_chart·ring_list·table은 null)")


class ChartVisualizationOutput(BaseModel):
    """차트 시각화용 출력 스키마 (text_summary 제외 - LLM이 반드시 차트 타입 선택)"""
    selected_visualization: Literal[
        "table", "bar_chart", "horizontal_bar", "stacked_bar",
        "pie_chart", "line_chart", "area_chart", "radar_chart",
        "scatter_plot", "ring_list", "lollipop_chart",
    ] = Field(description="차트 타입")
    visualization_data: ChartData
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